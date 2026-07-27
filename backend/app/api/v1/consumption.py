from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.consumption import (
    ConsumptionComparisonRead,
    ConsumptionDefaultSeedRead,
    ConsumptionImportPreviewRead,
    ConsumptionImportResultRead,
    ConsumptionMeterLiveRead,
    ConsumptionMeterRead,
    ConsumptionMeterReplacementWrite,
    ConsumptionMeterType,
    ConsumptionMeterWrite,
    ConsumptionNoteRead,
    ConsumptionNoteWrite,
    ConsumptionReadingRead,
    ConsumptionReadingReminderRead,
    ConsumptionReadingWrite,
    ConsumptionSettingsRead,
    ConsumptionSettingsWrite,
    ConsumptionStatisticsRead,
    ConsumptionSummaryRead,
)
from app.services.consumption import (
    ConsumptionConflictError,
    ConsumptionError,
    ConsumptionImportError,
    ConsumptionNotFoundError,
    ConsumptionService,
    ConsumptionValidationError,
)

router = APIRouter(prefix="/consumption", tags=["consumption"])
SessionDependency = Annotated[Session, Depends(get_session)]


def _http_error(exc: ConsumptionError) -> HTTPException:
    if isinstance(exc, ConsumptionNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ConsumptionConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, ConsumptionValidationError | ConsumptionImportError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail="Verbrauchsdaten konnten nicht verarbeitet werden")


def _call(callback):
    try:
        return callback()
    except ConsumptionError as exc:
        raise _http_error(exc) from exc


@router.get("/summary", response_model=ConsumptionSummaryRead)
def summary(session: SessionDependency) -> ConsumptionSummaryRead:
    return _call(lambda: ConsumptionService(session).summary())


@router.get("/statistics", response_model=ConsumptionStatisticsRead)
def statistics(
    session: SessionDependency,
    months: Annotated[int, Query(ge=1, le=60)] = 12,
) -> ConsumptionStatisticsRead:
    return _call(lambda: ConsumptionService(session).statistics(months=months))


@router.get("/dashboard-comparisons", response_model=list[ConsumptionComparisonRead])
def dashboard_comparisons(session: SessionDependency) -> list[ConsumptionComparisonRead]:
    return _call(lambda: ConsumptionService(session).dashboard_comparisons())


@router.get("/reading-reminders", response_model=list[ConsumptionReadingReminderRead])
def reading_reminders(
    session: SessionDependency,
    days_ahead: Annotated[int, Query(ge=0, le=31)] = 3,
) -> list[ConsumptionReadingReminderRead]:
    return _call(lambda: ConsumptionService(session).reading_reminders(days_ahead=days_ahead))


@router.get("/settings", response_model=ConsumptionSettingsRead)
def get_settings(session: SessionDependency) -> ConsumptionSettingsRead:
    return _call(lambda: ConsumptionService(session).get_settings())


@router.put("/settings", response_model=ConsumptionSettingsRead)
def update_settings(
    payload: ConsumptionSettingsWrite,
    session: SessionDependency,
) -> ConsumptionSettingsRead:
    return _call(lambda: ConsumptionService(session).update_settings(payload))


@router.post("/default-meters", response_model=ConsumptionDefaultSeedRead)
def seed_default_meters(session: SessionDependency) -> ConsumptionDefaultSeedRead:
    return _call(lambda: ConsumptionService(session).seed_defaults())


@router.get("/meters", response_model=list[ConsumptionMeterRead])
def list_meters(
    session: SessionDependency,
    search: Annotated[str | None, Query(max_length=100)] = None,
    meter_type: ConsumptionMeterType | None = None,
    asset_id: UUID | None = None,
    location_id: UUID | None = None,
    include_archived: bool = False,
) -> list[ConsumptionMeterRead]:
    return _call(
        lambda: ConsumptionService(session).list_meters(
            search=search,
            meter_type=meter_type,
            asset_id=asset_id,
            location_id=location_id,
            include_archived=include_archived,
        )
    )


@router.post("/meters", response_model=ConsumptionMeterRead, status_code=status.HTTP_201_CREATED)
def create_meter(
    payload: ConsumptionMeterWrite, session: SessionDependency
) -> ConsumptionMeterRead:
    return _call(lambda: ConsumptionService(session).create_meter(payload))


@router.get("/meters/{meter_id}", response_model=ConsumptionMeterRead)
def get_meter(
    meter_id: UUID,
    session: SessionDependency,
    include_archived: bool = False,
) -> ConsumptionMeterRead:
    return _call(
        lambda: ConsumptionService(session).get_meter(
            meter_id,
            include_archived=include_archived,
        )
    )


@router.put("/meters/{meter_id}", response_model=ConsumptionMeterRead)
def update_meter(
    meter_id: UUID,
    payload: ConsumptionMeterWrite,
    session: SessionDependency,
) -> ConsumptionMeterRead:
    return _call(lambda: ConsumptionService(session).update_meter(meter_id, payload))


@router.post("/meters/{meter_id}/replace", response_model=ConsumptionMeterRead)
def replace_meter(
    meter_id: UUID,
    payload: ConsumptionMeterReplacementWrite,
    session: SessionDependency,
) -> ConsumptionMeterRead:
    return _call(lambda: ConsumptionService(session).replace_meter(meter_id, payload))


@router.get("/meters/{meter_id}/live", response_model=ConsumptionMeterLiveRead)
def meter_live_values(
    meter_id: UUID,
    session: SessionDependency,
    refresh: bool = False,
) -> ConsumptionMeterLiveRead:
    return _call(
        lambda: ConsumptionService(session).meter_live_values(
            meter_id,
            refresh=refresh,
        )
    )


@router.delete("/meters/{meter_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_meter(meter_id: UUID, session: SessionDependency) -> Response:
    _call(lambda: ConsumptionService(session).archive_meter(meter_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/meters/{meter_id}/capture-home-assistant", response_model=ConsumptionReadingRead)
def capture_home_assistant(meter_id: UUID, session: SessionDependency) -> ConsumptionReadingRead:
    return _call(lambda: ConsumptionService(session).capture_home_assistant(meter_id))


@router.get("/readings", response_model=list[ConsumptionReadingRead])
def list_readings(
    session: SessionDependency,
    meter_id: UUID | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
) -> list[ConsumptionReadingRead]:
    return _call(
        lambda: ConsumptionService(session).list_readings(
            meter_id=meter_id,
            start=start,
            end=end,
            limit=limit,
        )
    )


@router.post(
    "/readings", response_model=ConsumptionReadingRead, status_code=status.HTTP_201_CREATED
)
def create_reading(
    payload: ConsumptionReadingWrite,
    session: SessionDependency,
) -> ConsumptionReadingRead:
    return _call(lambda: ConsumptionService(session).create_reading(payload))


@router.put("/readings/{reading_id}", response_model=ConsumptionReadingRead)
def update_reading(
    reading_id: UUID,
    payload: ConsumptionReadingWrite,
    session: SessionDependency,
) -> ConsumptionReadingRead:
    return _call(lambda: ConsumptionService(session).update_reading(reading_id, payload))


@router.delete("/readings/{reading_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_reading(reading_id: UUID, session: SessionDependency) -> Response:
    _call(lambda: ConsumptionService(session).archive_reading(reading_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/notes", response_model=list[ConsumptionNoteRead])
def list_notes(session: SessionDependency) -> list[ConsumptionNoteRead]:
    return _call(lambda: ConsumptionService(session).list_notes())


@router.post("/notes", response_model=ConsumptionNoteRead, status_code=status.HTTP_201_CREATED)
def create_note(payload: ConsumptionNoteWrite, session: SessionDependency) -> ConsumptionNoteRead:
    return _call(lambda: ConsumptionService(session).create_note(payload))


@router.put("/notes/{note_id}", response_model=ConsumptionNoteRead)
def update_note(
    note_id: UUID,
    payload: ConsumptionNoteWrite,
    session: SessionDependency,
) -> ConsumptionNoteRead:
    return _call(lambda: ConsumptionService(session).update_note(note_id, payload))


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_note(note_id: UUID, session: SessionDependency) -> Response:
    _call(lambda: ConsumptionService(session).archive_note(note_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _read_upload(file: UploadFile) -> tuple[str, bytes]:
    name = file.filename or "import"
    content = await file.read(50 * 1024 * 1024 + 1)
    return name, content


@router.post("/import/preview", response_model=ConsumptionImportPreviewRead)
async def preview_import(
    session: SessionDependency,
    file: Annotated[UploadFile, File()],
) -> ConsumptionImportPreviewRead:
    name, content = await _read_upload(file)
    return _call(
        lambda: ConsumptionService(session).preview_import(file_name=name, content=content)
    )


@router.post("/import", response_model=ConsumptionImportResultRead)
async def import_file(
    session: SessionDependency,
    file: Annotated[UploadFile, File()],
    create_missing_meters: bool = True,
    overwrite: bool = False,
) -> ConsumptionImportResultRead:
    name, content = await _read_upload(file)
    return _call(
        lambda: ConsumptionService(session).import_file(
            file_name=name,
            content=content,
            create_missing_meters=create_missing_meters,
            overwrite=overwrite,
        )
    )
