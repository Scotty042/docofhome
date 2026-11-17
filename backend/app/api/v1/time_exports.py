from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.db.session import get_session
from app.services.time_exports import TimeExportService, TimeExportState, TimeExportWrite

router = APIRouter(prefix="/time-exports", tags=["time-exports"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("")
def read_exports(session: SessionDep) -> dict[str, Any]:
    try:
        service = TimeExportService(session)
        return {"configuration": service.read(), "files": service.files()}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.put("/configuration", response_model=TimeExportState)
def configure_exports(data: TimeExportWrite, session: SessionDep) -> TimeExportState:
    try:
        return TimeExportService(session).write(data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/run", response_model=TimeExportState)
def run_export(session: SessionDep) -> TimeExportState:
    try:
        return TimeExportService(session).run_once(force=True)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/{filename}/download", response_class=FileResponse)
def download_export(filename: str, session: SessionDep) -> FileResponse:
    try:
        path = TimeExportService(session).download(filename)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(404, str(exc)) from exc
    return FileResponse(path, media_type="text/csv; charset=utf-8", filename=path.name)
