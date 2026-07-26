from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.document_links import DocumentLinkCreate, DocumentLinkRead, DocumentTargetType
from app.services.document_links import (
    DocumentLinkConflictError,
    DocumentLinkError,
    DocumentLinkNotFoundError,
    DocumentLinkService,
    DocumentLinkValidationError,
)

router = APIRouter(prefix="/document-links", tags=["document-links"])
SessionDependency = Annotated[Session, Depends(get_session)]


def _http_error(exc: DocumentLinkError) -> HTTPException:
    if isinstance(exc, DocumentLinkNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, DocumentLinkConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, DocumentLinkValidationError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail="Document link operation failed")


@router.get("", response_model=list[DocumentLinkRead])
def list_document_links(
    session: SessionDependency,
    target_type: Annotated[DocumentTargetType, Query()],
    target_id: Annotated[UUID, Query()],
) -> list[DocumentLinkRead]:
    try:
        return DocumentLinkService(session).list(target_type, target_id)
    except DocumentLinkError as exc:
        raise _http_error(exc) from exc


@router.post("", response_model=DocumentLinkRead, status_code=status.HTTP_201_CREATED)
def create_document_link(
    payload: DocumentLinkCreate,
    session: SessionDependency,
) -> DocumentLinkRead:
    try:
        return DocumentLinkService(session).create(payload)
    except DocumentLinkError as exc:
        raise _http_error(exc) from exc


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_link(link_id: UUID, session: SessionDependency) -> Response:
    try:
        DocumentLinkService(session).delete(link_id)
    except DocumentLinkError as exc:
        raise _http_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
