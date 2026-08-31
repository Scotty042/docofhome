from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.paperless import PaperlessDocumentLinkWrite, PaperlessDocumentRead
from app.schemas.work import WorkPaperlessLinkRead
from app.services.paperless import (
    PaperlessNotConfiguredError,
    PaperlessService,
    PaperlessServiceError,
)

router = APIRouter(prefix="/paperless", tags=["paperless"])
SessionDependency = Annotated[Session, Depends(get_session)]


def _error(exc: PaperlessServiceError) -> HTTPException:
    return HTTPException(
        status_code=409 if isinstance(exc, PaperlessNotConfiguredError) else 502,
        detail=str(exc),
    )


@router.get("/documents", response_model=list[PaperlessDocumentRead])
def search_documents(
    session: SessionDependency,
    q: Annotated[str, Query(max_length=500)] = "",
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> list[PaperlessDocumentRead]:
    try:
        return PaperlessService(session).search(q, page_size)
    except PaperlessServiceError as exc:
        raise _error(exc) from exc


@router.post(
    "/events/{event_id}/documents",
    response_model=WorkPaperlessLinkRead,
    status_code=status.HTTP_201_CREATED,
)
def link_document(
    event_id: UUID,
    payload: PaperlessDocumentLinkWrite,
    session: SessionDependency,
) -> WorkPaperlessLinkRead:
    try:
        return PaperlessService(session).link(event_id, payload.document_id)
    except PaperlessServiceError as exc:
        raise _error(exc) from exc


@router.delete(
    "/events/{event_id}/documents/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unlink_document(event_id: UUID, link_id: UUID, session: SessionDependency) -> Response:
    try:
        PaperlessService(session).unlink(event_id, link_id)
    except PaperlessServiceError as exc:
        raise _error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
