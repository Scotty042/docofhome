from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.asset_engine import Page, SortOrder
from app.schemas.electrical import (
    AvailableAssetRead,
    DistributionDetailRead,
    DistributionMoveWrite,
    DistributionRead,
    DistributionTreeNode,
    DistributionType,
    DistributionWrite,
    ElectricalRole,
    ProtectiveDeviceRead,
    ProtectiveDeviceType,
    ProtectiveDeviceWrite,
)
from app.services.electrical import (
    AvailableElectricalAssetService,
    ElectricalConflictError,
    ElectricalDistributionService,
    ElectricalNotFoundError,
    ElectricalProtectiveDeviceService,
    ElectricalSortError,
    ElectricalValidationError,
)

router = APIRouter(prefix="/electrical", tags=["electrical"])
SessionDependency = Annotated[Session, Depends(get_session)]
PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


def _translate_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ElectricalNotFoundError):
        return HTTPException(status_code=404, detail="Electrical resource not found")
    if isinstance(exc, ElectricalValidationError | ElectricalSortError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, ElectricalConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=500, detail="Unexpected electrical module error")


@router.get("/available-assets", response_model=Page[AvailableAssetRead])
def list_available_assets(
    session: SessionDependency,
    role: ElectricalRole,
    page: PageNumber = 1,
    page_size: PageSize = 25,
    search: str | None = None,
    sort_by: str = "name",
    sort_order: SortOrder = SortOrder.ASC,
    current_component_id: UUID | None = None,
) -> Page[AvailableAssetRead]:
    try:
        return AvailableElectricalAssetService(session).list_read(
            role=role,
            page=page,
            page_size=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            current_component_id=current_component_id,
        )
    except (ElectricalValidationError, ElectricalSortError) as exc:
        raise _translate_error(exc) from exc


@router.get("/distributions", response_model=Page[DistributionRead])
def list_distributions(
    session: SessionDependency,
    page: PageNumber = 1,
    page_size: PageSize = 25,
    search: str | None = None,
    sort_by: str = "designation",
    sort_order: SortOrder = SortOrder.ASC,
    include_deleted: bool = False,
    distribution_type: DistributionType | None = None,
    parent_distribution_id: UUID | None = None,
    location_id: UUID | None = None,
) -> Page[DistributionRead]:
    try:
        return ElectricalDistributionService(session).list_read(
            page=page,
            page_size=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            include_deleted=include_deleted,
            distribution_type=distribution_type,
            parent_distribution_id=parent_distribution_id,
            location_id=location_id,
        )
    except ElectricalSortError as exc:
        raise _translate_error(exc) from exc


@router.get("/distributions/tree", response_model=list[DistributionTreeNode])
def distribution_tree(
    session: SessionDependency,
    include_deleted: bool = False,
) -> list[DistributionTreeNode]:
    try:
        return ElectricalDistributionService(session).tree_read(include_deleted=include_deleted)
    except ElectricalValidationError as exc:
        raise _translate_error(exc) from exc


@router.post(
    "/distributions",
    response_model=DistributionDetailRead,
    status_code=status.HTTP_201_CREATED,
)
def create_distribution(
    payload: DistributionWrite,
    session: SessionDependency,
) -> DistributionDetailRead:
    try:
        return ElectricalDistributionService(session).create(payload)
    except (ElectricalValidationError, ElectricalConflictError) as exc:
        raise _translate_error(exc) from exc


@router.get("/distributions/{distribution_id}", response_model=DistributionDetailRead)
def get_distribution(
    distribution_id: UUID,
    session: SessionDependency,
    include_deleted: bool = False,
) -> DistributionDetailRead:
    try:
        return ElectricalDistributionService(session).get_read(
            distribution_id,
            include_deleted=include_deleted,
        )
    except (ElectricalNotFoundError, ElectricalValidationError) as exc:
        raise _translate_error(exc) from exc


@router.put("/distributions/{distribution_id}", response_model=DistributionDetailRead)
def update_distribution(
    distribution_id: UUID,
    payload: DistributionWrite,
    session: SessionDependency,
) -> DistributionDetailRead:
    try:
        return ElectricalDistributionService(session).update(distribution_id, payload)
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.post(
    "/distributions/{distribution_id}/move",
    response_model=DistributionDetailRead,
)
def move_distribution(
    distribution_id: UUID,
    payload: DistributionMoveWrite,
    session: SessionDependency,
) -> DistributionDetailRead:
    try:
        return ElectricalDistributionService(session).move(distribution_id, payload)
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.delete(
    "/distributions/{distribution_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_distribution(distribution_id: UUID, session: SessionDependency) -> Response:
    try:
        ElectricalDistributionService(session).delete(distribution_id)
    except (ElectricalNotFoundError, ElectricalConflictError) as exc:
        raise _translate_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/protective-devices", response_model=Page[ProtectiveDeviceRead])
def list_protective_devices(
    session: SessionDependency,
    page: PageNumber = 1,
    page_size: PageSize = 25,
    search: str | None = None,
    sort_by: str = "row_number",
    sort_order: SortOrder = SortOrder.ASC,
    include_deleted: bool = False,
    distribution_id: UUID | None = None,
    device_type: ProtectiveDeviceType | None = None,
    location_id: UUID | None = None,
) -> Page[ProtectiveDeviceRead]:
    try:
        return ElectricalProtectiveDeviceService(session).list_read(
            page=page,
            page_size=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            include_deleted=include_deleted,
            distribution_id=distribution_id,
            device_type=device_type,
            location_id=location_id,
        )
    except ElectricalSortError as exc:
        raise _translate_error(exc) from exc


@router.post(
    "/protective-devices",
    response_model=ProtectiveDeviceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_protective_device(
    payload: ProtectiveDeviceWrite,
    session: SessionDependency,
) -> ProtectiveDeviceRead:
    try:
        return ElectricalProtectiveDeviceService(session).create(payload)
    except (ElectricalValidationError, ElectricalConflictError) as exc:
        raise _translate_error(exc) from exc


@router.get(
    "/protective-devices/{device_id}",
    response_model=ProtectiveDeviceRead,
)
def get_protective_device(
    device_id: UUID,
    session: SessionDependency,
    include_deleted: bool = False,
) -> ProtectiveDeviceRead:
    try:
        return ElectricalProtectiveDeviceService(session).get_read(
            device_id,
            include_deleted=include_deleted,
        )
    except (ElectricalNotFoundError, ElectricalValidationError) as exc:
        raise _translate_error(exc) from exc


@router.put(
    "/protective-devices/{device_id}",
    response_model=ProtectiveDeviceRead,
)
def update_protective_device(
    device_id: UUID,
    payload: ProtectiveDeviceWrite,
    session: SessionDependency,
) -> ProtectiveDeviceRead:
    try:
        return ElectricalProtectiveDeviceService(session).update(device_id, payload)
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.delete(
    "/protective-devices/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_protective_device(device_id: UUID, session: SessionDependency) -> Response:
    try:
        ElectricalProtectiveDeviceService(session).delete(device_id)
    except (ElectricalNotFoundError, ElectricalConflictError) as exc:
        raise _translate_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
