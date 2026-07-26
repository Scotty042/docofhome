from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import get_session
from app.main import app


@pytest.fixture
def topology_client(tmp_path: Path) -> Generator[TestClient]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'topology.sqlite3'}",
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
    result: dict[str, Any] = response.json()
    return result


def connection_payload(
    source: dict[str, Any],
    target: dict[str, Any],
    *,
    phases: list[str],
    connection_type: str = "wire",
) -> dict[str, Any]:
    return {
        "source_kind": source["kind"],
        "source_id": source["id"],
        "target_kind": target["kind"],
        "target_id": target["id"],
        "connection_type": connection_type,
        "label": None,
        "phases": phases,
        "cable_type": "NYM-J" if connection_type == "cable" else None,
        "cores": 5 if connection_type == "cable" else None,
        "cross_section_mm2": 10 if connection_type == "cable" else None,
        "length_m": 12.5 if connection_type == "cable" else None,
        "route": "Utility room" if connection_type == "cable" else None,
        "notes": None,
    }


def prepare_topology(client: TestClient) -> dict[str, dict[str, Any]]:
    building = create(
        client,
        "locations",
        {"name": "Home", "location_type": "building"},
    )
    room = create(
        client,
        "locations",
        {
            "name": "Utility room",
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

    grid = asset("Grid connection")
    meter = asset("Electricity meter")
    pv = asset("PV inverter")
    load = asset("Dishwasher")
    distribution_asset = asset("Main distribution asset")
    rcd_asset = asset("RCD 1")
    mcb_one_asset = asset("Breaker F1")
    mcb_two_asset = asset("Breaker F2")
    distribution = create(
        client,
        "electrical/distributions",
        {
            "asset_id": distribution_asset["id"],
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

    def device(asset_record: dict[str, Any], device_type: str) -> dict[str, Any]:
        return create(
            client,
            "electrical/protective-devices",
            {
                "asset_id": asset_record["id"],
                "distribution_id": distribution["id"],
                "area_id": None,
                "device_type": device_type,
                "row_number": None,
                "start_position": None,
                "module_width": None,
                "rated_current_a": None,
                "residual_current_ma": 30 if device_type == "rcd" else None,
                "characteristic": None,
                "poles": None,
                "breaking_capacity_ka": None,
                "rcd_type": None,
                "fuse_type": None,
                "spd_type": None,
                "description": None,
                "notes": None,
            },
        )

    rcd = device(rcd_asset, "rcd")
    mcb_one = device(mcb_one_asset, "mcb")
    mcb_two = device(mcb_two_asset, "mcb")
    circuit = create(
        client,
        "electrical/circuits",
        {
            "distribution_id": distribution["id"],
            "protective_device_id": mcb_one["id"],
            "name": "Kitchen sockets",
            "circuit_number": "F1",
            "description": None,
            "notes": None,
        },
    )
    endpoints_response = client.get(
        "/api/v1/electrical/connection-endpoints",
        params={"page_size": 100},
    )
    assert endpoints_response.status_code == 200
    endpoints = endpoints_response.json()["items"]

    def endpoint(kind: str, endpoint_id: str) -> dict[str, Any]:
        return next(
            item for item in endpoints if item["kind"] == kind and item["id"] == endpoint_id
        )

    assert not any(
        item["kind"] == "asset" and item["id"] == distribution_asset["id"] for item in endpoints
    )
    return {
        "grid": endpoint("asset", grid["id"]),
        "meter": endpoint("asset", meter["id"]),
        "pv": endpoint("asset", pv["id"]),
        "load": endpoint("asset", load["id"]),
        "distribution": endpoint("distribution", distribution["id"]),
        "rcd": endpoint("protective_device", rcd["id"]),
        "mcb_one": endpoint("protective_device", mcb_one["id"]),
        "mcb_two": endpoint("protective_device", mcb_two["id"]),
        "circuit": endpoint("circuit", circuit["id"]),
    }


def test_supply_topology_paths_phases_cable_and_rcd_counts(
    topology_client: TestClient,
) -> None:
    client = topology_client
    endpoint = prepare_topology(client)
    chain = (
        ("grid", "meter", ["L1", "L2", "L3", "N", "PE"], "cable"),
        ("meter", "distribution", ["L1", "L2", "L3", "N", "PE"], "internal"),
        ("distribution", "rcd", ["L1", "L2", "L3", "N"], "busbar"),
        ("rcd", "mcb_one", ["L2", "N"], "busbar"),
        ("rcd", "mcb_two", ["L3", "N"], "busbar"),
        ("mcb_one", "circuit", ["L2", "N", "PE"], "wire"),
        ("circuit", "load", ["L2", "N", "PE"], "cable"),
    )
    created: list[dict[str, Any]] = []
    for source, target, phases, connection_type in chain:
        created.append(
            create(
                client,
                "electrical/connections",
                connection_payload(
                    endpoint[source],
                    endpoint[target],
                    phases=phases,
                    connection_type=connection_type,
                ),
            )
        )

    assert created[0]["cable_type"] == "NYM-J"
    assert created[0]["cross_section_mm2"] == 10
    topology = client.get("/api/v1/electrical/topology")
    assert topology.status_code == 200, topology.text
    body = topology.json()
    pv_supply = create(
        client,
        "electrical/connections",
        connection_payload(endpoint["pv"], endpoint["distribution"], phases=["L1", "L2", "L3"]),
    )
    topology = client.get("/api/v1/electrical/topology")
    assert topology.status_code == 200, topology.text
    body = topology.json()
    assert len(body["connections"]) == 8
    nodes = {item["endpoint"]["key"]: item for item in body["nodes"]}
    rcd = nodes[endpoint["rcd"]["key"]]
    mcb_one = nodes[endpoint["mcb_one"]["key"]]
    load = nodes[endpoint["load"]["key"]]
    assert rcd["downstream_protective_device_count"] == 2
    assert rcd["downstream_circuit_count"] == 1
    assert rcd["downstream_asset_count"] == 1
    assert mcb_one["incoming_phases"] == ["L2", "N"]
    assert load["source_names"] == ["Grid connection", "PV inverter"]

    duplicate_supply = client.post(
        "/api/v1/electrical/connections",
        json=connection_payload(endpoint["pv"], endpoint["distribution"], phases=["L1"]),
    )
    cycle = client.post(
        "/api/v1/electrical/connections",
        json=connection_payload(endpoint["load"], endpoint["grid"], phases=["L2"]),
    )
    assert duplicate_supply.status_code == 409
    assert cycle.status_code == 409

    updated_payload = connection_payload(
        endpoint["rcd"],
        endpoint["mcb_two"],
        phases=["L1", "N"],
    )
    updated = client.put(
        f"/api/v1/electrical/connections/{created[4]['id']}",
        json=updated_payload,
    )
    assert updated.status_code == 200
    assert updated.json()["phases"] == ["L1", "N"]
    assert client.delete(f"/api/v1/electrical/connections/{created[4]['id']}").status_code == 204
    assert len(client.get("/api/v1/electrical/connections").json()) == 7
    assert pv_supply["target"]["id"] == endpoint["distribution"]["id"]


def test_archived_endpoints_cannot_receive_new_connections(
    topology_client: TestClient,
) -> None:
    client = topology_client
    endpoint = prepare_topology(client)
    assert client.delete(f"/api/v1/assets/{endpoint['load']['id']}").status_code == 204
    response = client.post(
        "/api/v1/electrical/connections",
        json=connection_payload(endpoint["circuit"], endpoint["load"], phases=["L1"]),
    )
    assert response.status_code == 422


def test_grid_connection_is_a_real_source_only_endpoint(
    topology_client: TestClient,
) -> None:
    client = topology_client
    endpoints = prepare_topology(client)
    response = client.get(
        "/api/v1/electrical/connection-endpoints",
        params={"page_size": 100},
    )
    assert response.status_code == 200
    grid_sources = [
        item
        for item in response.json()["items"]
        if item["kind"] == "grid_connection"
    ]
    assert len(grid_sources) == 1
    grid_source = grid_sources[0]
    assert grid_source["name"] == "Netzanschluss"

    created = client.post(
        "/api/v1/electrical/connections",
        json=connection_payload(
            grid_source,
            endpoints["meter"],
            phases=["L1", "L2", "L3", "N", "PE"],
            connection_type="cable",
        ),
    )
    assert created.status_code == 201, created.text
    assert created.json()["source"]["kind"] == "grid_connection"

    invalid_target = client.post(
        "/api/v1/electrical/connections",
        json=connection_payload(
            endpoints["meter"],
            grid_source,
            phases=["L1"],
        ),
    )
    assert invalid_target.status_code == 422


def test_cabinet_component_accepts_multiple_feeds_and_preserves_phases(
    topology_client: TestClient,
) -> None:
    client = topology_client
    endpoints = prepare_topology(client)
    component = create(
        client,
        f"electrical/distributions/{endpoints['distribution']['id']}/cabinet-components",
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
            "description": None,
            "notes": None,
        },
    )
    endpoint_response = client.get(
        "/api/v1/electrical/connection-endpoints",
        params={"page_size": 100},
    )
    assert endpoint_response.status_code == 200
    component_endpoint = next(
        item
        for item in endpoint_response.json()["items"]
        if item["kind"] == "cabinet_component" and item["id"] == component["id"]
    )

    grid_feed = create(
        client,
        "electrical/connections",
        connection_payload(
            endpoints["meter"],
            component_endpoint,
            phases=["L1", "L2", "L3"],
        ),
    )
    pv_feed = create(
        client,
        "electrical/connections",
        connection_payload(
            endpoints["pv"],
            component_endpoint,
            phases=["L1", "L2", "L3"],
        ),
    )
    outgoing = create(
        client,
        "electrical/connections",
        connection_payload(
            component_endpoint,
            endpoints["rcd"],
            phases=["L1", "L2", "L3"],
            connection_type="busbar",
        ),
    )

    topology = client.get("/api/v1/electrical/topology")
    assert topology.status_code == 200, topology.text
    node = next(
        item
        for item in topology.json()["nodes"]
        if item["endpoint"]["key"] == component_endpoint["key"]
    )
    assert node["incoming_phases"] == ["L1", "L2", "L3"]
    assert node["source_names"] == ["Electricity meter", "PV inverter"]

    # One of two full three-phase feeds may be removed because the remaining feed
    # still supplies every conductor used by the outputs.
    assert client.delete(
        f"/api/v1/electrical/connections/{pv_feed['id']}"
    ).status_code == 204

    # Reducing the last feed while L2/L3 are still used downstream is rejected.
    invalid_feed_change = client.put(
        f"/api/v1/electrical/connections/{grid_feed['id']}",
        json=connection_payload(
            endpoints["meter"],
            component_endpoint,
            phases=["L1"],
        ),
    )
    assert invalid_feed_change.status_code == 422
    assert "L2" in invalid_feed_change.text and "L3" in invalid_feed_change.text

    reduced_output = client.put(
        f"/api/v1/electrical/connections/{outgoing['id']}",
        json=connection_payload(
            component_endpoint,
            endpoints["rcd"],
            phases=["L1"],
            connection_type="busbar",
        ),
    )
    assert reduced_output.status_code == 200
    reduced_feed = client.put(
        f"/api/v1/electrical/connections/{grid_feed['id']}",
        json=connection_payload(
            endpoints["meter"],
            component_endpoint,
            phases=["L1"],
        ),
    )
    assert reduced_feed.status_code == 200

    # The phase name is end-to-end semantics. An L2 output cannot be created if
    # only L1 enters the block; no L1-to-L2 remapping exists in the data model.
    invalid_phase_change = client.put(
        f"/api/v1/electrical/connections/{outgoing['id']}",
        json=connection_payload(
            component_endpoint,
            endpoints["rcd"],
            phases=["L2"],
            connection_type="busbar",
        ),
    )
    assert invalid_phase_change.status_code == 422
    assert "nicht eingespeist" in invalid_phase_change.text

    invalid_component_phase = client.put(
        f"/api/v1/electrical/connections/{outgoing['id']}",
        json=connection_payload(
            component_endpoint,
            endpoints["rcd"],
            phases=["N"],
            connection_type="busbar",
        ),
    )
    assert invalid_component_phase.status_code == 422
    assert "unterstützt" in invalid_component_phase.text

