from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import get_session
from app.main import app


@pytest.fixture
def release_client(tmp_path: Path) -> Generator[TestClient]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'release-1.6.sqlite3'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    def override_session() -> Generator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def create(client: TestClient, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post(f"/api/v1/{endpoint}", json=payload)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def test_breaker_defaults_are_inherited_and_can_be_overridden(
    release_client: TestClient,
) -> None:
    asset_type = create(
        release_client,
        "asset-types",
        {
            "name": "Sicherungsautomat",
            "module_width": 1,
            "breaker_characteristic": "B",
            "rated_current_a": 16,
        },
    )
    inherited = create(
        release_client,
        "assets",
        {
            "name": "Licht EG",
            "asset_type_id": asset_type["id"],
            "status": "active",
        },
    )
    assert inherited["breaker_characteristic"] is None
    assert inherited["rated_current_a"] is None
    assert inherited["effective_breaker_characteristic"] == "B"
    assert inherited["effective_rated_current_a"] == 16

    response = release_client.put(
        f"/api/v1/assets/{inherited['id']}",
        json={
            "name": "Licht EG",
            "asset_type_id": asset_type["id"],
            "breaker_characteristic": "C",
            "rated_current_a": 13,
            "status": "active",
        },
    )
    assert response.status_code == 200, response.text
    overridden = response.json()
    assert overridden["effective_breaker_characteristic"] == "C"
    assert overridden["effective_rated_current_a"] == 13


def test_impulse_switch_defaults_are_available_on_type_and_asset(
    release_client: TestClient,
) -> None:
    asset_type = create(
        release_client,
        "asset-types",
        {
            "name": "Stromstoßschalter",
            "module_width": 1,
            "rated_current_a": 16,
            "coil_voltage_v": 230,
            "coil_voltage_type": "AC",
            "contact_count": 1,
            "contact_type": "normally_open",
        },
    )
    impulse_switch = create(
        release_client,
        "assets",
        {
            "name": "Treppenhauslicht",
            "asset_type_id": asset_type["id"],
            "status": "active",
        },
    )

    assert impulse_switch["effective_rated_current_a"] == 16
    assert impulse_switch["effective_coil_voltage_v"] == 230
    assert impulse_switch["effective_coil_voltage_type"] == "AC"
    assert impulse_switch["effective_contact_count"] == 1
    assert impulse_switch["effective_contact_type"] == "normally_open"


def test_smart_meter_measurement_point_links_connection_and_home_assistant_entities(
    release_client: TestClient,
) -> None:
    smart_type = create(
        release_client,
        "asset-types",
        {"name": "Smart Meter", "module_width": 4},
    )
    generic_type = create(
        release_client,
        "asset-types",
        {"name": "Elektrisches Gerät"},
    )

    def asset(name: str, type_id: str) -> dict[str, Any]:
        return create(
            release_client,
            "assets",
            {"name": name, "asset_type_id": type_id, "status": "active"},
        )

    smart_meter = asset("Shelly Pro 3EM", smart_type["id"])
    meter = asset("Netzbetreiberzähler", generic_type["id"])
    main_switch = asset("Hauptschalter", generic_type["id"])

    endpoint_response = release_client.get(
        "/api/v1/electrical/connection-endpoints",
        params={"page_size": 100},
    )
    assert endpoint_response.status_code == 200, endpoint_response.text
    endpoints = endpoint_response.json()["items"]

    def endpoint(asset_id: str) -> dict[str, Any]:
        return next(
            item
            for item in endpoints
            if item["kind"] == "asset" and item["id"] == asset_id
        )

    source = endpoint(meter["id"])
    target = endpoint(main_switch["id"])
    connection = create(
        release_client,
        "electrical/connections",
        {
            "source_kind": source["kind"],
            "source_id": source["id"],
            "target_kind": target["kind"],
            "target_id": target["id"],
            "connection_type": "cable",
            "label": "Hausanschluss L1",
            "phases": ["L1"],
            "cable_type": "NYM-J",
            "cores": 1,
            "cross_section_mm2": 16,
            "length_m": 1.5,
            "route": None,
            "notes": None,
        },
    )

    point = create(
        release_client,
        f"electrical/smart-meters/{smart_meter['id']}/measurement-points",
        {
            "connection_id": connection["id"],
            "channel_name": "CT1",
            "name": "Hausanschluss L1",
            "phase": "L1",
            "direction": "source_to_target",
            "inverted": False,
            "transformer_nominal_current_a": 120,
            "transformer_ratio": "120 A / 40 mA",
            "notes": "Klemme zeigt in Richtung Haus",
            "entities": [
                {"entity_id": "sensor.smart_meter_l1_power", "role": "power"},
                {"entity_id": "sensor.smart_meter_l1_current", "role": "current"},
            ],
        },
    )
    assert point["connection_source_name"] == "Netzbetreiberzähler"
    assert point["connection_target_name"] == "Hauptschalter"
    assert {item["role"] for item in point["entities"]} == {"power", "current"}

    duplicate = release_client.post(
        f"/api/v1/electrical/smart-meters/{smart_meter['id']}/measurement-points",
        json={
            "connection_id": connection["id"],
            "channel_name": "ct1",
            "name": "Doppelter Kanal",
            "entities": [],
        },
    )
    assert duplicate.status_code == 409

    topology = release_client.get("/api/v1/electrical/topology")
    assert topology.status_code == 200, topology.text
    assert topology.json()["measurement_points"][0]["id"] == point["id"]

    blocked_connection = release_client.delete(
        f"/api/v1/electrical/connections/{connection['id']}"
    )
    blocked_asset = release_client.delete(f"/api/v1/assets/{smart_meter['id']}")
    assert blocked_connection.status_code == 409
    assert blocked_asset.status_code == 409

    deleted = release_client.delete(
        f"/api/v1/electrical/smart-meters/{smart_meter['id']}/measurement-points/{point['id']}"
    )
    assert deleted.status_code == 204
    assert release_client.delete(
        f"/api/v1/electrical/connections/{connection['id']}"
    ).status_code == 204


def test_measurement_points_require_a_smart_meter_asset(release_client: TestClient) -> None:
    asset_type = create(release_client, "asset-types", {"name": "Sensor"})
    sensor = create(
        release_client,
        "assets",
        {"name": "Stromsensor", "asset_type_id": asset_type["id"], "status": "active"},
    )
    response = release_client.get(
        f"/api/v1/electrical/smart-meters/{sensor['id']}/measurement-points"
    )
    assert response.status_code == 422
