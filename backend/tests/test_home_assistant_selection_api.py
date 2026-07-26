from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import get_session
from app.main import app


@pytest.fixture
def selection_client() -> Generator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_session() -> Generator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def test_selection_api_defaults_and_roundtrips(selection_client: TestClient) -> None:
    initial = selection_client.get("/api/v1/home-assistant/selection")
    assert initial.status_code == 200
    assert initial.json() == {
        "mode": "all",
        "entity_ids": [],
        "selected_count": 0,
        "updated_at": None,
    }

    saved = selection_client.put(
        "/api/v1/home-assistant/selection",
        json={
            "mode": "selected",
            "entity_ids": ["sensor.grid_power", "light.kitchen", "sensor.grid_power"],
        },
    )
    assert saved.status_code == 200
    assert saved.json()["entity_ids"] == ["light.kitchen", "sensor.grid_power"]
    assert saved.json()["selected_count"] == 2


def test_selection_api_rejects_invalid_entity_id(selection_client: TestClient) -> None:
    response = selection_client.put(
        "/api/v1/home-assistant/selection",
        json={"mode": "selected", "entity_ids": ["invalid id"]},
    )
    assert response.status_code == 422
    assert "Ungültige Home-Assistant-Entitäts-ID" in response.json()["detail"]
