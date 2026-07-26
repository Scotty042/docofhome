from datetime import UTC, datetime
from uuid import UUID

import httpx
import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models.asset_engine import Asset, AssetType
from app.models.integration_setting import IntegrationSetting
from app.schemas.immich import ImmichLinkWrite
from app.services.immich import (
    ImmichConfigurationError,
    ImmichLinkConflictError,
    ImmichService,
)

IMAGE_ID = UUID("11111111-1111-4111-8111-111111111111")


def create_session(*, enabled: bool = True) -> tuple[Session, Asset]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    asset_type = AssetType(name="Distribution", code_prefix="DIST")
    session.add(asset_type)
    session.commit()
    session.refresh(asset_type)
    asset = Asset(
        name="Main panel",
        jarvis_code="DIST-001",
        asset_type_id=asset_type.id,
    )
    session.add(asset)
    session.add(
        IntegrationSetting(
            kind="immich",
            enabled=enabled,
            base_url="http://immich.local",
            secret="immich-secret",
        )
    )
    session.commit()
    session.refresh(asset)
    return session, asset


def image_handler(request: httpx.Request) -> httpx.Response:
    assert request.method == "GET"
    assert request.url.path == f"/api/assets/{IMAGE_ID}"
    return httpx.Response(
        200,
        json={
            "id": str(IMAGE_ID),
            "type": "IMAGE",
            "originalFileName": "main-panel.jpg",
            "fileCreatedAt": "2026-07-20T10:30:00Z",
            "width": 1600,
            "height": 1200,
            "isFavorite": False,
        },
    )


def test_link_creation_persists_snapshot_and_prevents_duplicates() -> None:
    session, asset = create_session()
    service = ImmichService(session, transport=httpx.MockTransport(image_handler))
    payload = ImmichLinkWrite(asset_id=asset.id, immich_asset_id=IMAGE_ID)

    created = service.create_link(payload)

    assert created.original_file_name == "main-panel.jpg"
    assert created.thumbnail_url.endswith(f"/{IMAGE_ID}/thumbnail")
    assert service.list_links(asset_id=asset.id).items[0].id == created.id
    with pytest.raises(ImmichLinkConflictError, match="bereits"):
        service.create_link(payload)


def test_listing_and_unlinking_are_local_when_immich_is_unavailable() -> None:
    session, asset = create_session()
    created = ImmichService(session, transport=httpx.MockTransport(image_handler)).create_link(
        ImmichLinkWrite(asset_id=asset.id, immich_asset_id=IMAGE_ID)
    )
    offline_service = ImmichService(
        session,
        transport=httpx.MockTransport(lambda _: (_ for _ in ()).throw(httpx.ConnectError("down"))),
    )

    assert (
        offline_service.list_links(asset_id=asset.id).items[0].original_file_name
        == "main-panel.jpg"
    )
    offline_service.delete_link(created.id)
    assert offline_service.list_links(asset_id=asset.id).items == []


def test_archived_assets_cannot_receive_new_links() -> None:
    session, asset = create_session()
    asset.deleted_at = datetime.now(UTC)
    session.add(asset)
    session.commit()

    with pytest.raises(ImmichLinkConflictError, match="Archivierte"):
        ImmichService(session, transport=httpx.MockTransport(image_handler)).create_link(
            ImmichLinkWrite(asset_id=asset.id, immich_asset_id=IMAGE_ID)
        )


def test_disabled_integration_blocks_remote_browse_but_not_local_listing() -> None:
    session, asset = create_session(enabled=False)
    service = ImmichService(session)

    with pytest.raises(ImmichConfigurationError, match="deaktiviert"):
        service.browse_images(page=1, page_size=24)
    assert service.list_links(asset_id=asset.id).items == []
