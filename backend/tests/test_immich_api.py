from collections.abc import Generator
from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.connectors.immich import ImmichConnector, ImmichImage, ImmichImagePage, ImmichThumbnail
from app.db.session import get_session
from app.main import app
from app.models.asset_engine import Asset, AssetType
from app.models.integration_setting import IntegrationSetting

IMAGE_ID = UUID("11111111-1111-4111-8111-111111111111")


@pytest.fixture
def immich_client(monkeypatch: pytest.MonkeyPatch) -> Generator[tuple[TestClient, Asset]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        asset_type = AssetType(name="Panel", code_prefix="PNL")
        session.add(asset_type)
        session.commit()
        session.refresh(asset_type)
        asset = Asset(name="Main", jarvis_code="PNL-001", asset_type_id=asset_type.id)
        session.add(asset)
        session.add(
            IntegrationSetting(
                kind="immich",
                enabled=True,
                base_url="http://immich.local",
                secret="immich-secret",
            )
        )
        session.commit()
        session.refresh(asset)
        session.expunge(asset)

    image = ImmichImage(
        immich_asset_id=str(IMAGE_ID),
        original_file_name="panel.jpg",
        file_created_at=datetime(2026, 7, 20, 10, 30, tzinfo=UTC),
        width=1600,
        height=1200,
        is_favorite=True,
    )
    monkeypatch.setattr(
        ImmichConnector,
        "search_images",
        lambda self, **kwargs: ImmichImagePage(
            items=(image,),
            total=1,
            page=int(kwargs["page"]),
            page_size=int(kwargs["page_size"]),
            pages=1,
        ),
    )
    monkeypatch.setattr(ImmichConnector, "get_image", lambda self, _: image)
    monkeypatch.setattr(
        ImmichConnector,
        "get_thumbnail",
        lambda self, _: ImmichThumbnail(content=b"jpeg", media_type="image/jpeg"),
    )

    def override_session() -> Generator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            yield client, asset
    finally:
        app.dependency_overrides.clear()


def test_immich_api_browses_links_lists_and_unlinks(
    immich_client: tuple[TestClient, Asset],
) -> None:
    client, asset = immich_client

    browse = client.get("/api/v1/immich/assets?page=1&page_size=24&search=panel")
    assert browse.status_code == 200
    assert browse.json()["items"][0]["thumbnail_url"].startswith("/api/v1/immich/")

    created = client.post(
        "/api/v1/immich/links",
        json={"asset_id": str(asset.id), "immich_asset_id": str(IMAGE_ID)},
    )
    assert created.status_code == 201
    link_id = created.json()["id"]

    listed = client.get(f"/api/v1/immich/links?asset_id={asset.id}")
    assert listed.status_code == 200
    assert listed.json()["items"][0]["original_file_name"] == "panel.jpg"

    deleted = client.delete(f"/api/v1/immich/links/{link_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/immich/links?asset_id={asset.id}").json()["items"] == []


def test_immich_thumbnail_proxy_sets_safe_response_headers(
    immich_client: tuple[TestClient, Asset],
) -> None:
    client, _ = immich_client

    response = client.get(f"/api/v1/immich/assets/{IMAGE_ID}/thumbnail")

    assert response.status_code == 200
    assert response.content == b"jpeg"
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["cache-control"] == "private, max-age=300"
    assert "immich-secret" not in str(response.headers)
