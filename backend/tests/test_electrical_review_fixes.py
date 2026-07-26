from collections.abc import Generator
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import get_session
from app.main import app
from app.models.electrical import ElectricalComponent, ElectricalDistribution


@pytest.fixture
def client_and_engine(tmp_path: Path) -> Generator[tuple[TestClient, Engine]]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'electrical-review.sqlite3'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    def override_session() -> Generator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client, engine
    app.dependency_overrides.clear()


def create(
    client: TestClient,
    endpoint: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    response = client.post(f"/api/v1/{endpoint}", json=payload)
    assert response.status_code == 201, response.text
    result: dict[str, Any] = response.json()
    return result


def setup_assets(client: TestClient) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    root = create(client, "locations", {"name": "House", "location_type": "building"})
    room = create(
        client,
        "locations",
        {"name": "Electrical room", "location_type": "room", "parent_id": root["id"]},
    )
    asset_type = create(client, "asset-types", {"name": "Elektrische Verteilung"})
    assets = [
        create(
            client,
            "assets",
            {
                "name": name,
                "asset_type_id": asset_type["id"],
                "location_id": room["id"],
                "status": "active",
            },
        )
        for name in ("Distribution", "Other asset", "Protective device")
    ]
    return room, assets


def distribution_payload(
    asset_id: str,
    *,
    rows: int | None = 3,
    modules: int | None = 24,
) -> dict[str, Any]:
    return {
        "asset_id": asset_id,
        "parent_distribution_id": None,
        "distribution_type": "main",
        "designation": "HV",
        "rows": rows,
        "modules_per_row": modules,
        "description": None,
        "notes": None,
    }


def device_payload(asset_id: str, distribution_id: str) -> dict[str, Any]:
    return {
        "asset_id": asset_id,
        "distribution_id": distribution_id,
        "device_type": "mcb",
        "row_number": 3,
        "start_position": 20,
        "module_width": 2,
        "rated_current_a": 16,
        "residual_current_ma": None,
        "characteristic": "B",
        "poles": 1,
        "breaking_capacity_ka": 6,
        "rcd_type": None,
        "fuse_type": None,
        "spd_type": None,
        "description": None,
        "notes": None,
    }


def test_role_asset_is_immutable_and_target_remains_available(
    client_and_engine: tuple[TestClient, Engine],
) -> None:
    client, _ = client_and_engine
    _, assets = setup_assets(client)
    distribution = create(
        client,
        "electrical/distributions",
        distribution_payload(assets[0]["id"]),
    )

    changed = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}",
        json=distribution_payload(assets[1]["id"]),
    )
    assert changed.status_code == 409
    assert changed.json()["detail"] == "Electrical role asset identity is immutable"

    stored_response = client.get(f"/api/v1/electrical/distributions/{distribution['id']}")
    stored = stored_response.json()
    assert stored["id"] == distribution["id"]
    assert stored["asset_id"] == assets[0]["id"]

    candidates = client.get(
        "/api/v1/electrical/available-assets",
        params={"role": "distribution", "search": "Other asset"},
    )
    assert candidates.status_code == 200
    candidate_ids = [item["id"] for item in candidates.json()["items"]]
    assert candidate_ids == [assets[1]["id"]]


def test_distribution_capacity_cannot_exclude_active_device(
    client_and_engine: tuple[TestClient, Engine],
) -> None:
    client, _ = client_and_engine
    _, assets = setup_assets(client)
    distribution = create(
        client,
        "electrical/distributions",
        distribution_payload(assets[0]["id"]),
    )
    create(
        client,
        "electrical/protective-devices",
        device_payload(assets[2]["id"], distribution["id"]),
    )

    too_few_rows = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}",
        json=distribution_payload(assets[0]["id"], rows=2, modules=24),
    )
    too_few_modules = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}",
        json=distribution_payload(assets[0]["id"], rows=3, modules=20),
    )
    exact_capacity = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}",
        json=distribution_payload(assets[0]["id"], rows=3, modules=21),
    )

    assert too_few_rows.status_code == 409
    assert "row 3" in too_few_rows.json()["detail"]
    assert too_few_modules.status_code == 409
    assert "modules 20-21" in too_few_modules.json()["detail"]
    assert exact_capacity.status_code == 200
    assert exact_capacity.json()["rows"] == 3
    assert exact_capacity.json()["modules_per_row"] == 21


def test_specialized_table_rejects_wrong_component_role(
    client_and_engine: tuple[TestClient, Engine],
) -> None:
    client, engine = client_and_engine
    _, assets = setup_assets(client)

    with Session(engine) as session:
        component = ElectricalComponent(
            asset_id=UUID(assets[0]["id"]),
            role="protective_device",
        )
        session.add(component)
        session.flush()
        session.add(
            ElectricalDistribution(
                id=component.id,
                distribution_type="main",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_protective_device_asset_is_immutable(
    client_and_engine: tuple[TestClient, Engine],
) -> None:
    client, _ = client_and_engine
    _, assets = setup_assets(client)
    distribution = create(
        client,
        "electrical/distributions",
        distribution_payload(assets[0]["id"]),
    )
    device = create(
        client,
        "electrical/protective-devices",
        device_payload(assets[2]["id"], distribution["id"]),
    )

    changed = client.put(
        f"/api/v1/electrical/protective-devices/{device['id']}",
        json=device_payload(assets[1]["id"], distribution["id"]),
    )

    assert changed.status_code == 409
    assert changed.json()["detail"] == "Electrical role asset identity is immutable"
    stored = client.get(f"/api/v1/electrical/protective-devices/{device['id']}").json()
    assert stored["asset_id"] == assets[2]["id"]
    candidates = client.get(
        "/api/v1/electrical/available-assets",
        params={"role": "protective_device", "search": "Other asset"},
    )
    assert candidates.status_code == 200
    candidate_ids = [item["id"] for item in candidates.json()["items"]]
    assert candidate_ids == [assets[1]["id"]]
