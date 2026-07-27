from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.smart_meter import (
    SmartMeterMeasurementPointRead,
    SmartMeterMeasurementPointWrite,
)
from app.services.electrical import (
    ElectricalConflictError,
    ElectricalNotFoundError,
    ElectricalValidationError,
)
from app.services.smart_meter import SmartMeterMeasurementService

router = APIRouter(prefix="/electrical/smart-meters", tags=["smart-meter-measurements"])
SessionDependency = Annotated[Session, Depends(get_session)]


def _translate(exc: Exception) -> HTTPException:
    if isinstance(exc, ElectricalNotFoundError):
        return HTTPException(status_code=404, detail="Smart Meter oder Messpunkt nicht gefunden")
    if isinstance(exc, ElectricalValidationError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, ElectricalConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=500, detail="Unerwarteter Smart-Meter-Fehler")


@router.get(
    "/{asset_id}/measurement-points",
    response_model=list[SmartMeterMeasurementPointRead],
)
def list_measurement_points(
    asset_id: UUID,
    session: SessionDependency,
) -> list[SmartMeterMeasurementPointRead]:
    try:
        return SmartMeterMeasurementService(session).list_for_asset(asset_id)
    except (ElectricalNotFoundError, ElectricalValidationError, ElectricalConflictError) as exc:
        raise _translate(exc) from exc


@router.post(
    "/{asset_id}/measurement-points",
    response_model=SmartMeterMeasurementPointRead,
    status_code=status.HTTP_201_CREATED,
)
def create_measurement_point(
    asset_id: UUID,
    payload: SmartMeterMeasurementPointWrite,
    session: SessionDependency,
) -> SmartMeterMeasurementPointRead:
    try:
        return SmartMeterMeasurementService(session).create(asset_id, payload)
    except (ElectricalNotFoundError, ElectricalValidationError, ElectricalConflictError) as exc:
        raise _translate(exc) from exc


@router.put(
    "/{asset_id}/measurement-points/{point_id}",
    response_model=SmartMeterMeasurementPointRead,
)
def update_measurement_point(
    asset_id: UUID,
    point_id: UUID,
    payload: SmartMeterMeasurementPointWrite,
    session: SessionDependency,
) -> SmartMeterMeasurementPointRead:
    try:
        return SmartMeterMeasurementService(session).update(asset_id, point_id, payload)
    except (ElectricalNotFoundError, ElectricalValidationError, ElectricalConflictError) as exc:
        raise _translate(exc) from exc


@router.delete(
    "/{asset_id}/measurement-points/{point_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_measurement_point(
    asset_id: UUID,
    point_id: UUID,
    session: SessionDependency,
) -> Response:
    try:
        SmartMeterMeasurementService(session).delete(asset_id, point_id)
    except (ElectricalNotFoundError, ElectricalValidationError, ElectricalConflictError) as exc:
        raise _translate(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
