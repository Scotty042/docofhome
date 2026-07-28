from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine, select

from app.db.session import get_session
from app.main import app
from app.models.electrical import ElectricalProtectiveDevice
from app.models.electrical_topology import ElectricalConnection


@pytest.fixture
def layout_client(tmp_path: Path) -> Generator[tuple[TestClient, Engine]]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'layout.sqlite3'}",
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


def setup_assets(
    client: TestClient,
    count: int = 4,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    root = create(
        client,
        "locations",
        {"name": "House", "location_type": "building"},
    )
    room = create(
        client,
        "locations",
        {
            "name": "Meter room",
            "location_type": "room",
            "parent_id": root["id"],
        },
    )
    asset_type = create(
        client,
        "asset-types",
        {"name": "Elektrische Verteilung"},
    )
    assets = [
        create(
            client,
            "assets",
            {
                "name": f"Electrical asset {index}",
                "asset_type_id": asset_type["id"],
                "location_id": room["id"],
                "status": "active",
            },
        )
        for index in range(count)
    ]
    return room, assets


def structured_distribution(client: TestClient, asset_id: str) -> dict[str, Any]:
    return create(
        client,
        "electrical/distributions",
        {
            "asset_id": asset_id,
            "parent_distribution_id": None,
            "distribution_type": "main",
            "layout_mode": "sections",
            "designation": "Main distribution",
            "rows": None,
            "modules_per_row": None,
            "description": None,
            "notes": None,
        },
    )


def device(client: TestClient, asset_id: str, distribution_id: str) -> dict[str, Any]:
    return create(
        client,
        "electrical/protective-devices",
        {
            "asset_id": asset_id,
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


def test_fields_areas_and_device_placement(
    layout_client: tuple[TestClient, Engine],
) -> None:
    client, _ = layout_client
    _, assets = setup_assets(client)
    distribution = structured_distribution(client, assets[0]["id"])

    left = create(
        client,
        f"electrical/distributions/{distribution['id']}/sections",
        {"name": "Left field", "position": 1, "description": "OG"},
    )
    device_area = create(
        client,
        f"electrical/distributions/{distribution['id']}/sections/{left['id']}/areas",
        {
            "name": "Upper device area",
            "area_type": "device_rows",
            "position": 1,
            "rows": 2,
            "modules_per_row": 12,
            "description": None,
        },
    )
    meter_area = create(
        client,
        f"electrical/distributions/{distribution['id']}/sections/{left['id']}/areas",
        {
            "name": "Meter field",
            "area_type": "meter",
            "position": 2,
            "rows": None,
            "modules_per_row": None,
            "description": None,
        },
    )

    first = device(client, assets[1]["id"], distribution["id"])
    placed = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/protective-devices/{first['id']}/placement",
        json={
            "area_id": device_area["id"],
            "row_number": 1,
            "start_position": 1,
            "module_width": 2,
        },
    )
    assert placed.status_code == 204

    technical_update = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/protective-devices/{first['id']}/technical",
        json={
            "asset_id": assets[1]["id"],
            "distribution_id": distribution["id"],
            "area_id": None,
            "device_type": "mcb",
            "row_number": None,
            "start_position": None,
            "module_width": None,
            "rated_current_a": 20,
            "residual_current_ma": None,
            "characteristic": "C",
            "poles": 1,
            "breaking_capacity_ka": 6,
            "rcd_type": None,
            "fuse_type": None,
            "spd_type": None,
            "description": "Updated technical data",
            "notes": None,
        },
    )
    assert technical_update.status_code == 204

    updated = client.get(f"/api/v1/electrical/protective-devices/{first['id']}")
    assert updated.status_code == 200
    assert updated.json()["rated_current_a"] == 20
    assert updated.json()["characteristic"] == "C"
    assert updated.json()["area_id"] == device_area["id"]
    assert updated.json()["row_number"] == 1
    assert updated.json()["start_position"] == 1
    assert updated.json()["module_width"] == 2

    second = device(client, assets[2]["id"], distribution["id"])
    overlap = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/protective-devices/{second['id']}/placement",
        json={
            "area_id": device_area["id"],
            "row_number": 1,
            "start_position": 2,
            "module_width": 1,
        },
    )
    wrong_area = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/protective-devices/{second['id']}/placement",
        json={
            "area_id": meter_area["id"],
            "row_number": 1,
            "start_position": 3,
            "module_width": 1,
        },
    )
    layout = client.get(f"/api/v1/electrical/distributions/{distribution['id']}/layout")

    assert overlap.status_code == 409
    assert wrong_area.status_code == 422
    assert layout.status_code == 200
    assert layout.json()[0]["areas"][0]["name"] == "Upper device area"


def test_subdistribution_supports_empty_and_filled_fields_layout(
    layout_client: tuple[TestClient, Engine],
) -> None:
    client, _ = layout_client
    _, assets = setup_assets(client, count=3)
    main = structured_distribution(client, assets[0]["id"])
    sub = create(
        client,
        "electrical/distributions",
        {
            "asset_id": assets[1]["id"],
            "parent_distribution_id": main["id"],
            "distribution_type": "sub",
            "layout_mode": "sections",
            "designation": "Subdistribution",
            "rows": None,
            "modules_per_row": None,
            "description": None,
            "notes": None,
        },
    )

    empty_layout = client.get(
        f"/api/v1/electrical/distributions/{sub['id']}/layout"
    )
    field = create(
        client,
        f"electrical/distributions/{sub['id']}/sections",
        {"name": "Subdistribution field", "position": 1, "description": None},
    )
    filled_layout = client.get(
        f"/api/v1/electrical/distributions/{sub['id']}/layout"
    )

    assert empty_layout.status_code == 200
    assert empty_layout.json() == []
    assert field["name"] == "Subdistribution field"
    assert filled_layout.status_code == 200
    assert filled_layout.json()[0]["name"] == "Subdistribution field"


def test_half_width_neutral_and_pe_rails_and_meter_placement(
    layout_client: tuple[TestClient, Engine],
) -> None:
    client, _ = layout_client
    room, assets = setup_assets(client)
    distribution = structured_distribution(client, assets[0]["id"])
    field = create(
        client,
        f"electrical/distributions/{distribution['id']}/sections",
        {"name": "Upper field", "position": 1, "description": None},
    )
    neutral = create(
        client,
        f"electrical/distributions/{distribution['id']}/sections/{field['id']}/areas",
        {
            "name": "N rail",
            "area_type": "neutral_rail",
            "position": 1,
            "rows": None,
            "modules_per_row": None,
            "width": "half",
            "side": "left",
            "description": None,
        },
    )
    protective_earth = create(
        client,
        f"electrical/distributions/{distribution['id']}/sections/{field['id']}/areas",
        {
            "name": "PE rail",
            "area_type": "protective_earth_rail",
            "position": 1,
            "rows": None,
            "modules_per_row": None,
            "width": "half",
            "side": "right",
            "description": None,
        },
    )
    meter_area = create(
        client,
        f"electrical/distributions/{distribution['id']}/sections/{field['id']}/areas",
        {
            "name": "Meter field",
            "area_type": "meter",
            "position": 3,
            "rows": None,
            "modules_per_row": None,
            "width": "full",
            "description": None,
        },
    )
    assert neutral["width"] == "half"
    assert neutral["side"] == "left"
    assert protective_earth["width"] == "half"
    assert protective_earth["side"] == "right"
    assert protective_earth["position"] == neutral["position"]

    cabinet_components = client.get(
        f"/api/v1/electrical/distributions/{distribution['id']}/cabinet-components"
    )
    assert cabinet_components.status_code == 200, cabinet_components.text
    rail_components = {
        item["component_type"]: item for item in cabinet_components.json()
    }
    assert rail_components["neutral_rail"]["area_id"] == neutral["id"]
    assert rail_components["neutral_rail"]["phases"] == ["N"]
    assert rail_components["protective_earth_rail"]["area_id"] == protective_earth["id"]
    assert rail_components["protective_earth_rail"]["phases"] == ["PE"]

    endpoints = client.get(
        "/api/v1/electrical/connection-endpoints?page=1&page_size=100"
    )
    assert endpoints.status_code == 200, endpoints.text
    endpoint_keys = {item["key"] for item in endpoints.json()["items"]}
    assert f"cabinet_component:{rail_components['neutral_rail']['id']}" in endpoint_keys
    assert (
        f"cabinet_component:{rail_components['protective_earth_rail']['id']}"
        in endpoint_keys
    )

    meter = create(
        client,
        "consumption/meters",
        {
            "name": "Grid meter",
            "meter_type": "electricity_grid",
            "unit": "kWh",
            "decimals": 1,
            "asset_id": assets[1]["id"],
            "location_id": room["id"],
            "home_assistant_power_entity_id": "sensor.grid_power",
            "home_assistant_voltage_entity_id": "sensor.grid_voltage",
        },
    )
    placement = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/meters/{meter['id']}/placement",
        json={"area_id": meter_area["id"], "position": 1},
    )
    assert placement.status_code == 200, placement.text
    assert placement.json()["meter_name"] == "Grid meter"
    assert placement.json()["asset_name"] == assets[1]["name"]
    assert placement.json()["location_path"].endswith("Meter room")

    invalid_area_change = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}/areas/{meter_area['id']}",
        json={
            "name": "No longer a meter field",
            "area_type": "connection",
            "position": 3,
            "rows": None,
            "modules_per_row": None,
            "width": "full",
            "description": None,
        },
    )
    assert invalid_area_change.status_code == 409

    archived = client.delete(f"/api/v1/consumption/meters/{meter['id']}")
    assert archived.status_code == 204
    placements = client.get(
        f"/api/v1/electrical/distributions/{distribution['id']}/meter-placements"
    )
    assert placements.status_code == 200
    assert placements.json() == []


def test_meter_asset_can_be_placed_without_consumption_meter(
    layout_client: tuple[TestClient, Engine],
) -> None:
    client, _ = layout_client
    room, assets = setup_assets(client)
    distribution = structured_distribution(client, assets[0]["id"])
    section = create(
        client,
        f"electrical/distributions/{distribution['id']}/sections",
        {"name": "Meter section", "position": 1, "description": None},
    )
    meter_area = create(
        client,
        f"electrical/distributions/{distribution['id']}/sections/{section['id']}/areas",
        {
            "name": "Meter field",
            "area_type": "meter",
            "position": 1,
            "rows": None,
            "modules_per_row": None,
            "width": "full",
            "description": None,
        },
    )
    meter_type = create(client, "asset-types", {"name": "Zähler"})
    meter_asset = create(
        client,
        "assets",
        {
            "name": "Utility meter",
            "asset_type_id": meter_type["id"],
            "location_id": room["id"],
            "status": "active",
        },
    )

    placed = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/meter-assets/{meter_asset['id']}/placement",
        json={"area_id": meter_area["id"], "position": 1},
    )
    assert placed.status_code == 200, placed.text
    assert placed.json()["source_kind"] == "asset"
    assert placed.json()["meter_id"] is None
    assert placed.json()["asset_id"] == meter_asset["id"]
    assert placed.json()["meter_name"] == "Utility meter"

    blocked_archive = client.delete(f"/api/v1/assets/{meter_asset['id']}")
    assert blocked_archive.status_code == 409
    assert client.delete(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/meter-assets/{meter_asset['id']}/placement"
    ).status_code == 204
    assert client.delete(f"/api/v1/assets/{meter_asset['id']}").status_code == 204


def test_half_width_area_rejects_duplicate_side_and_full_overlap(
    layout_client: tuple[TestClient, Engine],
) -> None:
    client, _ = layout_client
    _, assets = setup_assets(client)
    distribution = structured_distribution(client, assets[0]["id"])
    section = create(
        client,
        f"electrical/distributions/{distribution['id']}/sections",
        {"name": "Rails", "position": 1, "description": None},
    )
    endpoint = (
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/sections/{section['id']}/areas"
    )
    left = client.post(
        endpoint,
        json={
            "name": "N-Schiene",
            "area_type": "neutral_rail",
            "position": 1,
            "rows": None,
            "modules_per_row": None,
            "width": "half",
            "side": "left",
            "description": None,
        },
    )
    duplicate_left = client.post(
        endpoint,
        json={
            "name": "Weitere Schiene",
            "area_type": "technology",
            "position": 1,
            "rows": None,
            "modules_per_row": None,
            "width": "half",
            "side": "left",
            "description": None,
        },
    )
    full_overlap = client.post(
        endpoint,
        json={
            "name": "Vollbreite",
            "area_type": "cover",
            "position": 1,
            "rows": None,
            "modules_per_row": None,
            "width": "full",
            "side": None,
            "description": None,
        },
    )

    assert left.status_code == 201
    assert duplicate_left.status_code == 409
    assert "linke Hälfte" in duplicate_left.text
    assert full_overlap.status_code == 409
    assert "voller Breite" in full_overlap.text


def test_generic_din_asset_placement_uses_product_module_width(
    layout_client: tuple[TestClient, Engine],
) -> None:
    client, _ = layout_client
    room, assets = setup_assets(client)
    distribution = structured_distribution(client, assets[0]["id"])
    section = create(
        client,
        f"electrical/distributions/{distribution['id']}/sections",
        {"name": "DIN", "position": 1, "description": None},
    )
    area = create(
        client,
        f"electrical/distributions/{distribution['id']}/sections/{section['id']}/areas",
        {
            "name": "Hutschiene",
            "area_type": "device_rows",
            "position": 1,
            "rows": 1,
            "modules_per_row": 12,
            "width": "full",
            "side": None,
            "description": None,
        },
    )
    smart_meter_type = create(client, "asset-types", {"name": "Smart Meter"})
    product = create(
        client,
        "products",
        {
            "name": "Shelly 3EM",
            "manufacturer": "Shelly",
            "model_number": "3EM-63",
            "din_rail_mount": True,
            "module_width": 4,
            "asset_type_id": smart_meter_type["id"],
        },
    )
    smart_meter = create(
        client,
        "assets",
        {
            "name": "Hausmessung",
            "asset_type_id": smart_meter_type["id"],
            "product_id": product["id"],
            "location_id": room["id"],
            "status": "active",
        },
    )

    placed = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/assets/{smart_meter['id']}/placement",
        json={"area_id": area["id"], "row_number": 1, "start_position": 3},
    )
    assert placed.status_code == 200, placed.text
    assert placed.json()["module_width"] == 4
    assert placed.json()["start_position"] == 3

    listed = client.get(
        f"/api/v1/electrical/distributions/{distribution['id']}/asset-placements"
    )
    assert listed.status_code == 200
    assert listed.json()[0]["asset_id"] == smart_meter["id"]


def test_rows_layout_drag_placement_and_passive_cabinet_components(
    layout_client: tuple[TestClient, Engine],
) -> None:
    client, _ = layout_client
    _, assets = setup_assets(client)
    distribution = create(
        client,
        "electrical/distributions",
        {
            "asset_id": assets[0]["id"],
            "parent_distribution_id": None,
            "distribution_type": "main",
            "layout_mode": "rows",
            "designation": "Main distribution rows",
            "rows": 2,
            "modules_per_row": 12,
            "description": None,
            "notes": None,
        },
    )
    protective_device = device(client, assets[1]["id"], distribution["id"])

    placed = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/protective-devices/{protective_device['id']}/placement",
        json={
            "area_id": None,
            "row_number": 1,
            "start_position": 5,
            "module_width": 2,
        },
    )
    assert placed.status_code == 204, placed.text

    cabinet = create(
        client,
        f"electrical/distributions/{distribution['id']}/cabinet-components",
        {
            "name": "Phasenverteiler L1/L2/L3",
            "component_type": "phase_distribution_block",
            "area_id": None,
            "row_number": 1,
            "start_position": 1,
            "module_width": 3,
            "phases": ["L1", "L2", "L3"],
            "rated_current_a": 125,
            "max_cross_section_mm2": 35,
            "outgoing_connections": 8,
            "description": "Abgang nach dem Zähler",
            "notes": None,
        },
    )
    assert cabinet["area_id"] is None
    assert cabinet["phases"] == ["L1", "L2", "L3"]

    overlap = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/protective-devices/{protective_device['id']}/placement",
        json={
            "area_id": None,
            "row_number": 1,
            "start_position": 2,
            "module_width": 2,
        },
    )
    assert overlap.status_code == 409
    assert "Schrankkomponente" in overlap.text

    endpoints = client.get(
        "/api/v1/electrical/connection-endpoints?page=1&page_size=100"
    )
    assert endpoints.status_code == 200, endpoints.text
    endpoint_keys = {item["key"] for item in endpoints.json()["items"]}
    assert f"cabinet_component:{cabinet['id']}" in endpoint_keys

    connection = create(
        client,
        "electrical/connections",
        {
            "source_kind": "grid_connection",
            "source_id": "00000000-0000-0000-0000-000000000001",
            "target_kind": "cabinet_component",
            "target_id": cabinet["id"],
            "connection_type": "wire",
            "label": "Zählerabgang",
            "phases": ["L1", "L2", "L3"],
            "cable_type": "H07V-K",
            "cores": 3,
            "cross_section_mm2": 16,
            "length_m": 1,
            "route": "Hauptverteilung",
            "notes": None,
        },
    )
    blocked_archive = client.delete(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/cabinet-components/{cabinet['id']}"
    )
    assert blocked_archive.status_code == 409
    assert "noch verkabelt" in blocked_archive.text

    assert client.delete(
        f"/api/v1/electrical/connections/{connection['id']}"
    ).status_code == 204
    assert client.delete(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/cabinet-components/{cabinet['id']}"
    ).status_code == 204


def test_din_asset_can_use_width_from_asset_or_asset_type_without_product(
    layout_client: tuple[TestClient, Engine],
) -> None:
    client, _ = layout_client
    room, distribution_assets = setup_assets(client, count=1)
    distribution = create(
        client,
        "electrical/distributions",
        {
            "asset_id": distribution_assets[0]["id"],
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
    smart_meter_type = create(
        client,
        "asset-types",
        {
            "name": "Smart Meter",
            "description": "DIN-Zähler ohne Produktstammsatz",
            "module_width": 4,
        },
    )
    inherited = create(
        client,
        "assets",
        {
            "name": "Smart Meter aus Typbreite",
            "asset_type_id": smart_meter_type["id"],
            "location_id": room["id"],
            "status": "active",
        },
    )
    overridden = create(
        client,
        "assets",
        {
            "name": "Smart Meter mit Assetbreite",
            "asset_type_id": smart_meter_type["id"],
            "location_id": room["id"],
            "module_width": 2,
            "status": "active",
        },
    )
    assert inherited["effective_module_width"] == 4
    assert overridden["effective_module_width"] == 2

    inherited_placement = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/assets/{inherited['id']}/placement",
        json={"area_id": None, "row_number": 1, "start_position": 1},
    )
    overridden_placement = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/assets/{overridden['id']}/placement",
        json={"area_id": None, "row_number": 1, "start_position": 5},
    )
    assert inherited_placement.status_code == 200, inherited_placement.text
    assert inherited_placement.json()["module_width"] == 4
    assert overridden_placement.status_code == 200, overridden_placement.text
    assert overridden_placement.json()["module_width"] == 2

    mismatched_width = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/assets/{overridden['id']}/placement",
        json={
            "area_id": None,
            "row_number": 2,
            "start_position": 1,
            "module_width": 3,
        },
    )
    assert mismatched_width.status_code == 422
    assert "hinterlegten DIN-Breite" in mismatched_width.text

    no_width_type = create(client, "asset-types", {"name": "Ohne DIN-Breite"})
    no_width_asset = create(
        client,
        "assets",
        {
            "name": "Nicht platzierbar",
            "asset_type_id": no_width_type["id"],
            "location_id": room["id"],
            "status": "active",
        },
    )
    rejected = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/assets/{no_width_asset['id']}/placement",
        json={"area_id": None, "row_number": 2, "start_position": 1},
    )
    assert rejected.status_code == 422
    assert "DIN-Breite" in rejected.text


def test_phase_rail_contacts_every_fully_covered_din_device(
    layout_client: tuple[TestClient, Engine],
) -> None:
    client, _ = layout_client
    room, distribution_assets = setup_assets(client, count=3)
    distribution = create(
        client,
        "electrical/distributions",
        {
            "asset_id": distribution_assets[0]["id"],
            "parent_distribution_id": None,
            "distribution_type": "main",
            "layout_mode": "rows",
            "designation": "HV mit Schienen",
            "rows": 2,
            "modules_per_row": 12,
            "description": None,
            "notes": None,
        },
    )
    din_type = create(
        client,
        "asset-types",
        {"name": "DIN-Hutschienengerät", "module_width": 4},
    )
    din_asset = create(
        client,
        "assets",
        {
            "name": "Allgemeines DIN-Gerät",
            "asset_type_id": din_type["id"],
            "location_id": room["id"],
            "status": "active",
        },
    )
    placed = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/assets/{din_asset['id']}/placement",
        json={"area_id": None, "row_number": 2, "start_position": 1},
    )
    assert placed.status_code == 200, placed.text

    general_busbar = client.post(
        f"/api/v1/electrical/distributions/{distribution['id']}/cabinet-components",
        json={
            "name": "Allgemeine Sammelschiene",
            "component_type": "busbar",
            "area_id": None,
            "row_number": 2,
            "start_position": 1,
            "module_width": 12,
            "phases": ["L1", "L2", "L3"],
            "rated_current_a": 63,
            "max_cross_section_mm2": None,
            "outgoing_connections": 12,
            "linked_rcd_device_id": None,
            "start_phase": None,
            "mounting_side": None,
            "description": None,
            "notes": None,
        },
    )
    assert general_busbar.status_code == 201, general_busbar.text

    phase_rail_over_asset = client.post(
        f"/api/v1/electrical/distributions/{distribution['id']}/cabinet-components",
        json={
            "name": "Kammschiene über DIN-Gerät",
            "component_type": "phase_rail",
            "area_id": None,
            "row_number": 2,
            "start_position": 1,
            "module_width": 12,
            "phases": ["L1", "L2", "L3"],
            "rated_current_a": 63,
            "max_cross_section_mm2": None,
            "outgoing_connections": 12,
            "linked_rcd_device_id": None,
            "start_phase": "L1",
            "mounting_side": "below",
            "description": None,
            "notes": None,
        },
    )
    assert phase_rail_over_asset.status_code == 201, phase_rail_over_asset.text
    connections = client.get("/api/v1/electrical/connections").json()
    generic_contact = next(
        item for item in connections
        if item["source"]["id"] == phase_rail_over_asset.json()["id"]
        and item["target"]["kind"] == "asset"
        and item["target"]["id"] == din_asset["id"]
    )
    # A four-TE generic DIN device physically touches four rail contacts. The
    # repeated fourth L1 contact is represented once in the phase set.
    assert generic_contact["phases"] == ["L1", "L2", "L3"]
    assert generic_contact["phase_locked"] is True

    breaker = device(client, distribution_assets[1]["id"], distribution["id"])
    placed_breaker = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/protective-devices/{breaker['id']}/placement",
        json={
            "area_id": None,
            "row_number": 1,
            "start_position": 1,
            "module_width": 1,
            "assigned_rcd_id": None,
            "neutral_rail_id": None,
        },
    )
    assert placed_breaker.status_code == 204, placed_breaker.text
    phase_rail = client.post(
        f"/api/v1/electrical/distributions/{distribution['id']}/cabinet-components",
        json={
            "name": "Kammschiene",
            "component_type": "phase_rail",
            "area_id": None,
            "row_number": 1,
            "start_position": 1,
            "module_width": 12,
            "phases": ["L1", "L2", "L3"],
            "rated_current_a": 63,
            "max_cross_section_mm2": None,
            "outgoing_connections": 12,
            "linked_rcd_device_id": None,
            "start_phase": "L1",
            "mounting_side": "below",
            "description": None,
            "notes": None,
        },
    )
    assert phase_rail.status_code == 201, phase_rail.text

    later_din_asset = create(
        client,
        "assets",
        {
            "name": "Stromstoßschalter unter Kammschiene",
            "asset_type_id": din_type["id"],
            "location_id": room["id"],
            "status": "active",
        },
    )
    placed_under_rail = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/assets/{later_din_asset['id']}/placement",
        json={"area_id": None, "row_number": 1, "start_position": 2},
    )
    assert placed_under_rail.status_code == 200, placed_under_rail.text
    connections = client.get("/api/v1/electrical/connections").json()
    rail_id = phase_rail.json()["id"]
    assert any(
        item["source"]["id"] == rail_id
        and item["target"]["kind"] == "protective_device"
        and item["target"]["id"] == breaker["id"]
        for item in connections
    )
    relay_contact = next(
        item for item in connections
        if item["source"]["id"] == rail_id
        and item["target"]["kind"] == "asset"
        and item["target"]["id"] == later_din_asset["id"]
    )
    assert relay_contact["phases"] == ["L1", "L2", "L3"]
    assert relay_contact["phase_locked"] is True

    duplicate = client.post(
        f"/api/v1/electrical/distributions/{distribution['id']}/cabinet-components",
        json={
            "name": "Überlappende Kammschiene",
            "component_type": "phase_rail",
            "area_id": None,
            "row_number": 1,
            "start_position": 1,
            "module_width": 4,
            "phases": ["L1", "L2", "L3"],
            "rated_current_a": 63,
            "max_cross_section_mm2": None,
            "outgoing_connections": 4,
            "linked_rcd_device_id": None,
            "start_phase": "L1",
            "mounting_side": "above",
            "description": None,
            "notes": None,
        },
    )
    assert duplicate.status_code == 409
    assert "Phasen-/Kammschienen dürfen sich nicht überdecken" in duplicate.text

def test_four_pole_rcd_uses_three_phase_rail_contacts_and_leaves_n_free(
    layout_client: tuple[TestClient, Engine],
) -> None:
    client, _ = layout_client
    room, distribution_assets = setup_assets(client, count=1)
    distribution = create(
        client,
        "electrical/distributions",
        {
            "asset_id": distribution_assets[0]["id"],
            "parent_distribution_id": None,
            "distribution_type": "main",
            "layout_mode": "rows",
            "designation": "HV mit vierpoligem FI",
            "rows": 2,
            "modules_per_row": 12,
            "description": None,
            "notes": None,
        },
    )
    rcd_type = create(client, "asset-types", {"name": "FI/RCD", "module_width": 4})

    def rcd_asset(name: str) -> dict[str, Any]:
        return create(
            client,
            "assets",
            {
                "name": name,
                "asset_type_id": rcd_type["id"],
                "location_id": room["id"],
                "status": "active",
            },
        )

    valid_rcd_asset = rcd_asset("FI O.G.")
    valid_rcd = create(
        client,
        "electrical/protective-devices",
        {
            "asset_id": valid_rcd_asset["id"],
            "distribution_id": distribution["id"],
            "area_id": None,
            "device_type": "rcd",
            "row_number": 1,
            "start_position": 1,
            "module_width": 4,
            "rated_current_a": 40,
            "residual_current_ma": 30,
            "characteristic": None,
            "poles": 4,
            "breaking_capacity_ka": None,
            "rcd_type": "A",
            "fuse_type": None,
            "spd_type": None,
            "assigned_rcd_id": None,
            "neutral_rail_id": None,
            "description": None,
            "notes": None,
        },
    )
    rail = create(
        client,
        f"electrical/distributions/{distribution['id']}/cabinet-components",
        {
            "name": "Kammschiene mit FI",
            "component_type": "phase_rail",
            "area_id": None,
            "row_number": 1,
            "start_position": 1,
            "module_width": 12,
            "phases": ["L1", "L2", "L3"],
            "rated_current_a": 63,
            "max_cross_section_mm2": None,
            "outgoing_connections": 12,
            "linked_rcd_device_id": valid_rcd["id"],
            "visible_protective_device_ids": [valid_rcd["id"]],
            "visible_asset_ids": [],
            "start_phase": "L1",
            "mounting_side": "below",
            "description": None,
            "notes": None,
        },
    )
    assert rail["automatic_connection_count"] == 1
    connections = client.get("/api/v1/electrical/connections").json()
    contact = next(
        item for item in connections
        if item["source"]["id"] == rail["id"]
        and item["target"]["kind"] == "protective_device"
        and item["target"]["id"] == valid_rcd["id"]
    )
    assert contact["phases"] == ["L1", "L2", "L3"]
    assert "N" not in contact["phases"]
    assert "PE" not in contact["phases"]

    invalid_rcd_asset = rcd_asset("FI falsch platziert")
    invalid_rcd = create(
        client,
        "electrical/protective-devices",
        {
            "asset_id": invalid_rcd_asset["id"],
            "distribution_id": distribution["id"],
            "area_id": None,
            "device_type": "rcd",
            "row_number": 2,
            "start_position": 2,
            "module_width": 4,
            "rated_current_a": 40,
            "residual_current_ma": 30,
            "characteristic": None,
            "poles": 4,
            "breaking_capacity_ka": None,
            "rcd_type": "A",
            "fuse_type": None,
            "spd_type": None,
            "assigned_rcd_id": None,
            "neutral_rail_id": None,
            "description": None,
            "notes": None,
        },
    )
    invalid_rail = client.post(
        f"/api/v1/electrical/distributions/{distribution['id']}/cabinet-components",
        json={
            "name": "Unzulässige FI-Kammschiene",
            "component_type": "phase_rail",
            "area_id": None,
            "row_number": 2,
            "start_position": 1,
            "module_width": 12,
            "phases": ["L1", "L2", "L3"],
            "rated_current_a": 63,
            "max_cross_section_mm2": None,
            "outgoing_connections": 12,
            "linked_rcd_device_id": invalid_rcd["id"],
            "visible_protective_device_ids": [invalid_rcd["id"]],
            "visible_asset_ids": [],
            "start_phase": "L1",
            "mounting_side": "below",
            "description": None,
            "notes": None,
        },
    )
    assert invalid_rail.status_code == 409
    assert "gemeinsam mit der Phasen-/Kammschiene bei TE 1 beginnen" in invalid_rail.text


def test_protective_device_inherits_din_width_from_asset_type(
    layout_client: tuple[TestClient, Engine],
) -> None:
    client, _ = layout_client
    room, distribution_assets = setup_assets(client, count=1)
    distribution = create(
        client,
        "electrical/distributions",
        {
            "asset_id": distribution_assets[0]["id"],
            "parent_distribution_id": None,
            "distribution_type": "main",
            "layout_mode": "rows",
            "designation": "UV",
            "rows": 1,
            "modules_per_row": 12,
            "description": None,
            "notes": None,
        },
    )
    mcb_type = create(
        client,
        "asset-types",
        {"name": "Sicherungsautomat", "module_width": 1},
    )
    mcb_asset = create(
        client,
        "assets",
        {
            "name": "Küche B16",
            "asset_type_id": mcb_type["id"],
            "location_id": room["id"],
            "status": "active",
        },
    )

    available = client.get(
        "/api/v1/electrical/available-assets",
        params={"role": "protective_device", "page": 1, "page_size": 100},
    )
    assert available.status_code == 200, available.text
    option = next(item for item in available.json()["items"] if item["id"] == mcb_asset["id"])
    assert option["effective_module_width"] == 1

    created = client.post(
        "/api/v1/electrical/protective-devices",
        json={
            "asset_id": mcb_asset["id"],
            "distribution_id": distribution["id"],
            "area_id": None,
            "device_type": "mcb",
            "row_number": 1,
            "start_position": 1,
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
    assert created.status_code == 201, created.text
    assert created.json()["module_width"] == 1
    assert created.json()["asset"]["effective_module_width"] == 1


def test_phase_rail_assigns_phase_rcd_and_neutral_rail_without_manual_device_links(
    layout_client: tuple[TestClient, Engine],
) -> None:
    client, _ = layout_client
    _, assets = setup_assets(client, count=4)
    distribution = create(
        client,
        "electrical/distributions",
        {
            "asset_id": assets[0]["id"],
            "parent_distribution_id": None,
            "distribution_type": "main",
            "layout_mode": "rows",
            "designation": "HV Gruppenlogik",
            "rows": 2,
            "modules_per_row": 12,
            "description": None,
            "notes": None,
        },
    )
    rcd = create(
        client,
        "electrical/protective-devices",
        {
            "asset_id": assets[1]["id"],
            "distribution_id": distribution["id"],
            "area_id": None,
            "device_type": "rcd",
            "row_number": 1,
            "start_position": 1,
            "module_width": 4,
            "rated_current_a": 40,
            "residual_current_ma": 30,
            "characteristic": None,
            "poles": 4,
            "breaking_capacity_ka": None,
            "rcd_type": "A",
            "fuse_type": None,
            "spd_type": None,
            "description": None,
            "notes": None,
        },
    )
    mcb = device(client, assets[2]["id"], distribution["id"])
    busbar = create(
        client,
        f"electrical/distributions/{distribution['id']}/cabinet-components",
        {
            "name": "Kammschiene FI Wohnen",
            "component_type": "phase_rail",
            "area_id": None,
            "row_number": 1,
            "start_position": 5,
            "module_width": 6,
            "phases": ["L1", "L2", "L3"],
            "rated_current_a": 63,
            "max_cross_section_mm2": None,
            "outgoing_connections": 6,
            "linked_rcd_device_id": rcd["id"],
            "start_phase": "L2",
            "mounting_side": "below",
            "description": None,
            "notes": None,
        },
    )
    neutral_rail = create(
        client,
        f"electrical/distributions/{distribution['id']}/cabinet-components",
        {
            "name": "N-Schiene FI Wohnen",
            "component_type": "neutral_rail",
            "area_id": None,
            "row_number": 2,
            "start_position": 1,
            "module_width": 2,
            "phases": ["N"],
            "rated_current_a": 63,
            "max_cross_section_mm2": None,
            "outgoing_connections": 12,
            "linked_rcd_device_id": rcd["id"],
            "start_phase": None,
            "description": None,
            "notes": None,
        },
    )

    placed = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/protective-devices/{mcb['id']}/placement",
        json={
            "area_id": None,
            "row_number": 1,
            "start_position": 7,
            "module_width": 1,
            "assigned_rcd_id": None,
            "neutral_rail_id": None,
        },
    )
    assert placed.status_code == 204, placed.text

    detail = client.get(
        f"/api/v1/electrical/distributions/{distribution['id']}"
    )
    assert detail.status_code == 200, detail.text
    stored = next(item for item in detail.json()["protective_devices"] if item["id"] == mcb["id"])
    assert stored["assigned_rcd_id"] is None
    assert stored["neutral_rail_id"] is None
    assert stored["effective_rcd_id"] == rcd["id"]
    assert stored["effective_neutral_rail_id"] == neutral_rail["id"]
    assert stored["busbar_component_id"] == busbar["id"]
    assert stored["calculated_phases"] == ["L1"]
    assert stored["group_warnings"] == []


def test_phase_rail_creates_and_updates_physical_connections_without_rcd(
    layout_client: tuple[TestClient, Engine],
) -> None:
    client, engine = layout_client
    room, distribution_assets = setup_assets(client, count=1)
    distribution = create(
        client,
        "electrical/distributions",
        {
            "asset_id": distribution_assets[0]["id"],
            "parent_distribution_id": None,
            "distribution_type": "main",
            "layout_mode": "rows",
            "designation": "HV auto wiring",
            "rows": 1,
            "modules_per_row": 12,
            "description": None,
            "notes": None,
        },
    )
    breaker_type = create(
        client,
        "asset-types",
        {"name": "Sicherungsautomat", "module_width": 1},
    )

    def breaker_asset(name: str) -> dict[str, Any]:
        return create(
            client,
            "assets",
            {
                "name": name,
                "asset_type_id": breaker_type["id"],
                "location_id": room["id"],
                "status": "active",
            },
        )

    def create_breaker(name: str, position: int) -> dict[str, Any]:
        asset = breaker_asset(name)
        return create(
            client,
            "electrical/protective-devices",
            {
                "asset_id": asset["id"],
                "distribution_id": distribution["id"],
                "area_id": None,
                "device_type": "mcb",
                "row_number": 1,
                "start_position": position,
                "module_width": 1,
                "rated_current_a": 16,
                "residual_current_ma": None,
                "characteristic": "B",
                "poles": 1,
                "breaking_capacity_ka": 6,
                "rcd_type": None,
                "fuse_type": None,
                "spd_type": None,
                "assigned_rcd_id": None,
                "neutral_rail_id": None,
                "description": None,
                "notes": None,
            },
        )

    first = create_breaker("Keller", 1)
    rail = create(
        client,
        f"electrical/distributions/{distribution['id']}/cabinet-components",
        {
            "name": "Kammschiene",
            "component_type": "phase_rail",
            "area_id": None,
            "row_number": 1,
            "start_position": 1,
            "module_width": 6,
            "phases": ["L1", "L2", "L3"],
            "rated_current_a": 63,
            "max_cross_section_mm2": None,
            "outgoing_connections": 6,
            "linked_rcd_device_id": None,
            "start_phase": "L1",
            "mounting_side": "below",
            "description": None,
            "notes": None,
        },
    )
    assert rail["linked_rcd_device_id"] is None
    assert rail["automatic_connection_count"] == 1

    connections = client.get("/api/v1/electrical/connections").json()
    first_link = next(
        item for item in connections
        if item["source"]["id"] == rail["id"] and item["target"]["id"] == first["id"]
    )
    assert first_link["connection_type"] == "busbar"
    assert first_link["phases"] == ["L1"]
    assert first_link["effective_phases"] == ["L1"]
    assert first_link["phase_locked"] is True
    assert first_link["locked_line_phases"] == ["L1"]

    cannot_delete = client.delete(
        f"/api/v1/electrical/connections/{first_link['id']}"
    )
    assert cannot_delete.status_code == 409
    assert "automatisch" in cannot_delete.text

    second = create_breaker("Waschmaschine", 2)
    connections = client.get("/api/v1/electrical/connections").json()
    second_link = next(
        item for item in connections
        if item["source"]["id"] == rail["id"] and item["target"]["id"] == second["id"]
    )
    assert second_link["phases"] == ["L2"]
    assert second_link["locked_line_phases"] == ["L2"]

    moved = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/protective-devices/{first['id']}/placement",
        json={
            "area_id": None,
            "row_number": 1,
            "start_position": 3,
            "module_width": 1,
            "assigned_rcd_id": None,
            "neutral_rail_id": None,
        },
    )
    assert moved.status_code == 204, moved.text
    connections = client.get("/api/v1/electrical/connections").json()
    moved_link = next(item for item in connections if item["id"] == first_link["id"])
    assert moved_link["phases"] == ["L3"]
    assert moved_link["effective_phases"] == ["L3"]
    assert moved_link["locked_line_phases"] == ["L3"]

    # Topology reads reconcile missing derived contacts. This protects existing
    # installations where a previous migration or interrupted transaction left
    # the phase rail visible but omitted its automatic connection.
    with Session(engine) as session:
        stale = session.get(ElectricalConnection, UUID(first_link["id"]))
        assert stale is not None
        stale.deleted_at = datetime.now(UTC)
        session.add(stale)
        session.commit()
    topology = client.get("/api/v1/electrical/topology")
    assert topology.status_code == 200, topology.text
    repaired_link = next(
        item for item in topology.json()["connections"]
        if item["source"]["id"] == rail["id"]
        and item["target"]["id"] == first["id"]
    )
    assert repaired_link["effective_phases"] == ["L3"]
    assert repaired_link["phase_locked"] is True

    # Archiving the physical rail keeps the breakers placed but atomically
    # deactivates both the upstream feed and all derived rail contacts.
    archived = client.delete(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/cabinet-components/{rail['id']}"
    )
    assert archived.status_code == 204, archived.text
    remaining_connections = client.get("/api/v1/electrical/connections").json()
    assert all(
        item["source"]["id"] != rail["id"] and item["target"]["id"] != rail["id"]
        for item in remaining_connections
    )
    detail = client.get(f"/api/v1/electrical/distributions/{distribution['id']}")
    assert detail.status_code == 200, detail.text
    placed_ids = {item["id"] for item in detail.json()["protective_devices"]}
    assert {first["id"], second["id"]}.issubset(placed_ids)


def test_structured_phase_rail_replaces_manual_feeds_and_contacts_all_din_devices(
    layout_client: tuple[TestClient, Engine],
) -> None:
    """Match the real mixed OG row: breakers plus a normal impulse relay."""
    client, engine = layout_client
    room, distribution_assets = setup_assets(client, count=1)
    distribution = structured_distribution(client, distribution_assets[0]["id"])
    section = create(
        client,
        f"electrical/distributions/{distribution['id']}/sections",
        {"name": "O.G.", "position": 1, "description": None},
    )
    area = create(
        client,
        f"electrical/distributions/{distribution['id']}/sections/{section['id']}/areas",
        {
            "name": "Sicherungen",
            "area_type": "device_rows",
            "position": 1,
            "rows": 1,
            "modules_per_row": 12,
            "width": "full",
            "side": None,
            "description": None,
        },
    )
    breaker_type = create(
        client, "asset-types", {"name": "Sicherungsautomat", "module_width": 1}
    )

    breakers: list[dict[str, Any]] = []
    for position, name in enumerate(("Keller", "Waschmaschine", "Trockner"), start=1):
        asset = create(
            client,
            "assets",
            {
                "name": name,
                "asset_type_id": breaker_type["id"],
                "location_id": room["id"],
                "status": "active",
            },
        )
        breakers.append(create(
            client,
            "electrical/protective-devices",
            {
                "asset_id": asset["id"],
                "distribution_id": distribution["id"],
                "area_id": area["id"],
                "device_type": "mcb",
                "row_number": 1,
                "start_position": position,
                "module_width": 1,
                "rated_current_a": 16,
                "residual_current_ma": None,
                "characteristic": "B",
                "poles": 1,
                "breaking_capacity_ka": 6,
                "rcd_type": None,
                "fuse_type": None,
                "spd_type": None,
                "assigned_rcd_id": None,
                "neutral_rail_id": None,
                "description": None,
                "notes": None,
            },
        ))

    # Simulate a real upgraded database: the cabinet view still knows the
    # effective 1-TE width through the asset type, while the legacy placement
    # column itself is NULL. Automatic rail wiring must use the same inherited
    # width as the UI and may not silently drop these visible breakers.
    with Session(engine) as session:
        for breaker in breakers:
            stored = session.get(ElectricalProtectiveDevice, UUID(breaker["id"]))
            assert stored is not None
            stored.module_width = None
            session.add(stored)
        session.commit()

    relay_type = create(
        client, "asset-types", {"name": "Stromstoßschalter", "module_width": 1}
    )
    relay = create(
        client,
        "assets",
        {
            "name": "Stromstoßschalter",
            "asset_type_id": relay_type["id"],
            "location_id": room["id"],
            "status": "active",
        },
    )
    relay_placement = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/assets/{relay['id']}/placement",
        json={"area_id": area["id"], "row_number": 1, "start_position": 4},
    )
    assert relay_placement.status_code == 200, relay_placement.text

    old_block = create(
        client,
        f"electrical/distributions/{distribution['id']}/cabinet-components",
        {
            "name": "Phasenverteilerblock L1/L2/L3",
            "component_type": "phase_distribution_block",
            "area_id": area["id"],
            "row_number": 1,
            "start_position": 10,
            "module_width": 3,
            "phases": ["L1", "L2", "L3"],
            "rated_current_a": 125,
            "max_cross_section_mm2": 35,
            "outgoing_connections": 8,
            "linked_rcd_device_id": None,
            "start_phase": None,
            "mounting_side": None,
            "description": None,
            "notes": None,
        },
    )
    manual = create(
        client,
        "electrical/connections",
        {
            "source_kind": "cabinet_component",
            "source_id": old_block["id"],
            "target_kind": "protective_device",
            "target_id": breakers[1]["id"],
            "connection_type": "wire",
            "label": None,
            "phases": ["L1"],
            "cable_type": None,
            "cores": None,
            "cross_section_mm2": None,
            "length_m": None,
            "route": None,
            "notes": None,
        },
    )

    rail = create(
        client,
        f"electrical/distributions/{distribution['id']}/cabinet-components",
        {
            "name": "Kammschiene 1 OG",
            "component_type": "phase_rail",
            "area_id": area["id"],
            "row_number": 1,
            "start_position": 1,
            "module_width": 9,
            "phases": ["L1", "L2", "L3"],
            "rated_current_a": 63,
            "max_cross_section_mm2": None,
            "outgoing_connections": 9,
            "linked_rcd_device_id": None,
            "visible_protective_device_ids": [item["id"] for item in breakers],
            "start_phase": "L1",
            "mounting_side": "below",
            "description": None,
            "notes": None,
        },
    )

    assert rail["automatic_connection_count"] == 4
    connections = client.get("/api/v1/electrical/connections").json()
    automatic = {
        item["target"]["id"]: item
        for item in connections
        if item["source"]["id"] == rail["id"]
        and item["target"]["kind"] == "protective_device"
    }
    assert set(automatic) == {item["id"] for item in breakers}
    assert automatic[breakers[0]["id"]]["phases"] == ["L1"]
    assert automatic[breakers[1]["id"]]["phases"] == ["L2"]
    assert automatic[breakers[2]["id"]]["phases"] == ["L3"]
    assert all(item["phase_locked"] for item in automatic.values())
    relay_contact = next(
        item for item in connections
        if item["source"]["id"] == rail["id"]
        and item["target"]["kind"] == "asset"
        and item["target"]["id"] == relay["id"]
    )
    assert relay_contact["phases"] == ["L1"]
    assert relay_contact["phase_locked"] is True
    assert all(item["id"] != manual["id"] for item in connections)

    endpoint_page = client.get(
        "/api/v1/electrical/connection-endpoints",
        params={"page": 1, "page_size": 200},
    )
    assert endpoint_page.status_code == 200, endpoint_page.text
    relay_endpoint = next(
        item for item in endpoint_page.json()["items"]
        if item["kind"] == "asset" and item["id"] == relay["id"]
    )
    assert relay_endpoint["effective_phases"] == ["L1"]

    manual_relay_feed = client.post(
        "/api/v1/electrical/connections",
        json={
            "source_kind": "cabinet_component",
            "source_id": old_block["id"],
            "target_kind": "asset",
            "target_id": relay["id"],
            "connection_type": "wire",
            "label": None,
            "phases": ["L1"],
            "cable_type": None,
            "cores": None,
            "cross_section_mm2": None,
            "length_m": None,
            "route": None,
            "notes": None,
        },
    )
    assert manual_relay_feed.status_code == 422
    assert "bereits physisch durch eine Phasen-/Kammschiene" in manual_relay_feed.text

    consumer_type = create(client, "asset-types", {"name": "Verbraucher"})
    consumer = create(
        client,
        "assets",
        {
            "name": "Tasterkreis",
            "asset_type_id": consumer_type["id"],
            "location_id": room["id"],
            "status": "active",
        },
    )
    relay_output = create(
        client,
        "electrical/connections",
        {
            "source_kind": "asset",
            "source_id": relay["id"],
            "target_kind": "asset",
            "target_id": consumer["id"],
            "connection_type": "wire",
            "label": None,
            "phases": ["L3"],
            "cable_type": None,
            "cores": None,
            "cross_section_mm2": None,
            "length_m": None,
            "route": None,
            "notes": None,
        },
    )
    assert relay_output["phases"] == ["L1"]
    assert relay_output["effective_phases"] == ["L1"]

    # The dedicated post-save endpoint must rebuild contacts independently of
    # the create transaction. This is the exact browser runtime path used by
    # 1.6.3.4 and protects upgraded installations where the initial ORM lookup
    # returned an empty device list.
    with Session(engine) as session:
        stored = session.exec(
            select(ElectricalConnection).where(
                ElectricalConnection.source_kind == "cabinet_component",
                ElectricalConnection.source_id == UUID(rail["id"]),
                ElectricalConnection.target_kind == "protective_device",
            )
        ).all()
        now = datetime.now(UTC)
        for item in stored:
            item.deleted_at = now
            item.updated_at = now
            session.add(item)
        session.commit()

    synchronized = client.post(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/cabinet-components/{rail['id']}/synchronize",
        json={
            "protective_device_ids": [item["id"] for item in breakers],
            "asset_ids": [relay["id"]],
        },
    )
    assert synchronized.status_code == 200, synchronized.text
    assert synchronized.json()["automatic_connection_count"] == 4


def test_phase_rail_can_link_to_rcd_din_asset(layout_client: tuple[TestClient, Engine]) -> None:
    client, _ = layout_client
    root = create(client, "locations", {"name": "House FI", "location_type": "building"})
    room = create(
        client,
        "locations",
        {"name": "Cabinet FI", "location_type": "room", "parent_id": root["id"]},
    )
    distribution_type = create(client, "asset-types", {"name": "Verteilung FI"})
    rcd_type = create(
        client,
        "asset-types",
        {"name": "FI-Schutzschalter", "module_width": 4},
    )
    distribution_asset = create(
        client,
        "assets",
        {
            "name": "HV FI",
            "asset_type_id": distribution_type["id"],
            "location_id": room["id"],
            "status": "active",
        },
    )
    rcd_asset = create(
        client,
        "assets",
        {
            "name": "FI Zählerraum",
            "asset_type_id": rcd_type["id"],
            "location_id": room["id"],
            "status": "active",
        },
    )
    distribution = create(
        client,
        "electrical/distributions",
        {
            "asset_id": distribution_asset["id"],
            "parent_distribution_id": None,
            "distribution_type": "main",
            "layout_mode": "rows",
            "designation": "HV FI",
            "rows": 2,
            "modules_per_row": 12,
            "description": None,
            "notes": None,
        },
    )
    placement = client.put(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/assets/{rcd_asset['id']}/placement",
        json={"area_id": None, "row_number": 2, "start_position": 1},
    )
    assert placement.status_code == 200, placement.text
    assert placement.json()["is_rcd"] is True

    rail = client.post(
        f"/api/v1/electrical/distributions/{distribution['id']}/cabinet-components",
        json={
            "name": "Kammschiene FI-Gruppe",
            "component_type": "phase_rail",
            "area_id": None,
            "row_number": 1,
            "start_position": 1,
            "module_width": 12,
            "phases": ["L1", "L2", "L3"],
            "rated_current_a": 63,
            "max_cross_section_mm2": None,
            "outgoing_connections": 12,
            "linked_rcd_device_id": None,
            "linked_rcd_asset_id": rcd_asset["id"],
            "start_phase": "L1",
            "mounting_side": "below",
            "description": None,
            "notes": None,
        },
    )
    assert rail.status_code == 201, rail.text
    body = rail.json()
    assert body["linked_rcd_device_id"] is None
    assert body["linked_rcd_asset_id"] == rcd_asset["id"]
    assert body["linked_rcd_name"] == "FI Zählerraum"

    unplace = client.delete(
        f"/api/v1/electrical/distributions/{distribution['id']}"
        f"/assets/{rcd_asset['id']}/placement"
    )
    assert unplace.status_code == 409, unplace.text
    assert "Zuordnung" in unplace.text
