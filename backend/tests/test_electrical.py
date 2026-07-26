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
from app.models.electrical import ElectricalComponent, ElectricalDistribution


@pytest.fixture
def electrical_client(tmp_path: Path) -> Generator[tuple[TestClient, Engine]]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'electrical.sqlite3'}",
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


def create_home(client: TestClient) -> tuple[dict[str, Any], dict[str, Any]]:
    root = create(
        client,
        "locations",
        {"name": "Test House", "location_type": "building"},
    )
    room = create(
        client,
        "locations",
        {
            "name": "Electrical room",
            "location_type": "room",
            "parent_id": root["id"],
        },
    )
    return root, room


def create_asset_type(client: TestClient) -> dict[str, Any]:
    return create(client, "asset-types", {"name": "Elektrische Verteilung"})


def create_asset(
    client: TestClient,
    asset_type_id: str,
    location_id: str | None,
    name: str,
    *,
    status: str = "active",
) -> dict[str, Any]:
    return create(
        client,
        "assets",
        {
            "name": name,
            "asset_type_id": asset_type_id,
            "location_id": location_id,
            "status": status,
        },
    )


def distribution_payload(
    asset_id: str,
    *,
    designation: str,
    parent_id: str | None = None,
    rows: int | None = None,
    modules_per_row: int | None = None,
) -> dict[str, Any]:
    return {
        "asset_id": asset_id,
        "parent_distribution_id": parent_id,
        "distribution_type": "sub" if parent_id else "main",
        "designation": designation,
        "rows": rows,
        "modules_per_row": modules_per_row,
        "description": f"Description for {designation}",
        "notes": None,
    }


def device_payload(
    asset_id: str,
    distribution_id: str,
    *,
    device_type: str = "mcb",
    row_number: int | None = None,
    start_position: int | None = None,
    module_width: int | None = None,
) -> dict[str, Any]:
    return {
        "asset_id": asset_id,
        "distribution_id": distribution_id,
        "device_type": device_type,
        "row_number": row_number,
        "start_position": start_position,
        "module_width": module_width,
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


def test_distribution_crud_tree_search_filter_move_and_archive_rules(
    electrical_client: tuple[TestClient, Engine],
) -> None:
    client, _ = electrical_client
    _, room = create_home(client)
    asset_type = create_asset_type(client)
    assets = [
        create_asset(client, asset_type["id"], room["id"], name)
        for name in ("Main cabinet", "Floor cabinet", "Workshop cabinet")
    ]
    main = create(
        client,
        "electrical/distributions",
        distribution_payload(
            assets[0]["id"],
            designation="HV",
            rows=3,
            modules_per_row=24,
        ),
    )
    floor = create(
        client,
        "electrical/distributions",
        distribution_payload(
            assets[1]["id"],
            designation="UV Floor",
            parent_id=main["id"],
        ),
    )
    workshop = create(
        client,
        "electrical/distributions",
        distribution_payload(assets[2]["id"], designation="UV Workshop"),
    )

    tree = client.get("/api/v1/electrical/distributions/tree")
    searched = client.get(
        "/api/v1/electrical/distributions",
        params={"search": "test house / electrical", "sort_by": "asset_name"},
    )
    filtered = client.get(
        "/api/v1/electrical/distributions",
        params={"distribution_type": "sub", "parent_distribution_id": main["id"]},
    )
    paged = client.get(
        "/api/v1/electrical/distributions",
        params={"page": 2, "page_size": 2, "sort_by": "designation"},
    )

    assert tree.status_code == 200
    assert len(tree.json()) == 2
    assert tree.json()[0]["children"][0]["id"] == floor["id"]
    assert searched.json()["total"] == 3
    assert filtered.json()["items"][0]["id"] == floor["id"]
    assert paged.json()["total"] == 3
    assert paged.json()["pages"] == 2
    assert main["direct_subdistribution_count"] == 0
    assert (
        client.get(f"/api/v1/electrical/distributions/{main['id']}").json()[
            "direct_subdistribution_count"
        ]
        == 1
    )

    updated_payload = distribution_payload(
        assets[2]["id"],
        designation="UV Workshop edited",
        parent_id=main["id"],
        rows=2,
        modules_per_row=12,
    )
    updated = client.put(
        f"/api/v1/electrical/distributions/{workshop['id']}",
        json=updated_payload,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["distribution_type"] == "sub"

    self_parent = client.post(
        f"/api/v1/electrical/distributions/{floor['id']}/move",
        json={"parent_distribution_id": floor["id"]},
    )
    cycle = client.post(
        f"/api/v1/electrical/distributions/{main['id']}/move",
        json={"parent_distribution_id": floor["id"]},
    )
    assert self_parent.status_code == 409
    assert cycle.status_code == 409
    assert (
        client.get(f"/api/v1/electrical/distributions/{main['id']}").json()[
            "parent_distribution_id"
        ]
        is None
    )

    blocked = client.delete(f"/api/v1/electrical/distributions/{main['id']}")
    assert blocked.status_code == 409
    assert client.delete(f"/api/v1/electrical/distributions/{floor['id']}").status_code == 204
    assert client.get(f"/api/v1/electrical/distributions/{floor['id']}").status_code == 404
    historical = client.get(
        f"/api/v1/electrical/distributions/{floor['id']}",
        params={"include_deleted": "true"},
    )
    assert historical.status_code == 200
    assert historical.json()["deleted_at"] is not None


def test_role_asset_validation_replacement_and_database_integrity(
    electrical_client: tuple[TestClient, Engine],
) -> None:
    client, engine = electrical_client
    _, room = create_home(client)
    asset_type = create_asset_type(client)
    valid = create_asset(client, asset_type["id"], room["id"], "Valid cabinet")
    unlocated = create_asset(client, asset_type["id"], None, "Unlocated cabinet")
    inactive = create_asset(
        client,
        asset_type["id"],
        room["id"],
        "Inactive cabinet",
        status="inactive",
    )

    created = create(
        client,
        "electrical/distributions",
        distribution_payload(valid["id"], designation="HV"),
    )
    duplicate = client.post(
        "/api/v1/electrical/protective-devices",
        json=device_payload(valid["id"], created["id"]),
    )
    missing_location = client.post(
        "/api/v1/electrical/distributions",
        json=distribution_payload(unlocated["id"], designation="No room"),
    )
    inactive_role = client.post(
        "/api/v1/electrical/distributions",
        json=distribution_payload(inactive["id"], designation="Inactive"),
    )
    assert duplicate.status_code == 409
    assert missing_location.status_code == 422
    assert inactive_role.status_code == 409
    status_change = client.put(
        f"/api/v1/assets/{valid['id']}",
        json={
            "name": valid["name"],
            "asset_type_id": asset_type["id"],
            "location_id": room["id"],
            "status": "inactive",
        },
    )
    assert status_change.status_code == 409
    assert client.delete(f"/api/v1/assets/{valid['id']}").status_code == 409

    replacement_source = create_asset(
        client,
        asset_type["id"],
        room["id"],
        "Old cabinet",
    )
    replacement_distribution = create(
        client,
        "electrical/distributions",
        distribution_payload(replacement_source["id"], designation="Old role"),
    )
    replacement_payload = {
        "replacement": {
            "name": "Replacement cabinet",
            "asset_type_id": asset_type["id"],
            "location_id": room["id"],
        },
        "reason": "Lifecycle test",
    }
    blocked_replacement = client.post(
        f"/api/v1/assets/{replacement_source['id']}/replacement",
        json=replacement_payload,
    )
    assert blocked_replacement.status_code == 409
    assert (
        client.delete(
            f"/api/v1/electrical/distributions/{replacement_distribution['id']}"
        ).status_code
        == 204
    )
    replaced = client.post(
        f"/api/v1/assets/{replacement_source['id']}/replacement",
        json=replacement_payload,
    )
    assert replaced.status_code == 201, replaced.text
    rejected_replaced = client.post(
        "/api/v1/electrical/distributions",
        json=distribution_payload(replacement_source["id"], designation="Old"),
    )
    assert rejected_replaced.status_code == 409
    historical_role = client.get(
        f"/api/v1/electrical/distributions/{replacement_distribution['id']}",
        params={"include_deleted": "true"},
    )
    assert historical_role.status_code == 200
    assert historical_role.json()["asset"]["status"] == "retired"

    with Session(engine) as session:
        session.add(
            ElectricalComponent(
                asset_id=UUID(valid["id"]),
                role="distribution",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        missing_asset_component = ElectricalComponent(
            asset_id=uuid4(),
            role="distribution",
        )
        session.add(missing_asset_component)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        invalid_parent = ElectricalDistribution(
            id=uuid4(),
            distribution_type="sub",
            parent_distribution_id=uuid4(),
        )
        session.add(invalid_parent)
        with pytest.raises(IntegrityError):
            session.commit()


@pytest.mark.parametrize("device_type", ["fuse", "rcd", "mcb", "rcbo", "spd"])
def test_all_protective_device_types_and_unknown_positions(
    electrical_client: tuple[TestClient, Engine],
    device_type: str,
) -> None:
    client, _ = electrical_client
    _, room = create_home(client)
    asset_type = create_asset_type(client)
    distribution_asset = create_asset(client, asset_type["id"], room["id"], "Distribution")
    device_asset = create_asset(client, asset_type["id"], room["id"], "Device")
    distribution = create(
        client,
        "electrical/distributions",
        distribution_payload(distribution_asset["id"], designation="HV"),
    )
    created = create(
        client,
        "electrical/protective-devices",
        device_payload(device_asset["id"], distribution["id"], device_type=device_type),
    )
    assert created["device_type"] == device_type
    assert created["row_number"] is None
    assert created["start_position"] is None
    assert created["module_width"] is None


def test_protective_device_location_position_overlap_capacity_and_archive(
    electrical_client: tuple[TestClient, Engine],
) -> None:
    client, _ = electrical_client
    root, room = create_home(client)
    other_room = create(
        client,
        "locations",
        {
            "name": "Workshop",
            "location_type": "room",
            "parent_id": root["id"],
        },
    )
    asset_type = create_asset_type(client)
    distribution_asset = create_asset(client, asset_type["id"], room["id"], "Distribution")
    distribution = create(
        client,
        "electrical/distributions",
        distribution_payload(
            distribution_asset["id"],
            designation="HV",
            rows=2,
            modules_per_row=12,
        ),
    )
    device_assets = [
        create_asset(client, asset_type["id"], room["id"], f"Device {index}") for index in range(5)
    ]
    wrong_location = create_asset(client, asset_type["id"], other_room["id"], "Wrong room device")
    first = create(
        client,
        "electrical/protective-devices",
        device_payload(
            device_assets[0]["id"],
            distribution["id"],
            row_number=1,
            start_position=2,
            module_width=2,
        ),
    )
    partial = client.post(
        "/api/v1/electrical/protective-devices",
        json=device_payload(
            device_assets[1]["id"],
            distribution["id"],
            row_number=1,
        ),
    )
    overlap = client.post(
        "/api/v1/electrical/protective-devices",
        json=device_payload(
            device_assets[1]["id"],
            distribution["id"],
            row_number=1,
            start_position=3,
            module_width=1,
        ),
    )
    row_overflow = client.post(
        "/api/v1/electrical/protective-devices",
        json=device_payload(
            device_assets[2]["id"],
            distribution["id"],
            row_number=3,
            start_position=1,
            module_width=1,
        ),
    )
    module_overflow = client.post(
        "/api/v1/electrical/protective-devices",
        json=device_payload(
            device_assets[3]["id"],
            distribution["id"],
            row_number=2,
            start_position=12,
            module_width=2,
        ),
    )
    location_mismatch = client.post(
        "/api/v1/electrical/protective-devices",
        json=device_payload(wrong_location["id"], distribution["id"]),
    )
    assert partial.status_code == 422
    assert overlap.status_code == 409
    assert row_overflow.status_code == 409
    assert module_overflow.status_code == 409
    assert location_mismatch.status_code == 409

    detail = client.get(f"/api/v1/electrical/distributions/{distribution['id']}")
    assert detail.json()["direct_protective_device_count"] == 1
    assert [item["id"] for item in detail.json()["protective_devices"]] == [first["id"]]
    blocked_archive = client.delete(f"/api/v1/electrical/distributions/{distribution['id']}")
    assert blocked_archive.status_code == 409
    assert client.delete(f"/api/v1/electrical/protective-devices/{first['id']}").status_code == 204
    archived_distribution = client.delete(f"/api/v1/electrical/distributions/{distribution['id']}")
    assert archived_distribution.status_code == 204

    archived_target = client.post(
        "/api/v1/electrical/protective-devices",
        json=device_payload(device_assets[4]["id"], distribution["id"]),
    )
    assert archived_target.status_code == 422
    historical_device = client.get(
        f"/api/v1/electrical/protective-devices/{first['id']}",
        params={"include_deleted": "true"},
    )
    assert historical_device.status_code == 200
    assert historical_device.json()["deleted_at"] is not None


def test_available_assets_and_embedded_devices_exceed_one_hundred_without_loss(
    electrical_client: tuple[TestClient, Engine],
) -> None:
    client, _ = electrical_client
    _, room = create_home(client)
    asset_type = create_asset_type(client)
    distribution_asset = create_asset(client, asset_type["id"], room["id"], "Distribution")
    distribution = create(
        client,
        "electrical/distributions",
        distribution_payload(distribution_asset["id"], designation="HV"),
    )
    device_assets = [
        create_asset(
            client,
            asset_type["id"],
            room["id"],
            f"Protection {index:03d}",
        )
        for index in range(105)
    ]

    first_candidates = client.get(
        "/api/v1/electrical/available-assets",
        params={"role": "protective_device", "page": 1, "page_size": 100},
    )
    second_candidates = client.get(
        "/api/v1/electrical/available-assets",
        params={"role": "protective_device", "page": 2, "page_size": 100},
    )
    assert first_candidates.status_code == 200
    assert first_candidates.json()["total"] == 105
    assert len(first_candidates.json()["items"]) == 100
    assert len(second_candidates.json()["items"]) == 5

    for asset in device_assets[:101]:
        response = client.post(
            "/api/v1/electrical/protective-devices",
            json=device_payload(asset["id"], distribution["id"]),
        )
        assert response.status_code == 201, response.text

    list_page_one = client.get(
        "/api/v1/electrical/protective-devices",
        params={
            "distribution_id": distribution["id"],
            "page": 1,
            "page_size": 100,
        },
    ).json()
    list_page_two = client.get(
        "/api/v1/electrical/protective-devices",
        params={
            "distribution_id": distribution["id"],
            "page": 2,
            "page_size": 100,
        },
    ).json()
    detail = client.get(f"/api/v1/electrical/distributions/{distribution['id']}").json()

    assert list_page_one["total"] == 101
    assert len(list_page_one["items"]) == 100
    assert len(list_page_two["items"]) == 1
    assert detail["direct_protective_device_count"] == 101
    assert len(detail["protective_devices"]) == 101
    assert len({item["id"] for item in detail["protective_devices"]}) == 101


def test_distribution_asset_selection_and_backend_reject_non_distribution_type(
    electrical_client: tuple[TestClient, Engine],
) -> None:
    client, _ = electrical_client
    _, room = create_home(client)
    distribution_type = create_asset_type(client)
    meter_type = create(client, "asset-types", {"name": "Zähler"})
    distribution_asset = create_asset(
        client,
        distribution_type["id"],
        room["id"],
        "Main distribution",
    )
    meter_asset = create_asset(
        client,
        meter_type["id"],
        room["id"],
        "Grid meter",
    )

    available = client.get(
        "/api/v1/electrical/available-assets",
        params={"role": "distribution", "page_size": 100},
    )
    assert available.status_code == 200, available.text
    assert [item["id"] for item in available.json()["items"]] == [
        distribution_asset["id"]
    ]

    invalid = client.post(
        "/api/v1/electrical/distributions",
        json=distribution_payload(meter_asset["id"], designation="Invalid"),
    )
    assert invalid.status_code == 422
    assert "Elektrische Verteilung" in invalid.json()["detail"]
