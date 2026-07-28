from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.asset_engine import Page
from app.schemas.electrical_topology import (
    ElectricalConnectionRead,
    ElectricalConnectionWrite,
    ElectricalEndpointRead,
    ElectricalTopologyRead,
)
from app.services.electrical import (
    ElectricalConflictError,
    ElectricalNotFoundError,
    ElectricalValidationError,
)
from app.services.electrical_topology import ElectricalTopologyService

router = APIRouter(prefix="/electrical", tags=["electrical"])
SessionDependency = Annotated[Session, Depends(get_session)]
PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


def _translate_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ElectricalNotFoundError):
        return HTTPException(status_code=404, detail="Electrical connection not found")
    if isinstance(exc, ElectricalValidationError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, ElectricalConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=500, detail="Unexpected electrical topology error")


@router.get("/connection-endpoints", response_model=Page[ElectricalEndpointRead])
def list_connection_endpoints(
    session: SessionDependency,
    page: PageNumber = 1,
    page_size: PageSize = 25,
    search: str | None = None,
) -> Page[ElectricalEndpointRead]:
    try:
        return ElectricalTopologyService(session).endpoint_page(
            page=page,
            page_size=page_size,
            search=search,
        )
    except ElectricalValidationError as exc:
        raise _translate_error(exc) from exc


@router.get("/connections", response_model=list[ElectricalConnectionRead])
def list_connections(session: SessionDependency) -> list[ElectricalConnectionRead]:
    try:
        return ElectricalTopologyService(session).list_connections()
    except ElectricalValidationError as exc:
        raise _translate_error(exc) from exc


@router.post(
    "/connections",
    response_model=ElectricalConnectionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_connection(
    payload: ElectricalConnectionWrite,
    session: SessionDependency,
) -> ElectricalConnectionRead:
    try:
        return ElectricalTopologyService(session).create(payload)
    except (ElectricalValidationError, ElectricalConflictError) as exc:
        raise _translate_error(exc) from exc


@router.put("/connections/{connection_id}", response_model=ElectricalConnectionRead)
def update_connection(
    connection_id: UUID,
    payload: ElectricalConnectionWrite,
    session: SessionDependency,
) -> ElectricalConnectionRead:
    try:
        return ElectricalTopologyService(session).update(connection_id, payload)
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.delete(
    "/connections/{connection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_connection(connection_id: UUID, session: SessionDependency) -> Response:
    try:
        ElectricalTopologyService(session).delete(connection_id)
    except (
        ElectricalNotFoundError,
        ElectricalValidationError,
        ElectricalConflictError,
    ) as exc:
        raise _translate_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/topology", response_model=ElectricalTopologyRead)
def get_topology(session: SessionDependency) -> ElectricalTopologyRead:
    try:
        return ElectricalTopologyService(session).topology()
    except ElectricalValidationError as exc:
        raise _translate_error(exc) from exc
