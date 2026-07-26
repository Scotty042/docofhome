from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import get_session
from app.main import app
from app.models.asset_engine import Asset, AssetType


@pytest.fixture
def link_client() -> Generator[tuple[TestClient, UUID, UUID]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        asset_type = AssetType(name="Smart Home", code_prefix="SH")
        session.add(asset_type)
        session.commit()
        session.refresh(asset_type)
        first = Asset(
            name="Erstes Asset",
            jarvis_code="SH-001",
            asset_type_id=asset_type.id,
        )
        second = Asset(
            name="Zweites Asset",
            jarvis_code="SH-002",
            asset_type_id=asset_type.id,
        )
        session.add(first)
        session.add(second)
        session.commit()
        session.refresh(first)
        session.refresh(second)

    def override_session() -> Generator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            yield client, first.id, second.id
    finally:
        app.dependency_overrides.clear()


def test_home_assistant_asset_link_api_roundtrip(
    link_client: tuple[TestClient, UUID, UUID],
) -> None:
    client, first_id, second_id = link_client

    created = client.put(
        "/api/v1/home-assistant/links/entity/sensor.grid_power",
        json={"asset_id": str(first_id)},
    )
    assert created.status_code == 200
    assert created.json()["asset_code"] == "SH-001"

    reassigned = client.put(
        "/api/v1/home-assistant/links/entity/sensor.grid_power",
        json={"asset_id": str(second_id)},
    )
    assert reassigned.status_code == 200
    assert reassigned.json()["id"] == created.json()["id"]
    assert reassigned.json()["asset_code"] == "SH-002"

    listed = client.get("/api/v1/home-assistant/links?object_type=entity")
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1

    filtered = client.get(f"/api/v1/home-assistant/links?asset_id={second_id}")
    assert filtered.status_code == 200
    assert [item["external_id"] for item in filtered.json()["items"]] == ["sensor.grid_power"]

    bindings = client.get(f"/api/v1/home-assistant/assets/{second_id}")
    assert bindings.status_code == 200, bindings.text
    assert [item["external_id"] for item in bindings.json()["entity_links"]] == [
        "sensor.grid_power"
    ]
    assert bindings.json()["entities"] == []
    assert bindings.json()["missing_entity_ids"] == ["sensor.grid_power"]
    assert bindings.json()["warning"]

    deleted = client.delete("/api/v1/home-assistant/links/entity/sensor.grid_power")
    assert deleted.status_code == 204
    assert client.get("/api/v1/home-assistant/links").json()["items"] == []
