from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.knowledge import (
    KnowledgeTargetType,
    NoteCreate,
    NoteRead,
    NoteUpdate,
    WikiPageCreate,
    WikiPageRead,
    WikiPageUpdate,
)
from app.services.knowledge import (
    KnowledgeConflictError,
    KnowledgeError,
    KnowledgeNotFoundError,
    KnowledgeValidationError,
    NoteService,
    WikiService,
)

router = APIRouter(tags=["knowledge"])
SessionDependency = Annotated[Session, Depends(get_session)]


def _http_error(exc: KnowledgeError) -> HTTPException:
    if isinstance(exc, KnowledgeNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, KnowledgeConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, KnowledgeValidationError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail="Wissensinhalte konnten nicht verarbeitet werden")


@router.get("/wiki/pages", response_model=list[WikiPageRead])
def list_wiki_pages(
    session: SessionDependency,
    search: Annotated[str | None, Query(max_length=100)] = None,
    include_archived: bool = False,
) -> list[WikiPageRead]:
    return WikiService(session).list(search=search, include_archived=include_archived)


@router.post("/wiki/pages", response_model=WikiPageRead, status_code=status.HTTP_201_CREATED)
def create_wiki_page(payload: WikiPageCreate, session: SessionDependency) -> WikiPageRead:
    try:
        return WikiService(session).create(payload)
    except KnowledgeError as exc:
        raise _http_error(exc) from exc


@router.get("/wiki/pages/{page_id}", response_model=WikiPageRead)
def get_wiki_page(
    page_id: UUID,
    session: SessionDependency,
    include_archived: bool = False,
) -> WikiPageRead:
    try:
        return WikiService(session).get(page_id, include_archived=include_archived)
    except KnowledgeError as exc:
        raise _http_error(exc) from exc


@router.put("/wiki/pages/{page_id}", response_model=WikiPageRead)
def update_wiki_page(
    page_id: UUID,
    payload: WikiPageUpdate,
    session: SessionDependency,
) -> WikiPageRead:
    try:
        return WikiService(session).update(page_id, payload)
    except KnowledgeError as exc:
        raise _http_error(exc) from exc


@router.delete("/wiki/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_wiki_page(page_id: UUID, session: SessionDependency) -> Response:
    try:
        WikiService(session).archive(page_id)
    except KnowledgeError as exc:
        raise _http_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/notes", response_model=list[NoteRead])
def list_notes(
    session: SessionDependency,
    target_type: Annotated[KnowledgeTargetType, Query()],
    target_id: Annotated[UUID, Query()],
) -> list[NoteRead]:
    try:
        return NoteService(session).list(target_type, target_id)
    except KnowledgeError as exc:
        raise _http_error(exc) from exc


@router.post("/notes", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
def create_note(payload: NoteCreate, session: SessionDependency) -> NoteRead:
    try:
        return NoteService(session).create(payload)
    except KnowledgeError as exc:
        raise _http_error(exc) from exc


@router.put("/notes/{note_id}", response_model=NoteRead)
def update_note(note_id: UUID, payload: NoteUpdate, session: SessionDependency) -> NoteRead:
    try:
        return NoteService(session).update(note_id, payload)
    except KnowledgeError as exc:
        raise _http_error(exc) from exc


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: UUID, session: SessionDependency) -> Response:
    try:
        NoteService(session).delete(note_id)
    except KnowledgeError as exc:
        raise _http_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
