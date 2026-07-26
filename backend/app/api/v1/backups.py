from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.backups import (
    BackupCreateRequest,
    BackupListRead,
    BackupRecord,
    BackupRestoreRead,
    BackupRestoreRequest,
    BackupScheduleRead,
    BackupScheduleWrite,
    BackupValidationRead,
    RemoteBackupListRead,
)
from app.services.backup_schedule import BackupScheduler, BackupScheduleStore
from app.services.backups import BackupError, BackupService

router = APIRouter(prefix="/backups", tags=["backups"])
SessionDependency = Annotated[Session, Depends(get_session)]
NextcloudFolder = Annotated[
    str,
    Query(min_length=1, max_length=500),
]


@router.get("", response_model=BackupListRead)
def list_backups(session: SessionDependency) -> BackupListRead:
    return BackupListRead(items=BackupService(session).list_backups())


@router.post("", response_model=BackupRecord, status_code=status.HTTP_201_CREATED)
def create_backup(
    payload: BackupCreateRequest,
    session: SessionDependency,
) -> BackupRecord:
    try:
        return BackupService(session).create_backup(
            upload_to_nextcloud=payload.upload_to_nextcloud,
            nextcloud_folder=payload.nextcloud_folder,
        )
    except BackupError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/import", response_model=BackupRecord, status_code=status.HTTP_201_CREATED)
async def import_backup(request: Request, session: SessionDependency) -> BackupRecord:
    if request.headers.get("content-type", "").split(";", 1)[0] != "application/zip":
        raise HTTPException(status_code=415, detail="Expected application/zip")
    try:
        return BackupService(session).import_backup(await request.body())
    except BackupError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/remote", response_model=RemoteBackupListRead)
def list_remote_backups(
    session: SessionDependency,
    folder: NextcloudFolder = "DocOfHome/Backups",
) -> RemoteBackupListRead:
    try:
        items = BackupService(session).list_nextcloud_backups(folder)
    except BackupError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return RemoteBackupListRead(items=items)


@router.post(
    "/remote/{filename}/import",
    response_model=BackupRecord,
    status_code=status.HTTP_201_CREATED,
)
def import_remote_backup(
    filename: str,
    session: SessionDependency,
    folder: NextcloudFolder = "DocOfHome/Backups",
) -> BackupRecord:
    try:
        return BackupService(session).import_from_nextcloud(filename, folder)
    except BackupError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/remote/{filename}", status_code=status.HTTP_204_NO_CONTENT)
def delete_remote_backup(
    filename: str,
    session: SessionDependency,
    folder: NextcloudFolder = "DocOfHome/Backups",
) -> Response:
    try:
        BackupService(session).delete_from_nextcloud(filename, folder)
    except BackupError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/schedule", response_model=BackupScheduleRead)
def read_schedule() -> BackupScheduleRead:
    return BackupScheduleStore().read()


@router.put("/schedule", response_model=BackupScheduleRead)
def update_schedule(payload: BackupScheduleWrite) -> BackupScheduleRead:
    return BackupScheduleStore().write(payload)


@router.post("/schedule/run", response_model=BackupScheduleRead)
def run_schedule_now() -> BackupScheduleRead:
    store = BackupScheduleStore()
    BackupScheduler(store).run_once(force=True)
    return store.read()


@router.get("/{filename}/download", response_class=FileResponse)
def download_backup(filename: str, session: SessionDependency) -> FileResponse:
    try:
        archive_path = BackupService(session).archive_path(filename)
    except BackupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(
        archive_path,
        media_type="application/zip",
        filename=archive_path.name,
    )


@router.delete("/{filename}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backup(filename: str, session: SessionDependency) -> Response:
    try:
        BackupService(session).delete_backup(filename)
    except BackupError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{filename}/validate", response_model=BackupValidationRead)
def validate_backup(filename: str, session: SessionDependency) -> BackupValidationRead:
    try:
        record = BackupService(session).validate_backup(filename)
    except BackupError as exc:
        return BackupValidationRead(valid=False, message=str(exc))
    return BackupValidationRead(valid=True, message="Backup is valid", record=record)


@router.post("/{filename}/restore", response_model=BackupRestoreRead)
def restore_backup(
    filename: str,
    payload: BackupRestoreRequest,
    session: SessionDependency,
) -> BackupRestoreRead:
    if payload.confirmation != "WIEDERHERSTELLEN":
        raise HTTPException(
            status_code=422,
            detail="Type WIEDERHERSTELLEN to confirm the restore",
        )
    try:
        BackupService(session).schedule_restore(filename)
    except BackupError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return BackupRestoreRead(
        scheduled=True,
        restart_required=True,
        message=(
            "Restore has been validated and scheduled. Restart the DocOfHome container to apply it."
        ),
    )
