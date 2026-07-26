from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.documents import (
    DocumentFolderCreate,
    DocumentListRead,
    DocumentMoveRequest,
    DocumentMutationRead,
)
from app.services.documents import (
    MAX_DOCUMENT_BYTES,
    DocumentConfigurationError,
    DocumentConflictError,
    DocumentError,
    DocumentNotFoundError,
    DocumentRemoteError,
    DocumentService,
    DocumentTooLargeError,
    DocumentValidationError,
)

router = APIRouter(prefix="/documents", tags=["documents"])
SessionDependency = Annotated[Session, Depends(get_session)]
RelativePath = Annotated[str, Query(max_length=1000)]


def _http_error(exc: DocumentError) -> HTTPException:
    if isinstance(exc, DocumentConfigurationError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, DocumentValidationError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, DocumentNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, DocumentConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, DocumentTooLargeError):
        return HTTPException(status_code=413, detail=str(exc))
    if isinstance(exc, DocumentRemoteError):
        return HTTPException(status_code=502, detail=str(exc))
    return HTTPException(status_code=500, detail="Document operation failed")


@router.get("", response_model=DocumentListRead)
def list_documents(
    session: SessionDependency,
    path: RelativePath = "",
) -> DocumentListRead:
    try:
        return DocumentService(session).list_entries(path)
    except DocumentError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/folders",
    response_model=DocumentMutationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_document_folder(
    payload: DocumentFolderCreate,
    session: SessionDependency,
) -> DocumentMutationRead:
    try:
        return DocumentService(session).create_folder(payload.parent_path, payload.name)
    except DocumentError as exc:
        raise _http_error(exc) from exc


@router.post("/upload", response_model=DocumentMutationRead)
async def upload_document(
    request: Request,
    session: SessionDependency,
    filename: Annotated[str, Query(min_length=1, max_length=255)],
    path: RelativePath = "",
    overwrite: bool = False,
) -> DocumentMutationRead:
    length = request.headers.get("content-length")
    if length:
        try:
            if int(length) > MAX_DOCUMENT_BYTES:
                raise HTTPException(status_code=413, detail="Document exceeds the 100 MB limit")
        except ValueError:
            pass
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > MAX_DOCUMENT_BYTES:
            raise HTTPException(status_code=413, detail="Document exceeds the 100 MB limit")
        chunks.append(chunk)
    content = b"".join(chunks)
    try:
        return DocumentService(session).upload(
            path,
            filename,
            content,
            content_type=request.headers.get("content-type", "application/octet-stream"),
            overwrite=overwrite,
        )
    except DocumentError as exc:
        raise _http_error(exc) from exc


@router.get("/download")
def download_document(
    session: SessionDependency,
    path: Annotated[str, Query(min_length=1, max_length=1000)],
) -> Response:
    try:
        document = DocumentService(session).download(path)
    except DocumentError as exc:
        raise _http_error(exc) from exc
    ascii_name = document.filename.encode("ascii", "ignore").decode() or "document"
    disposition = (
        f'attachment; filename="{ascii_name.replace(chr(34), "")}"; '
        f"filename*=UTF-8''{quote(document.filename, safe='')}"
    )
    headers = {
        "Cache-Control": "private, no-store",
        "Content-Disposition": disposition,
        "X-Content-Type-Options": "nosniff",
    }
    if document.etag:
        headers["ETag"] = document.etag
    return Response(content=document.content, media_type=document.content_type, headers=headers)


@router.post("/move", response_model=DocumentMutationRead)
def move_document(
    payload: DocumentMoveRequest,
    session: SessionDependency,
) -> DocumentMutationRead:
    try:
        return DocumentService(session).move(
            payload.source_path,
            payload.target_parent_path,
            payload.name,
        )
    except DocumentError as exc:
        raise _http_error(exc) from exc


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    session: SessionDependency,
    path: Annotated[str, Query(min_length=1, max_length=1000)],
) -> Response:
    try:
        DocumentService(session).delete(path)
    except DocumentError as exc:
        raise _http_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
