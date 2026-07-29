from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session

from app.db.session import get_session
from app.distribution_layout import ElectricalLayoutService
from app.schemas.electrical import ProtectiveDeviceWrite
from app.schemas.electrical_layout import (
    DistributionAreaRead,
    DistributionAreaWrite,
    DistributionSectionRead,
    DistributionSectionWrite,
    ElectricalAssetPlacementRead,
    ElectricalAssetPlacementWrite,
    ElectricalCabinetComponentRead,
    ElectricalCabinetComponentWrite,
    ElectricalMeterPlacementRead,
    ElectricalMeterPlacementWrite,
    PhaseRailSynchronizationWrite,
)
from app.services.electrical import (
    ElectricalConflictError,
    ElectricalNotFoundError,
    ElectricalValidationError,
)

router = APIRouter(
    prefix="/electrical/distributions",
    tags=["electrical-layout"],
)
SessionDependency = Annotated[Session, Depends(get_session)]


class ProtectiveDevicePlacementWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    area_id: UUID | None = None
    row_number: int | None = Field(default=None, ge=1, le=100)
    start_position: int | None = Field(default=None, ge=1, le=1000)
    module_width: int | None = Field(default=None, ge=1, le=100)
    assigned_rcd_id: UUID | None = None
    neutral_rail_id: UUID | None = None


def _translate_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ElectricalNotFoundError):
        return HTTPException(
            status_code=404,
            detail="Electrical layout resource not found",
        )
    if isinstance(exc, ElectricalValidationError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, ElectricalConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(
        status_code=500,
        detail="Unexpected electrical layout error",
    )


@router.get(
    "/placements/assets",
    response_model=list[ElectricalAssetPlacementRead],
)
def list_all_asset_placements(
    session: SessionDependency,
) -> list[ElectricalAssetPlacementRead]:
    try:
        return ElectricalLayoutService(session).list_asset_placements()
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.get(
    "/placements/meters",
    response_model=list[ElectricalMeterPlacementRead],
)
def list_all_meter_placements(
    session: SessionDependency,
) -> list[ElectricalMeterPlacementRead]:
    try:
        return ElectricalLayoutService(session).list_meter_placements()
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.get(
    "/{distribution_id}/layout",
    response_model=list[DistributionSectionRead],
)
def read_layout(
    distribution_id: UUID,
    session: SessionDependency,
) -> list[DistributionSectionRead]:
    try:
        return ElectricalLayoutService(session).read(distribution_id)
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.post(
    "/{distribution_id}/sections",
    response_model=DistributionSectionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_section(
    distribution_id: UUID,
    payload: DistributionSectionWrite,
    session: SessionDependency,
) -> DistributionSectionRead:
    try:
        return ElectricalLayoutService(session).create_section(
            distribution_id,
            payload,
        )
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.put(
    "/{distribution_id}/sections/{section_id}",
    response_model=DistributionSectionRead,
)
def update_section(
    distribution_id: UUID,
    section_id: UUID,
    payload: DistributionSectionWrite,
    session: SessionDependency,
) -> DistributionSectionRead:
    try:
        return ElectricalLayoutService(session).update_section(
            distribution_id,
            section_id,
            payload,
        )
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.delete(
    "/{distribution_id}/sections/{section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def archive_section(
    distribution_id: UUID,
    section_id: UUID,
    session: SessionDependency,
) -> Response:
    try:
        ElectricalLayoutService(session).archive_section(
            distribution_id,
            section_id,
        )
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{distribution_id}/sections/{section_id}/areas",
    response_model=DistributionAreaRead,
    status_code=status.HTTP_201_CREATED,
)
def create_area(
    distribution_id: UUID,
    section_id: UUID,
    payload: DistributionAreaWrite,
    session: SessionDependency,
) -> DistributionAreaRead:
    try:
        return ElectricalLayoutService(session).create_area(
            distribution_id,
            section_id,
            payload,
        )
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.put(
    "/{distribution_id}/areas/{area_id}",
    response_model=DistributionAreaRead,
)
def update_area(
    distribution_id: UUID,
    area_id: UUID,
    payload: DistributionAreaWrite,
    session: SessionDependency,
) -> DistributionAreaRead:
    try:
        return ElectricalLayoutService(session).update_area(
            distribution_id,
            area_id,
            payload,
        )
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.delete(
    "/{distribution_id}/areas/{area_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def archive_area(
    distribution_id: UUID,
    area_id: UUID,
    session: SessionDependency,
) -> Response:
    try:
        ElectricalLayoutService(session).archive_area(
            distribution_id,
            area_id,
        )
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{distribution_id}/asset-placements",
    response_model=list[ElectricalAssetPlacementRead],
)
def list_asset_placements(
    distribution_id: UUID,
    session: SessionDependency,
) -> list[ElectricalAssetPlacementRead]:
    try:
        return ElectricalLayoutService(session).list_asset_placements(distribution_id)
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.put(
    "/{distribution_id}/assets/{asset_id}/placement",
    response_model=ElectricalAssetPlacementRead,
)
def place_asset(
    distribution_id: UUID,
    asset_id: UUID,
    payload: ElectricalAssetPlacementWrite,
    session: SessionDependency,
) -> ElectricalAssetPlacementRead:
    try:
        return ElectricalLayoutService(session).place_asset(
            distribution_id, asset_id, payload
        )
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.delete(
    "/{distribution_id}/assets/{asset_id}/placement",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unplace_asset(
    distribution_id: UUID,
    asset_id: UUID,
    session: SessionDependency,
) -> Response:
    try:
        ElectricalLayoutService(session).unplace_asset(distribution_id, asset_id)
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{distribution_id}/cabinet-components",
    response_model=list[ElectricalCabinetComponentRead],
)
def list_cabinet_components(
    distribution_id: UUID,
    session: SessionDependency,
) -> list[ElectricalCabinetComponentRead]:
    try:
        return ElectricalLayoutService(session).list_cabinet_components(distribution_id)
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.post(
    "/{distribution_id}/cabinet-components",
    response_model=ElectricalCabinetComponentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_cabinet_component(
    distribution_id: UUID,
    payload: ElectricalCabinetComponentWrite,
    session: SessionDependency,
) -> ElectricalCabinetComponentRead:
    try:
        return ElectricalLayoutService(session).create_cabinet_component(
            distribution_id, payload
        )
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.put(
    "/{distribution_id}/cabinet-components/{component_id}",
    response_model=ElectricalCabinetComponentRead,
)
def update_cabinet_component(
    distribution_id: UUID,
    component_id: UUID,
    payload: ElectricalCabinetComponentWrite,
    session: SessionDependency,
) -> ElectricalCabinetComponentRead:
    try:
        return ElectricalLayoutService(session).update_cabinet_component(
            distribution_id, component_id, payload
        )
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.post(
    "/{distribution_id}/cabinet-components/{component_id}/synchronize",
    response_model=ElectricalCabinetComponentRead,
)
def synchronize_phase_rail_contacts(
    distribution_id: UUID,
    component_id: UUID,
    payload: PhaseRailSynchronizationWrite,
    session: SessionDependency,
) -> ElectricalCabinetComponentRead:
    try:
        return ElectricalLayoutService(session).synchronize_phase_rail_contacts(
            distribution_id,
            component_id,
            payload.protective_device_ids,
            payload.asset_ids,
        )
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.delete(
    "/{distribution_id}/cabinet-components/{component_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def archive_cabinet_component(
    distribution_id: UUID,
    component_id: UUID,
    session: SessionDependency,
) -> Response:
    try:
        ElectricalLayoutService(session).archive_cabinet_component(
            distribution_id, component_id
        )
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{distribution_id}/meter-placements",
    response_model=list[ElectricalMeterPlacementRead],
)
def list_meter_placements(
    distribution_id: UUID,
    session: SessionDependency,
) -> list[ElectricalMeterPlacementRead]:
    try:
        return ElectricalLayoutService(session).list_meter_placements(distribution_id)
    except (ElectricalNotFoundError, ElectricalValidationError, ElectricalConflictError) as exc:
        raise _translate_error(exc) from exc


@router.put(
    "/{distribution_id}/meters/{meter_id}/placement",
    response_model=ElectricalMeterPlacementRead,
)
def place_meter(
    distribution_id: UUID,
    meter_id: UUID,
    payload: ElectricalMeterPlacementWrite,
    session: SessionDependency,
) -> ElectricalMeterPlacementRead:
    try:
        return ElectricalLayoutService(session).place_meter(distribution_id, meter_id, payload)
    except (ElectricalNotFoundError, ElectricalValidationError, ElectricalConflictError) as exc:
        raise _translate_error(exc) from exc


@router.put(
    "/{distribution_id}/meter-assets/{asset_id}/placement",
    response_model=ElectricalMeterPlacementRead,
)
def place_asset_meter(
    distribution_id: UUID,
    asset_id: UUID,
    payload: ElectricalMeterPlacementWrite,
    session: SessionDependency,
) -> ElectricalMeterPlacementRead:
    try:
        return ElectricalLayoutService(session).place_asset_meter(
            distribution_id,
            asset_id,
            payload,
        )
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.delete(
    "/{distribution_id}/meter-assets/{asset_id}/placement",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unplace_asset_meter(
    distribution_id: UUID,
    asset_id: UUID,
    session: SessionDependency,
) -> Response:
    try:
        ElectricalLayoutService(session).unplace_asset_meter(distribution_id, asset_id)
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{distribution_id}/meters/{meter_id}/placement",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unplace_meter(
    distribution_id: UUID,
    meter_id: UUID,
    session: SessionDependency,
) -> Response:
    try:
        ElectricalLayoutService(session).unplace_meter(distribution_id, meter_id)
    except (ElectricalNotFoundError, ElectricalValidationError, ElectricalConflictError) as exc:
        raise _translate_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/{distribution_id}/protective-devices/{device_id}/placement",
    status_code=status.HTTP_204_NO_CONTENT,
)
def place_device(
    distribution_id: UUID,
    device_id: UUID,
    payload: ProtectiveDevicePlacementWrite,
    session: SessionDependency,
) -> Response:
    try:
        ElectricalLayoutService(session).place_device(
            distribution_id,
            device_id,
            area_id=payload.area_id,
            row_number=payload.row_number,
            start_position=payload.start_position,
            module_width=payload.module_width,
            assigned_rcd_id=payload.assigned_rcd_id,
            neutral_rail_id=payload.neutral_rail_id,
        )
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/{distribution_id}/protective-devices/{device_id}/technical",
    status_code=status.HTTP_204_NO_CONTENT,
)
def update_device_technical(
    distribution_id: UUID,
    device_id: UUID,
    payload: ProtectiveDeviceWrite,
    session: SessionDependency,
) -> Response:
    try:
        ElectricalLayoutService(session).update_device_technical(
            distribution_id,
            device_id,
            payload,
        )
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
