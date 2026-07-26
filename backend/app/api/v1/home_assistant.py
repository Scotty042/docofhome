from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.db.session import get_session
from app.models.asset_engine import Asset
from app.schemas.home_assistant import (
    HomeAssistantAssetBindingsRead,
    HomeAssistantAssetBindingsWrite,
    HomeAssistantAssetLinkListRead,
    HomeAssistantAssetLinkRead,
    HomeAssistantAssetLinkWrite,
    HomeAssistantDeviceListRead,
    HomeAssistantEntityListRead,
    HomeAssistantObjectType,
    HomeAssistantOverviewRead,
    HomeAssistantSelectionRead,
    HomeAssistantSelectionScope,
    HomeAssistantSelectionWrite,
)
from app.services.home_assistant import (
    HomeAssistantConfigurationError,
    HomeAssistantConnectionError,
    HomeAssistantService,
)
from app.services.home_assistant_links import (
    HomeAssistantLinkAssetError,
    HomeAssistantLinkConflictError,
    HomeAssistantLinkError,
    HomeAssistantLinkNotFoundError,
    HomeAssistantLinkService,
)
from app.services.home_assistant_selection import (
    HomeAssistantSelectionError,
    HomeAssistantSelectionService,
)

router = APIRouter(prefix="/home-assistant", tags=["home-assistant"])
SessionDependency = Annotated[Session, Depends(get_session)]
SelectionScopeQuery = Annotated[HomeAssistantSelectionScope, Query()]


@router.get("/overview", response_model=HomeAssistantOverviewRead)
def overview(
    session: SessionDependency,
    refresh: bool = Query(default=False),
) -> HomeAssistantOverviewRead:
    try:
        return HomeAssistantService(session).overview(refresh=refresh)
    except HomeAssistantConfigurationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except HomeAssistantConnectionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/devices", response_model=HomeAssistantDeviceListRead)
def devices(
    session: SessionDependency,
    search: str | None = Query(default=None, max_length=200),
    area_id: str | None = Query(default=None, max_length=255),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    refresh: bool = Query(default=False),
    selection_scope: SelectionScopeQuery = HomeAssistantSelectionScope.VISIBLE,
) -> HomeAssistantDeviceListRead:
    try:
        return HomeAssistantService(session).devices(
            search=search,
            area_id=area_id,
            offset=offset,
            limit=limit,
            refresh=refresh,
            selection_scope=selection_scope,
        )
    except HomeAssistantConfigurationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except HomeAssistantConnectionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/entities", response_model=HomeAssistantEntityListRead)
def entities(
    session: SessionDependency,
    search: str | None = Query(default=None, max_length=200),
    domain: str | None = Query(default=None, max_length=100),
    device_id: str | None = Query(default=None, max_length=255),
    area_id: str | None = Query(default=None, max_length=255),
    available: bool | None = Query(default=None),
    device_class: str | None = Query(default=None, max_length=100),
    unit: str | None = Query(default=None, max_length=100),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    refresh: bool = Query(default=False),
    selection_scope: SelectionScopeQuery = HomeAssistantSelectionScope.VISIBLE,
) -> HomeAssistantEntityListRead:
    try:
        return HomeAssistantService(session).entities(
            search=search,
            domain=domain,
            device_id=device_id,
            area_id=area_id,
            available=available,
            device_class=device_class,
            unit=unit,
            offset=offset,
            limit=limit,
            refresh=refresh,
            selection_scope=selection_scope,
        )
    except HomeAssistantConfigurationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except HomeAssistantConnectionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/selection", response_model=HomeAssistantSelectionRead)
def get_selection(session: SessionDependency) -> HomeAssistantSelectionRead:
    return HomeAssistantSelectionService(session).get()


@router.put("/selection", response_model=HomeAssistantSelectionRead)
def replace_selection(
    payload: HomeAssistantSelectionWrite,
    session: SessionDependency,
) -> HomeAssistantSelectionRead:
    try:
        return HomeAssistantSelectionService(session).replace(payload)
    except HomeAssistantSelectionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/links", response_model=HomeAssistantAssetLinkListRead)
def list_links(
    session: SessionDependency,
    object_type: HomeAssistantObjectType | None = None,
    asset_id: UUID | None = None,
) -> HomeAssistantAssetLinkListRead:
    try:
        return HomeAssistantLinkService(session).list_links(
            object_type=object_type,
            asset_id=asset_id,
        )
    except HomeAssistantLinkAssetError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get(
    "/assets/{asset_id}",
    response_model=HomeAssistantAssetBindingsRead,
)
def asset_bindings(
    asset_id: UUID,
    session: SessionDependency,
    refresh: bool = Query(default=False),
) -> HomeAssistantAssetBindingsRead:
    asset = session.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset wurde nicht gefunden.")

    links = HomeAssistantLinkService(session).list_links(asset_id=asset_id).items
    device_links = [link for link in links if link.object_type == HomeAssistantObjectType.DEVICE]
    entity_links = [link for link in links if link.object_type == HomeAssistantObjectType.ENTITY]
    device_ids = {link.external_id for link in device_links}
    entity_ids = {link.external_id for link in entity_links}
    if not device_ids and not entity_ids:
        return HomeAssistantAssetBindingsRead(
            asset_id=asset_id,
            device_links=[],
            entity_links=[],
            devices=[],
            entities=[],
            missing_device_ids=[],
            missing_entity_ids=[],
        )

    try:
        devices, entities, missing_devices, missing_entities, refreshed_at = HomeAssistantService(
            session
        ).linked_objects(
            device_ids=device_ids,
            entity_ids=entity_ids,
            refresh=refresh,
        )
        warning = None
    except (HomeAssistantConfigurationError, HomeAssistantConnectionError) as exc:
        devices = []
        entities = []
        missing_devices = sorted(device_ids)
        missing_entities = sorted(entity_ids)
        refreshed_at = None
        warning = str(exc)

    return HomeAssistantAssetBindingsRead(
        asset_id=asset_id,
        device_links=device_links,
        entity_links=entity_links,
        devices=devices,
        entities=entities,
        missing_device_ids=missing_devices,
        missing_entity_ids=missing_entities,
        warning=warning,
        refreshed_at=refreshed_at,
    )


@router.put(
    "/assets/{asset_id}/bindings",
    response_model=HomeAssistantAssetBindingsRead,
)
def replace_asset_bindings(
    asset_id: UUID,
    payload: HomeAssistantAssetBindingsWrite,
    session: SessionDependency,
) -> HomeAssistantAssetBindingsRead:
    if session.get(Asset, asset_id) is None:
        raise HTTPException(status_code=404, detail="Asset wurde nicht gefunden.")
    service = HomeAssistantLinkService(session)
    try:
        service.replace_asset_bindings(asset_id, payload)
    except HomeAssistantLinkAssetError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HomeAssistantLinkConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return asset_bindings(asset_id, session, refresh=False)


@router.put(
    "/links/{object_type}/{external_id}",
    response_model=HomeAssistantAssetLinkRead,
)
def upsert_link(
    object_type: HomeAssistantObjectType,
    external_id: str,
    payload: HomeAssistantAssetLinkWrite,
    session: SessionDependency,
) -> HomeAssistantAssetLinkRead:
    try:
        return HomeAssistantLinkService(session).upsert(
            object_type=object_type,
            external_id=external_id,
            asset_id=payload.asset_id,
            role=payload.role,
        )
    except HomeAssistantLinkAssetError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HomeAssistantLinkConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except HomeAssistantLinkError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete(
    "/links/{object_type}/{external_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_link(
    object_type: HomeAssistantObjectType,
    external_id: str,
    session: SessionDependency,
) -> Response:
    try:
        HomeAssistantLinkService(session).delete(
            object_type=object_type,
            external_id=external_id,
        )
    except HomeAssistantLinkNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HomeAssistantLinkError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
