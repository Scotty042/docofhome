from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.network import (
    NetworkAddressRead,
    NetworkAddressWrite,
    NetworkConnectionRead,
    NetworkConnectionWrite,
    NetworkDeviceCandidateRead,
    NetworkDeviceRead,
    NetworkDeviceWrite,
    NetworkInterfaceRead,
    NetworkInterfaceWrite,
    NetworkIpActionRead,
    NetworkIpOverviewRead,
    NetworkIpStatus,
    NetworkRole,
    NetworkSegmentRead,
    NetworkSegmentWrite,
    NetworkSummaryRead,
    NetworkTopologyRead,
)
from app.services.network import (
    NetworkConflictError,
    NetworkError,
    NetworkNotFoundError,
    NetworkService,
    NetworkValidationError,
)

router = APIRouter(prefix="/network", tags=["network"])
SessionDependency = Annotated[Session, Depends(get_session)]


def _http_error(exc: NetworkError) -> HTTPException:
    if isinstance(exc, NetworkNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, NetworkValidationError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, NetworkConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=500, detail="Netzwerkdaten konnten nicht verarbeitet werden")


def _call(callback):
    try:
        return callback()
    except NetworkError as exc:
        raise _http_error(exc) from exc


@router.get("/summary", response_model=NetworkSummaryRead)
def summary(session: SessionDependency) -> NetworkSummaryRead:
    return _call(lambda: NetworkService(session).summary())


@router.get("/topology", response_model=NetworkTopologyRead)
def topology(session: SessionDependency) -> NetworkTopologyRead:
    return _call(lambda: NetworkService(session).topology())


@router.get("/device-candidates", response_model=list[NetworkDeviceCandidateRead])
def device_candidates(session: SessionDependency) -> list[NetworkDeviceCandidateRead]:
    return _call(lambda: NetworkService(session).device_candidates())


@router.get("/devices", response_model=list[NetworkDeviceRead])
def list_devices(
    session: SessionDependency,
    search: Annotated[str | None, Query(max_length=100)] = None,
    role: NetworkRole | None = None,
    include_archived: bool = False,
) -> list[NetworkDeviceRead]:
    return _call(
        lambda: NetworkService(session).list_devices(
            search=search,
            role=role,
            include_archived=include_archived,
        )
    )


@router.post("/devices", response_model=NetworkDeviceRead, status_code=status.HTTP_201_CREATED)
def create_device(payload: NetworkDeviceWrite, session: SessionDependency) -> NetworkDeviceRead:
    return _call(lambda: NetworkService(session).create_device(payload))


@router.get("/devices/{record_id}", response_model=NetworkDeviceRead)
def get_device(
    record_id: UUID,
    session: SessionDependency,
    include_archived: bool = False,
) -> NetworkDeviceRead:
    return _call(
        lambda: NetworkService(session).get_device(record_id, include_archived=include_archived)
    )


@router.put("/devices/{record_id}", response_model=NetworkDeviceRead)
def update_device(
    record_id: UUID,
    payload: NetworkDeviceWrite,
    session: SessionDependency,
) -> NetworkDeviceRead:
    return _call(lambda: NetworkService(session).update_device(record_id, payload))


@router.delete("/devices/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(record_id: UUID, session: SessionDependency) -> Response:
    _call(lambda: NetworkService(session).delete_device(record_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/segments", response_model=list[NetworkSegmentRead])
def list_segments(session: SessionDependency) -> list[NetworkSegmentRead]:
    return _call(lambda: NetworkService(session).list_segments())


@router.post("/segments", response_model=NetworkSegmentRead, status_code=status.HTTP_201_CREATED)
def create_segment(payload: NetworkSegmentWrite, session: SessionDependency) -> NetworkSegmentRead:
    return _call(lambda: NetworkService(session).create_segment(payload))


@router.put("/segments/{record_id}", response_model=NetworkSegmentRead)
def update_segment(
    record_id: UUID,
    payload: NetworkSegmentWrite,
    session: SessionDependency,
) -> NetworkSegmentRead:
    return _call(lambda: NetworkService(session).update_segment(record_id, payload))


@router.delete("/segments/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_segment(record_id: UUID, session: SessionDependency) -> Response:
    _call(lambda: NetworkService(session).delete_segment(record_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/interfaces", response_model=list[NetworkInterfaceRead])
def list_interfaces(
    session: SessionDependency,
    device_id: UUID | None = None,
) -> list[NetworkInterfaceRead]:
    return _call(lambda: NetworkService(session).list_interfaces(device_id=device_id))


@router.post(
    "/interfaces", response_model=NetworkInterfaceRead, status_code=status.HTTP_201_CREATED
)
def create_interface(
    payload: NetworkInterfaceWrite, session: SessionDependency
) -> NetworkInterfaceRead:
    return _call(lambda: NetworkService(session).create_interface(payload))


@router.put("/interfaces/{record_id}", response_model=NetworkInterfaceRead)
def update_interface(
    record_id: UUID,
    payload: NetworkInterfaceWrite,
    session: SessionDependency,
) -> NetworkInterfaceRead:
    return _call(lambda: NetworkService(session).update_interface(record_id, payload))


@router.delete("/interfaces/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interface(record_id: UUID, session: SessionDependency) -> Response:
    _call(lambda: NetworkService(session).delete_interface(record_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)




@router.get("/ip-addresses", response_model=list[NetworkIpOverviewRead])
def ip_addresses(
    session: SessionDependency,
    device_id: UUID | None = None,
    status_filter: Annotated[NetworkIpStatus | None, Query(alias="status")] = None,
) -> list[NetworkIpOverviewRead]:
    return _call(lambda: NetworkService(session).list_ip_overview(device_id=device_id, status=status_filter))


@router.post("/ip-addresses/{observed_id}/accept", response_model=NetworkIpActionRead)
def accept_ip_address(observed_id: UUID, session: SessionDependency) -> NetworkIpActionRead:
    return _call(lambda: NetworkService(session).accept_observed_address(observed_id))


@router.post("/ip-addresses/{observed_id}/ignore", response_model=NetworkIpActionRead)
def ignore_ip_address(observed_id: UUID, session: SessionDependency) -> NetworkIpActionRead:
    return _call(lambda: NetworkService(session).ignore_observed_address(observed_id))


@router.get("/addresses", response_model=list[NetworkAddressRead])
def list_addresses(
    session: SessionDependency,
    interface_id: UUID | None = None,
    device_id: UUID | None = None,
    segment_id: UUID | None = None,
) -> list[NetworkAddressRead]:
    return _call(
        lambda: NetworkService(session).list_addresses(
            interface_id=interface_id,
            device_id=device_id,
            segment_id=segment_id,
        )
    )


@router.post("/addresses", response_model=NetworkAddressRead, status_code=status.HTTP_201_CREATED)
def create_address(payload: NetworkAddressWrite, session: SessionDependency) -> NetworkAddressRead:
    return _call(lambda: NetworkService(session).create_address(payload))


@router.put("/addresses/{record_id}", response_model=NetworkAddressRead)
def update_address(
    record_id: UUID,
    payload: NetworkAddressWrite,
    session: SessionDependency,
) -> NetworkAddressRead:
    return _call(lambda: NetworkService(session).update_address(record_id, payload))


@router.delete("/addresses/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(record_id: UUID, session: SessionDependency) -> Response:
    _call(lambda: NetworkService(session).delete_address(record_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/connections", response_model=list[NetworkConnectionRead])
def list_connections(
    session: SessionDependency,
    device_id: UUID | None = None,
) -> list[NetworkConnectionRead]:
    return _call(lambda: NetworkService(session).list_connections(device_id=device_id))


@router.post(
    "/connections", response_model=NetworkConnectionRead, status_code=status.HTTP_201_CREATED
)
def create_connection(
    payload: NetworkConnectionWrite,
    session: SessionDependency,
) -> NetworkConnectionRead:
    return _call(lambda: NetworkService(session).create_connection(payload))


@router.put("/connections/{record_id}", response_model=NetworkConnectionRead)
def update_connection(
    record_id: UUID,
    payload: NetworkConnectionWrite,
    session: SessionDependency,
) -> NetworkConnectionRead:
    return _call(lambda: NetworkService(session).update_connection(record_id, payload))


@router.delete("/connections/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(record_id: UUID, session: SessionDependency) -> Response:
    _call(lambda: NetworkService(session).delete_connection(record_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
