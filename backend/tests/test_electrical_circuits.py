from collections.abc import Generator
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import get_session
from app.main import app
from app.models.electrical_circuit import ElectricalCircuit


@pytest.fixture
def circuit_client(tmp_path: Path) -> Generator[tuple[TestClient, Engine]]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'circuits.sqlite3'}",
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


def create(client: TestClient, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post(f"/api/v1/{endpoint}", json=payload)
    assert response.status_code == 201, response.text
    result: dict[str, Any] = response.json()
    return result


def prepare_electrical_records(
    client: TestClient,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    building = create(
        client,
        "locations",
        {"name": "Home", "location_type": "building"},
    )
    room = create(
        client,
        "locations",
        {
            "name": "Technical room",
            "location_type": "room",
            "parent_id": building["id"],
        },
    )
    asset_type = create(client, "asset-types", {"name": "Elektrische Verteilung"})

    def asset(name: str) -> dict[str, Any]:
        return create(
            client,
            "assets",
            {
                "name": name,
                "asset_type_id": asset_type["id"],
                "location_id": room["id"],
                "status": "active",
            },
        )

    distribution_one = create(
        client,
        "electrical/distributions",
        {
            "asset_id": asset("Main distribution")["id"],
            "parent_distribution_id": None,
            "distribution_type": "main",
            "layout_mode": "rows",
            "designation": "HV",
            "rows": 2,
            "modules_per_row": 12,
            "description": None,
            "notes": None,
        },
    )
    distribution_two = create(
        client,
        "electrical/distributions",
        {
            "asset_id": asset("Garage distribution")["id"],
            "parent_distribution_id": None,
            "distribution_type": "main",
            "layout_mode": "rows",
            "designation": "Garage",
            "rows": None,
            "modules_per_row": None,
            "description": None,
            "notes": None,
        },
    )

    def device(name: str, distribution_id: str) -> dict[str, Any]:
        return create(
            client,
            "electrical/protective-devices",
            {
                "asset_id": asset(name)["id"],
                "distribution_id": distribution_id,
                "area_id": None,
                "device_type": "mcb",
                "row_number": None,
                "start_position": None,
                "module_width": None,
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
            },
        )

    return (
        distribution_one,
        distribution_two,
        device("Kitchen breaker", distribution_one["id"]),
        device("Garage breaker", distribution_two["id"]),
    )


def circuit_payload(
    distribution_id: str,
    *,
    name: str,
    number: str | None,
    device_id: str | None = None,
) -> dict[str, Any]:
    return {
        "distribution_id": distribution_id,
        "protective_device_id": device_id,
        "name": name,
        "circuit_number": number,
        "description": "Documented circuit",
        "notes": None,
    }


def test_circuit_crud_search_filter_pagination_and_archive_guards(
    circuit_client: tuple[TestClient, Engine],
) -> None:
    client, _ = circuit_client
    distribution, other_distribution, device, other_device = prepare_electrical_records(client)
    circuit = create(
        client,
        "electrical/circuits",
        circuit_payload(
            distribution["id"],
            name=" Kitchen sockets ",
            number=" F1 ",
            device_id=device["id"],
        ),
    )
    create(
        client,
        "electrical/circuits",
        circuit_payload(distribution["id"], name="Lighting", number="F2"),
    )
    create(
        client,
        "electrical/circuits",
        circuit_payload(other_distribution["id"], name="Garage", number="F1"),
    )

    assert circuit["name"] == "Kitchen sockets"
    assert circuit["circuit_number"] == "F1"
    assert circuit["distribution_name"] == "HV"
    assert circuit["protective_device_name"] == "Kitchen breaker"
    assert circuit["protective_device_code"]

    searched = client.get(
        "/api/v1/electrical/circuits",
        params={"search": "kitchen", "distribution_id": distribution["id"]},
    )
    filtered = client.get(
        "/api/v1/electrical/circuits",
        params={"protective_device_id": device["id"]},
    )
    paged = client.get(
        "/api/v1/electrical/circuits",
        params={"page": 2, "page_size": 2, "sort_by": "name"},
    )
    assert searched.status_code == 200
    assert searched.json()["total"] == 1
    assert filtered.json()["items"][0]["id"] == circuit["id"]
    assert paged.json()["total"] == 3
    assert paged.json()["pages"] == 2

    updated_payload = circuit_payload(
        distribution["id"],
        name="Kitchen appliances",
        number="F3",
        device_id=device["id"],
    )
    updated = client.put(
        f"/api/v1/electrical/circuits/{circuit['id']}",
        json=updated_payload,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Kitchen appliances"

    duplicate = client.post(
        "/api/v1/electrical/circuits",
        json=circuit_payload(distribution["id"], name="Duplicate", number="f3"),
    )
    wrong_device = client.post(
        "/api/v1/electrical/circuits",
        json=circuit_payload(
            distribution["id"],
            name="Wrong device",
            number="F4",
            device_id=other_device["id"],
        ),
    )
    missing_distribution = client.post(
        "/api/v1/electrical/circuits",
        json=circuit_payload(str(uuid4()), name="Missing", number="F5"),
    )
    assert duplicate.status_code == 409
    assert wrong_device.status_code == 409
    assert missing_distribution.status_code == 422

    assert client.delete(f"/api/v1/electrical/protective-devices/{device['id']}").status_code == 409
    move_device = client.put(
        f"/api/v1/electrical/protective-devices/{device['id']}",
        json={
            "asset_id": device["asset_id"],
            "distribution_id": other_distribution["id"],
            "area_id": None,
            "device_type": "mcb",
            "row_number": None,
            "start_position": None,
            "module_width": None,
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
        },
    )
    assert move_device.status_code == 409
    assert (
        client.delete(f"/api/v1/electrical/distributions/{distribution['id']}").status_code == 409
    )

    assert client.delete(f"/api/v1/electrical/circuits/{circuit['id']}").status_code == 204
    assert client.get(f"/api/v1/electrical/circuits/{circuit['id']}").status_code == 404
    historical = client.get(
        f"/api/v1/electrical/circuits/{circuit['id']}",
        params={"include_deleted": "true"},
    )
    assert historical.status_code == 200
    assert historical.json()["deleted_at"] is not None


def test_circuit_database_foreign_keys_and_active_number_uniqueness(
    circuit_client: tuple[TestClient, Engine],
) -> None:
    client, engine = circuit_client
    distribution, _, _, _ = prepare_electrical_records(client)
    with Session(engine) as session:
        session.add(ElectricalCircuit(distribution_id=uuid4(), name="Invalid"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        first = ElectricalCircuit(
            distribution_id=UUID(distribution["id"]),
            name="One",
            circuit_number="A1",
        )
        session.add(first)
        session.commit()
        session.add(
            ElectricalCircuit(
                distribution_id=UUID(distribution["id"]),
                name="Two",
                circuit_number="a1",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_circuit_asset_assignments_are_searchable_and_historic(
    circuit_client: tuple[TestClient, Engine],
) -> None:
    client, _ = circuit_client
    distribution, _, device, _ = prepare_electrical_records(client)
    circuit = create(
        client,
        "electrical/circuits",
        circuit_payload(
            distribution["id"],
            name="Kitchen supply",
            number="F10",
            device_id=device["id"],
        ),
    )
    asset_types = client.get("/api/v1/asset-types", params={"page_size": 100}).json()
    locations = client.get("/api/v1/locations", params={"page_size": 100}).json()
    assignable = create(
        client,
        "assets",
        {
            "name": "Dishwasher",
            "asset_type_id": asset_types["items"][0]["id"],
            "location_id": next(
                item["id"] for item in locations["items"] if item["name"] == "Technical room"
            ),
            "status": "active",
        },
    )

    assigned = client.post(
        f"/api/v1/electrical/circuits/{circuit['id']}/assets",
        json={"asset_id": assignable["id"]},
    )
    assert assigned.status_code == 201, assigned.text
    assert assigned.json()["asset_name"] == "Dishwasher"
    assert assigned.json()["asset_code"] == assignable["jarvis_code"]
    assert assigned.json()["asset_type_name"] == "Electrical"
    assert assigned.json()["location_name"] == "Technical room"

    duplicate = client.post(
        f"/api/v1/electrical/circuits/{circuit['id']}/assets",
        json={"asset_id": assignable["id"]},
    )
    assert duplicate.status_code == 409
    listed = client.get(f"/api/v1/electrical/circuits/{circuit['id']}/assets")
    assert listed.status_code == 200
    assert [item["asset_id"] for item in listed.json()] == [assignable["id"]]

    removed = client.delete(
        f"/api/v1/electrical/circuits/{circuit['id']}/assets/{assignable['id']}"
    )
    assert removed.status_code == 204
    assert client.get(f"/api/v1/electrical/circuits/{circuit['id']}/assets").json() == []
    history = client.get(
        f"/api/v1/electrical/circuits/{circuit['id']}/assets",
        params={"include_deleted": "true"},
    )
    assert history.status_code == 200
    assert history.json()[0]["removed_at"] is not None

    reassigned = client.post(
        f"/api/v1/electrical/circuits/{circuit['id']}/assets",
        json={"asset_id": assignable["id"]},
    )
    assert reassigned.status_code == 201
    assert reassigned.json()["link_id"] != assigned.json()["link_id"]

    assert client.delete(f"/api/v1/assets/{assignable['id']}").status_code == 204
    second_circuit = create(
        client,
        "electrical/circuits",
        circuit_payload(
            distribution["id"],
            name="Second supply",
            number="F11",
        ),
    )
    rejected_archived_asset = client.post(
        f"/api/v1/electrical/circuits/{second_circuit['id']}/assets",
        json={"asset_id": assignable["id"]},
    )
    assert rejected_archived_asset.status_code == 422

    assert client.delete(f"/api/v1/electrical/circuits/{circuit['id']}").status_code == 204
    historical_after_archive = client.get(f"/api/v1/electrical/circuits/{circuit['id']}/assets")
    assert historical_after_archive.status_code == 200
    assert historical_after_archive.json()[0]["asset_deleted_at"] is not None
    cannot_change_archived = client.delete(
        f"/api/v1/electrical/circuits/{circuit['id']}/assets/{assignable['id']}"
    )
    assert cannot_change_archived.status_code == 404
