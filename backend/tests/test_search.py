from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import get_session
from app.main import app
from app.models.asset_engine import Asset, AssetType, Location, Product
from app.models.electrical import (
    ElectricalComponent,
    ElectricalDistribution,
    ElectricalProtectiveDevice,
)
from app.models.electrical_circuit import ElectricalCircuit
from app.models.knowledge import WikiPage
from app.models.network import NetworkAddress, NetworkDevice, NetworkInterface, NetworkSegment
from app.repositories.search import GlobalSearchRepository


@pytest.fixture
def search_client(tmp_path: Path) -> Generator[TestClient]:
    database_path = tmp_path / "search.sqlite3"
    test_engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(test_engine)

    root_id = uuid4()
    room_id = uuid4()
    asset_type_id = uuid4()
    product_id = uuid4()
    exact_asset_id = uuid4()
    wildcard_asset_id = uuid4()
    archived_asset_id = uuid4()
    distribution_asset_id = uuid4()
    device_asset_id = uuid4()
    distribution_id = uuid4()
    device_id = uuid4()
    circuit_id = uuid4()
    network_device_id = uuid4()
    network_interface_id = uuid4()
    network_segment_id = uuid4()

    with Session(test_engine) as session:
        session.add_all(
            [
                Location(id=root_id, name="Testhaus", location_type="building"),
                Location(
                    id=room_id,
                    name="Technikkeller",
                    short_name="TK",
                    location_type="room",
                    parent_id=root_id,
                    description="Zentrale Haustechnik",
                    notes="Enthält die Elektroverteilung",
                ),
                Location(
                    name="Archivraum",
                    location_type="room",
                    parent_id=root_id,
                    deleted_at=datetime.now(UTC),
                ),
                AssetType(
                    id=asset_type_id,
                    name="Wechselrichter",
                    code_prefix="INV",
                ),
                WikiPage(
                    title="Heizungswissen",
                    slug="heizungswissen",
                    content="Wartung und Filterwechsel im Keller",
                ),
                Product(
                    id=product_id,
                    name="Sunny Home",
                    manufacturer="Solar GmbH",
                    model_number="SH-9000",
                    asset_type_id=asset_type_id,
                ),
            ]
        )
        session.flush()
        session.add_all(
            [
                Asset(
                    id=exact_asset_id,
                    name="PV Wechselrichter",
                    jarvis_code="INV-001",
                    description="Primärer Wechselrichter",
                    asset_type_id=asset_type_id,
                    product_id=product_id,
                    location_id=room_id,
                    serial_number="SER-ÄÖ-01",
                    inventory_number="INV-NUM-01",
                ),
                Asset(
                    id=wildcard_asset_id,
                    name='Pumpe \\ "ÄÖ" 100%_Safe',
                    jarvis_code="INV-001-EXT",
                    asset_type_id=asset_type_id,
                    location_id=room_id,
                ),
                Asset(
                    id=archived_asset_id,
                    name="Altes Steuergerät",
                    jarvis_code="INV-OLD",
                    asset_type_id=asset_type_id,
                    location_id=room_id,
                    deleted_at=datetime.now(UTC),
                ),
                Asset(
                    id=distribution_asset_id,
                    name="Hauptverteilung Keller",
                    jarvis_code="UV-001",
                    asset_type_id=asset_type_id,
                    location_id=room_id,
                ),
                Asset(
                    id=device_asset_id,
                    name="FI Küche",
                    jarvis_code="FI-001",
                    asset_type_id=asset_type_id,
                    location_id=room_id,
                ),
            ]
        )
        session.flush()
        session.add_all(
            [
                ElectricalComponent(
                    id=distribution_id,
                    asset_id=distribution_asset_id,
                    role="distribution",
                ),
                ElectricalComponent(
                    id=device_id,
                    asset_id=device_asset_id,
                    role="protective_device",
                ),
            ]
        )
        session.flush()
        session.add(
            ElectricalDistribution(
                id=distribution_id,
                distribution_type="main",
                designation="HV Keller",
                rows=2,
                modules_per_row=12,
                description="Zentrale Stromverteilung",
            )
        )
        session.flush()
        session.add(
            ElectricalProtectiveDevice(
                id=device_id,
                distribution_id=distribution_id,
                device_type="rcd",
                rated_current_a=40,
                residual_current_ma=30,
                rcd_type="Typ A",
                notes="Schützt die Küchenkreise",
            )
        )
        session.add(
            ElectricalCircuit(
                id=circuit_id,
                distribution_id=distribution_id,
                protective_device_id=device_id,
                name="Küchensteckdosen",
                circuit_number="K-01",
                description="Arbeitsplatte und Kühlschrank",
            )
        )
        session.add(
            NetworkDevice(
                id=network_device_id,
                asset_id=exact_asset_id,
                role="server",
                hostname="pv-server",
                notes="Netzwerkgerät im Keller",
            )
        )
        session.flush()
        session.add(
            NetworkSegment(
                id=network_segment_id,
                name="Technik-LAN",
                cidr="172.16.10.0/24",
                vlan_id=110,
                gateway="172.16.10.1",
                dns_servers_json='["172.16.10.1"]',
            )
        )
        session.add(
            NetworkInterface(
                id=network_interface_id,
                network_device_id=network_device_id,
                name="eth0",
                interface_type="ethernet",
                mac_address="AA:BB:CC:DD:EE:10",
                poe_mode="none",
            )
        )
        session.flush()
        session.add(
            NetworkAddress(
                interface_id=network_interface_id,
                segment_id=network_segment_id,
                address="172.16.10.20",
                assignment_type="static",
                hostname="pv-server",
                is_primary=True,
            )
        )
        session.commit()

    def override_session() -> Generator[Session]:
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def group(body: dict[str, Any], result_type: str) -> dict[str, Any]:
    groups = body["groups"]
    assert isinstance(groups, list)
    return next(item for item in groups if item["result_type"] == result_type)


def test_global_search_returns_fixed_groups_and_all_supported_types(
    search_client: TestClient,
) -> None:
    response = search_client.get("/api/v1/search", params={"q": "Keller"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["query"] == "Keller"
    assert [item["result_type"] for item in body["groups"]] == [
        "asset",
        "location",
        "electrical_distribution",
        "electrical_protective_device",
        "electrical_circuit",
        "wiki_page",
            "network_device",
            "network_segment",
            "consumption_meter",
            "document",
    ]
    assert group(body, "asset")["results"]
    assert group(body, "location")["results"][0]["title"] == "Technikkeller"
    assert group(body, "electrical_distribution")["results"][0]["title"] == "HV Keller"
    assert group(body, "network_device")["results"][0]["title"] == "PV Wechselrichter"

    circuit = search_client.get("/api/v1/search", params={"q": "K-01"}).json()
    assert group(circuit, "electrical_circuit")["results"][0]["title"] == "Küchensteckdosen"

    wiki = search_client.get("/api/v1/search", params={"q": "Filterwechsel"}).json()
    assert group(wiki, "wiki_page")["results"][0]["title"] == "Heizungswissen"

    device = search_client.get("/api/v1/search", params={"q": "Typ A"}).json()
    assert group(device, "electrical_protective_device")["results"][0]["title"] == "FI Küche"

    network_address = search_client.get("/api/v1/search", params={"q": "172.16.10.20"}).json()
    assert group(network_address, "network_device")["results"][0]["title"] == "PV Wechselrichter"

    network_vlan = search_client.get("/api/v1/search", params={"q": "110"}).json()
    assert group(network_vlan, "network_segment")["results"][0]["title"] == "Technik-LAN"


def test_asset_search_covers_product_identifiers_and_exact_code_ranking(
    search_client: TestClient,
) -> None:
    for value in ("Solar GmbH", "SH-9000", "SER-ÄÖ-01", "INV-NUM-01"):
        body = search_client.get("/api/v1/search", params={"q": value}).json()
        assert group(body, "asset")["results"][0]["title"] == "PV Wechselrichter"

    ranked = search_client.get("/api/v1/search", params={"q": "INV-001"}).json()
    results = group(ranked, "asset")["results"]
    assert [item["title"] for item in results[:2]] == [
        "PV Wechselrichter",
        'Pumpe \\ "ÄÖ" 100%_Safe',
    ]


def test_search_treats_wildcards_quotes_backslash_and_unicode_as_text(
    search_client: TestClient,
) -> None:
    for value in ("%_", '"ÄÖ"', '\\ "'):
        response = search_client.get("/api/v1/search", params={"q": value})
        assert response.status_code == 200, response.text
        results = group(response.json(), "asset")["results"]
        assert results[0]["title"] == 'Pumpe \\ "ÄÖ" 100%_Safe'


def test_search_limit_validation_and_no_result_state(search_client: TestClient) -> None:
    limited = search_client.get(
        "/api/v1/search",
        params={"q": "INV", "limit_per_type": 1},
    )
    assert limited.status_code == 200
    assert len(group(limited.json(), "asset")["results"]) == 1

    empty = search_client.get("/api/v1/search", params={"q": "nichtvorhanden"})
    assert empty.status_code == 200
    assert empty.json()["total"] == 0
    assert all(item["total"] == 0 for item in empty.json()["groups"])

    assert search_client.get("/api/v1/search").status_code == 422
    assert search_client.get("/api/v1/search", params={"q": "a"}).status_code == 422
    assert search_client.get("/api/v1/search", params={"q": "  a  "}).status_code == 422
    assert search_client.get("/api/v1/search", params={"q": "x" * 101}).status_code == 422
    assert (
        search_client.get("/api/v1/search", params={"q": "ok", "limit_per_type": 0}).status_code
        == 422
    )
    assert (
        search_client.get("/api/v1/search", params={"q": "ok", "limit_per_type": 21}).status_code
        == 422
    )


def test_only_assets_use_the_safe_archived_search_route(search_client: TestClient) -> None:
    active_only = search_client.get("/api/v1/search", params={"q": "Altes"}).json()
    assert group(active_only, "asset")["results"] == []

    archived = search_client.get(
        "/api/v1/search",
        params={"q": "Altes", "include_archived": "true"},
    ).json()
    result = group(archived, "asset")["results"][0]
    assert result["archived"] is True
    assert result["route"].endswith("?archived=1")

    archived_location = search_client.get(
        "/api/v1/search",
        params={"q": "Archivraum", "include_archived": "true"},
    ).json()
    assert group(archived_location, "location")["results"] == []


def test_search_failure_is_atomic_and_does_not_expose_internal_details(
    search_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*_: object, **__: object) -> list[object]:
        raise RuntimeError("sqlite:///secret/path?token=do-not-leak")

    monkeypatch.setattr(GlobalSearchRepository, "search_locations", fail)
    response = search_client.get("/api/v1/search", params={"q": "Keller"})

    assert response.status_code == 500
    assert "do-not-leak" not in response.text
    assert "sqlite" not in response.text.casefold()
