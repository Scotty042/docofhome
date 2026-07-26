from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401
from app.db.session import get_session
from app.main import app
from app.models.asset_engine import Asset, AssetType


@pytest.fixture
def network_client(tmp_path: Path) -> Generator[TestClient]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'network-api.sqlite3'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        asset_type = AssetType(name="Network device", code_prefix="NET")
        session.add(asset_type)
        session.flush()
        session.add_all(
            [
                Asset(name="Core Switch", jarvis_code="NET-0001", asset_type_id=asset_type.id),
                Asset(name="NAS", jarvis_code="NET-0002", asset_type_id=asset_type.id),
            ]
        )
        session.commit()

    def override_session() -> Generator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_network_api_complete_documentation_flow(network_client: TestClient) -> None:
    candidates = network_client.get("/api/v1/network/device-candidates")
    assert candidates.status_code == 200, candidates.text
    candidate_by_name = {item["name"]: item for item in candidates.json()}

    switch = network_client.post(
        "/api/v1/network/devices",
        json={
            "asset_id": candidate_by_name["Core Switch"]["asset_id"],
            "role": "switch",
            "hostname": "sw-core",
            "management_url": "https://192.168.10.2/",
            "notes": "Main switch",
        },
    )
    assert switch.status_code == 201, switch.text
    nas = network_client.post(
        "/api/v1/network/devices",
        json={
            "asset_id": candidate_by_name["NAS"]["asset_id"],
            "role": "nas",
            "hostname": "nas",
            "management_url": None,
            "notes": None,
        },
    )
    assert nas.status_code == 201, nas.text

    segment = network_client.post(
        "/api/v1/network/segments",
        json={
            "name": "LAN",
            "cidr": "192.168.10.0/24",
            "vlan_id": None,
            "gateway": "192.168.10.1",
            "dns_servers": ["192.168.10.1"],
            "description": "Main LAN",
        },
    )
    assert segment.status_code == 201, segment.text
    assert segment.json()["vlan_id"] is None

    switch_port = network_client.post(
        "/api/v1/network/interfaces",
        json={
            "network_device_id": switch.json()["id"],
            "name": "Port 1",
            "interface_type": "ethernet",
            "mac_address": "aa-bb-cc-dd-ee-01",
            "speed_mbps": 1000,
            "poe_mode": "source",
            "enabled": True,
            "description": None,
        },
    )
    assert switch_port.status_code == 201, switch_port.text
    assert switch_port.json()["mac_address"] == "AA:BB:CC:DD:EE:01"

    nas_port = network_client.post(
        "/api/v1/network/interfaces",
        json={
            "network_device_id": nas.json()["id"],
            "name": "eth0",
            "interface_type": "ethernet",
            "mac_address": "AA:BB:CC:DD:EE:02",
            "speed_mbps": 1000,
            "poe_mode": "none",
            "enabled": True,
            "description": None,
        },
    )
    assert nas_port.status_code == 201, nas_port.text

    address = network_client.post(
        "/api/v1/network/addresses",
        json={
            "interface_id": nas_port.json()["id"],
            "segment_id": segment.json()["id"],
            "address": "192.168.10.20",
            "assignment_type": "static",
            "hostname": "nas",
            "is_primary": True,
            "notes": None,
        },
    )
    assert address.status_code == 201, address.text

    connection = network_client.post(
        "/api/v1/network/connections",
        json={
            "source_interface_id": switch_port.json()["id"],
            "target_interface_id": nas_port.json()["id"],
            "connection_type": "physical",
            "status": "active",
            "cable_type": "Cat 6A",
            "cable_label": "P01",
            "description": None,
        },
    )
    assert connection.status_code == 201, connection.text

    summary = network_client.get("/api/v1/network/summary")
    assert summary.status_code == 200, summary.text
    assert summary.json() == {
        "device_count": 2,
        "segment_count": 1,
        "interface_count": 2,
        "address_count": 1,
        "connection_count": 1,
        "free_interface_count": 0,
        "device_without_connection_count": 0,
        "unconnected_interface_count": 0,
    }

    topology = network_client.get("/api/v1/network/topology")
    assert topology.status_code == 200, topology.text
    assert len(topology.json()["nodes"]) == 2
    assert len(topology.json()["edges"]) == 1


def test_network_api_reports_validation_and_conflicts(network_client: TestClient) -> None:
    asset_id = network_client.get("/api/v1/network/device-candidates").json()[0]["asset_id"]
    first = network_client.post(
        "/api/v1/network/devices",
        json={
            "asset_id": asset_id,
            "role": "router",
            "hostname": "router",
            "management_url": None,
            "notes": None,
        },
    )
    assert first.status_code == 201, first.text

    duplicate = network_client.post(
        "/api/v1/network/devices",
        json={
            "asset_id": asset_id,
            "role": "router",
            "hostname": "router-2",
            "management_url": None,
            "notes": None,
        },
    )
    assert duplicate.status_code == 409

    invalid_segment = network_client.post(
        "/api/v1/network/segments",
        json={
            "name": "Invalid",
            "cidr": "10.0.0.0/24",
            "vlan_id": 5000,
            "gateway": "192.168.1.1",
            "dns_servers": [],
            "description": None,
        },
    )
    assert invalid_segment.status_code == 422


def test_network_page_endpoints_load_with_empty_legacy_compatible_data(
    network_client: TestClient,
) -> None:
    endpoints = (
        "/api/v1/network/devices",
        "/api/v1/network/device-candidates",
        "/api/v1/network/segments",
        "/api/v1/network/interfaces",
        "/api/v1/network/connections",
        "/api/v1/network/summary",
        "/api/v1/network/topology",
    )

    responses = [network_client.get(endpoint) for endpoint in endpoints]

    assert all(response.status_code == 200 for response in responses)
    assert responses[5].json()["free_interface_count"] == 0
