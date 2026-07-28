from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.asset_engine import Page, SortOrder
from app.schemas.electrical_circuit import (
    ElectricalCircuitAssetRead,
    ElectricalCircuitAssetWrite,
    ElectricalCircuitRead,
    ElectricalCircuitWrite,
    ElectricalProtectiveDeviceOptionRead,
)
from app.services.electrical import (
    ElectricalConflictError,
    ElectricalNotFoundError,
    ElectricalSortError,
    ElectricalValidationError,
)
from app.services.electrical_circuit import ElectricalCircuitService

router = APIRouter(prefix="/electrical/circuits", tags=["electrical"])
SessionDependency = Annotated[Session, Depends(get_session)]
PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


def _translate_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ElectricalNotFoundError):
        return HTTPException(status_code=404, detail="Electrical circuit not found")
    if isinstance(exc, ElectricalValidationError | ElectricalSortError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, ElectricalConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=500, detail="Unexpected electrical circuit error")


@router.get("", response_model=Page[ElectricalCircuitRead])
def list_circuits(
    session: SessionDependency,
    page: PageNumber = 1,
    page_size: PageSize = 25,
    search: str | None = None,
    sort_by: str = "circuit_number",
    sort_order: SortOrder = SortOrder.ASC,
    include_deleted: bool = False,
    distribution_id: UUID | None = None,
    protective_device_id: UUID | None = None,
    protective_device_asset_id: UUID | None = None,
) -> Page[ElectricalCircuitRead]:
    try:
        return ElectricalCircuitService(session).list_read(
            page=page,
            page_size=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            include_deleted=include_deleted,
            distribution_id=distribution_id,
            protective_device_id=protective_device_id,
            protective_device_asset_id=protective_device_asset_id,
        )
    except ElectricalSortError as exc:
        raise _translate_error(exc) from exc


@router.get(
    "/protective-device-options",
    response_model=list[ElectricalProtectiveDeviceOptionRead],
)
def protective_device_options(
    distribution_id: UUID,
    session: SessionDependency,
    circuit_id: UUID | None = None,
) -> list[ElectricalProtectiveDeviceOptionRead]:
    try:
        return ElectricalCircuitService(session).protective_device_options(
            distribution_id,
            circuit_id=circuit_id,
        )
    except (ElectricalNotFoundError, ElectricalValidationError) as exc:
        raise _translate_error(exc) from exc


@router.post(
    "",
    response_model=ElectricalCircuitRead,
    status_code=status.HTTP_201_CREATED,
)
def create_circuit(
    payload: ElectricalCircuitWrite,
    session: SessionDependency,
) -> ElectricalCircuitRead:
    try:
        return ElectricalCircuitService(session).create(payload)
    except (ElectricalValidationError, ElectricalConflictError) as exc:
        raise _translate_error(exc) from exc


@router.get(
    "/{circuit_id}/assets",
    response_model=list[ElectricalCircuitAssetRead],
)
def list_circuit_assets(
    circuit_id: UUID,
    session: SessionDependency,
    include_deleted: bool = False,
) -> list[ElectricalCircuitAssetRead]:
    try:
        return ElectricalCircuitService(session).list_assets(
            circuit_id,
            include_deleted=include_deleted,
        )
    except ElectricalNotFoundError as exc:
        raise _translate_error(exc) from exc


@router.post(
    "/{circuit_id}/assets",
    response_model=ElectricalCircuitAssetRead,
    status_code=status.HTTP_201_CREATED,
)
def assign_circuit_asset(
    circuit_id: UUID,
    payload: ElectricalCircuitAssetWrite,
    session: SessionDependency,
) -> ElectricalCircuitAssetRead:
    try:
        return ElectricalCircuitService(session).assign_asset(circuit_id, payload)
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.delete(
    "/{circuit_id}/assets/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_circuit_asset(
    circuit_id: UUID,
    asset_id: UUID,
    session: SessionDependency,
) -> Response:
    try:
        ElectricalCircuitService(session).remove_asset(circuit_id, asset_id)
    except ElectricalNotFoundError as exc:
        raise _translate_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{circuit_id}", response_model=ElectricalCircuitRead)
def get_circuit(
    circuit_id: UUID,
    session: SessionDependency,
    include_deleted: bool = False,
) -> ElectricalCircuitRead:
    try:
        return ElectricalCircuitService(session).get_read(
            circuit_id,
            include_deleted=include_deleted,
        )
    except ElectricalNotFoundError as exc:
        raise _translate_error(exc) from exc


@router.put("/{circuit_id}", response_model=ElectricalCircuitRead)
def update_circuit(
    circuit_id: UUID,
    payload: ElectricalCircuitWrite,
    session: SessionDependency,
) -> ElectricalCircuitRead:
    try:
        return ElectricalCircuitService(session).update(circuit_id, payload)
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.delete("/{circuit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_circuit(circuit_id: UUID, session: SessionDependency) -> Response:
    try:
        ElectricalCircuitService(session).delete(circuit_id)
    except (ElectricalNotFoundError, ElectricalConflictError) as exc:
        raise _translate_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
