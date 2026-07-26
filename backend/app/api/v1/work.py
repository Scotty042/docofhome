from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.knowledge import KnowledgeTargetType
from app.schemas.work import (
    WorkCompletionWrite,
    WorkItemEventRead,
    WorkItemRead,
    WorkItemType,
    WorkItemWrite,
    WorkStatus,
    WorkSummaryRead,
)
from app.services.work import (
    WorkConflictError,
    WorkError,
    WorkNotFoundError,
    WorkService,
    WorkValidationError,
)

router = APIRouter(prefix="/work-items", tags=["work-items"])
SessionDependency = Annotated[Session, Depends(get_session)]


def _http_error(exc: WorkError) -> HTTPException:
    if isinstance(exc, WorkNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, WorkConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, WorkValidationError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(
        status_code=500,
        detail="Wartungen und Aufgaben konnten nicht verarbeitet werden",
    )


@router.get("", response_model=list[WorkItemRead])
def list_work_items(
    session: SessionDependency,
    status_filter: Annotated[WorkStatus | None, Query(alias="status")] = None,
    item_type: WorkItemType | None = None,
    target_type: KnowledgeTargetType | None = None,
    target_id: UUID | None = None,
) -> list[WorkItemRead]:
    try:
        return WorkService(session).list(
            status=status_filter,
            item_type=item_type,
            target_type=target_type,
            target_id=target_id,
        )
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.get("/summary", response_model=WorkSummaryRead)
def work_summary(session: SessionDependency) -> WorkSummaryRead:
    return WorkService(session).summary()


@router.get("/upcoming", response_model=list[WorkItemRead])
def upcoming_work_items(
    session: SessionDependency,
    days: Annotated[int, Query(ge=0, le=31)] = 3,
) -> list[WorkItemRead]:
    try:
        return WorkService(session).upcoming(days=days)
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.post("", response_model=WorkItemRead, status_code=status.HTTP_201_CREATED)
def create_work_item(payload: WorkItemWrite, session: SessionDependency) -> WorkItemRead:
    try:
        return WorkService(session).create(payload)
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.get("/{item_id}", response_model=WorkItemRead)
def get_work_item(item_id: UUID, session: SessionDependency) -> WorkItemRead:
    try:
        return WorkService(session).get(item_id)
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.put("/{item_id}", response_model=WorkItemRead)
def update_work_item(
    item_id: UUID,
    payload: WorkItemWrite,
    session: SessionDependency,
) -> WorkItemRead:
    try:
        return WorkService(session).update(item_id, payload)
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.post("/{item_id}/complete", response_model=WorkItemRead)
def complete_work_item(
    item_id: UUID,
    payload: WorkCompletionWrite,
    session: SessionDependency,
) -> WorkItemRead:
    try:
        return WorkService(session).complete(item_id, payload)
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.post("/{item_id}/cancel", response_model=WorkItemRead)
def cancel_work_item(item_id: UUID, session: SessionDependency) -> WorkItemRead:
    try:
        return WorkService(session).cancel(item_id)
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.post("/{item_id}/reopen", response_model=WorkItemRead)
def reopen_work_item(item_id: UUID, session: SessionDependency) -> WorkItemRead:
    try:
        return WorkService(session).reopen(item_id)
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.get("/{item_id}/events", response_model=list[WorkItemEventRead])
def work_item_events(item_id: UUID, session: SessionDependency) -> list[WorkItemEventRead]:
    try:
        return WorkService(session).events(item_id)
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_item(item_id: UUID, session: SessionDependency) -> Response:
    try:
        WorkService(session).delete(item_id)
    except WorkError as exc:
        raise _http_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
