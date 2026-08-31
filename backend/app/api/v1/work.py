from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.knowledge import KnowledgeTargetType
from app.schemas.work import (
    WorkCompletionWrite,
    WorkEventAttachmentRead,
    WorkHistoryEntryWrite,
    WorkHistoryRead,
    WorkItemEventRead,
    WorkItemRead,
    WorkItemType,
    WorkItemWrite,
    WorkStatus,
    WorkSubjectRead,
    WorkSubjectTimelineRead,
    WorkSubjectWrite,
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
    subject_id: UUID | None = None,
) -> list[WorkItemRead]:
    try:
        return WorkService(session).list(
            status=status_filter,
            item_type=item_type,
            target_type=target_type,
            target_id=target_id,
            subject_id=subject_id,
        )
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.get("/subjects", response_model=list[WorkSubjectRead])
def list_work_subjects(session: SessionDependency) -> list[WorkSubjectRead]:
    try:
        return WorkService(session).list_subjects()
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.get("/subjects/{subject_id}/timeline", response_model=WorkSubjectTimelineRead)
def work_subject_timeline(subject_id: UUID, session: SessionDependency) -> WorkSubjectTimelineRead:
    try:
        return WorkService(session).subject_timeline(subject_id)
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.post("/subjects", response_model=WorkSubjectRead, status_code=status.HTTP_201_CREATED)
def create_work_subject(payload: WorkSubjectWrite, session: SessionDependency) -> WorkSubjectRead:
    try:
        return WorkService(session).create_subject(payload)
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.put("/subjects/{subject_id}", response_model=WorkSubjectRead)
def update_work_subject(
    subject_id: UUID, payload: WorkSubjectWrite, session: SessionDependency
) -> WorkSubjectRead:
    try:
        return WorkService(session).update_subject(subject_id, payload)
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_subject(subject_id: UUID, session: SessionDependency) -> Response:
    try:
        WorkService(session).delete_subject(subject_id)
    except WorkError as exc:
        raise _http_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


@router.get("/{item_id}/history", response_model=WorkHistoryRead)
def work_item_history(item_id: UUID, session: SessionDependency) -> WorkHistoryRead:
    try:
        return WorkService(session).history(item_id)
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/{item_id}/history",
    response_model=WorkItemEventRead,
    status_code=status.HTTP_201_CREATED,
)
def add_work_item_history(
    item_id: UUID, payload: WorkHistoryEntryWrite, session: SessionDependency
) -> WorkItemEventRead:
    try:
        return WorkService(session).add_history(item_id, payload)
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.put("/{item_id}/history/{event_id}", response_model=WorkItemEventRead)
def update_work_item_history(
    item_id: UUID, event_id: UUID, payload: WorkHistoryEntryWrite, session: SessionDependency
) -> WorkItemEventRead:
    try:
        return WorkService(session).update_history(item_id, event_id, payload)
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.delete("/{item_id}/history/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_item_history(item_id: UUID, event_id: UUID, session: SessionDependency) -> Response:
    try:
        WorkService(session).delete_history(item_id, event_id)
    except WorkError as exc:
        raise _http_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{item_id}/history/{event_id}/attachments",
    response_model=WorkEventAttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_work_history_attachment(
    item_id: UUID,
    event_id: UUID,
    session: SessionDependency,
    file: UploadFile = File(...),
) -> WorkEventAttachmentRead:
    content = await file.read(20 * 1024 * 1024 + 1)
    try:
        return WorkService(session).add_attachment(
            item_id,
            event_id,
            file.filename or "anhang",
            file.content_type or "application/octet-stream",
            content,
        )
    except WorkError as exc:
        raise _http_error(exc) from exc


@router.get("/{item_id}/history/{event_id}/attachments/{attachment_id}")
def download_work_history_attachment(
    item_id: UUID, event_id: UUID, attachment_id: UUID, session: SessionDependency
) -> Response:
    try:
        attachment, content = WorkService(session).attachment(item_id, event_id, attachment_id)
    except WorkError as exc:
        raise _http_error(exc) from exc
    safe_name = attachment.file_name.replace('"', '')
    return Response(
        content=content,
        media_type=attachment.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.delete(
    "/{item_id}/history/{event_id}/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_work_history_attachment(
    item_id: UUID, event_id: UUID, attachment_id: UUID, session: SessionDependency
) -> Response:
    try:
        WorkService(session).delete_attachment(item_id, event_id, attachment_id)
    except WorkError as exc:
        raise _http_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
