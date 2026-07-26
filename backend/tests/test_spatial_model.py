from collections.abc import Generator
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import get_session
from app.main import app
from app.models.asset_engine import Location


@pytest.fixture
def spatial_client(tmp_path: Path) -> Generator[tuple[TestClient, Engine]]:
    test_engine = create_engine(
        f"sqlite:///{tmp_path / 'spatial.sqlite3'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(test_engine)

    def override_session() -> Generator[Session]:
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client, test_engine
    app.dependency_overrides.clear()


def create_location(
    client: TestClient,
    name: str,
    location_type: str,
    parent_id: str | None = None,
    **values: Any,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/locations",
        json={
            "name": name,
            "location_type": location_type,
            "parent_id": parent_id,
            **values,
        },
    )
    assert response.status_code == 201, response.text
    result: dict[str, Any] = response.json()
    return result


def test_root_hierarchy_paths_tree_search_filter_move_and_counts(
    spatial_client: tuple[TestClient, Engine],
) -> None:
    client, _ = spatial_client
    root = create_location(client, "Test House", "building", sort_order=0)
    second_root = client.post(
        "/api/v1/locations",
        json={"name": "Other House", "location_type": "building"},
    )
    child_building = client.post(
        "/api/v1/locations",
        json={"name": "Nested House", "location_type": "building", "parent_id": root["id"]},
    )
    orphan = client.post(
        "/api/v1/locations",
        json={"name": "Orphan room", "location_type": "room"},
    )
    ground = create_location(client, "Ground floor", "floor", root["id"], sort_order=10)
    basement = create_location(client, "Basement", "floor", root["id"], sort_order=20)
    kitchen = create_location(
        client,
        "Kitchen",
        "room",
        ground["id"],
        short_name="KIT",
        notes="Main cooking area",
    )
    compatible_update = client.put(
        f"/api/v1/locations/{kitchen['id']}",
        json={"name": "Kitchen"},
    )
    assert compatible_update.status_code == 200
    assert compatible_update.json()["parent_id"] == ground["id"]
    assert compatible_update.json()["location_type"] == "room"

    asset_type = client.post("/api/v1/asset-types", json={"name": "Appliance"}).json()
    asset = client.post(
        "/api/v1/assets",
        json={
            "name": "Oven",
            "asset_type_id": asset_type["id"],
            "location_id": kitchen["id"],
        },
    )
    assert asset.status_code == 201, asset.text

    detail = client.get(f"/api/v1/locations/{kitchen['id']}").json()
    root_detail = client.get(f"/api/v1/locations/{root['id']}").json()
    search = client.get("/api/v1/locations", params={"search": "ground floor / kit"}).json()
    filtered = client.get(
        "/api/v1/locations",
        params={"location_type": "room", "sort_by": "path"},
    ).json()
    paged = client.get(
        "/api/v1/locations",
        params={"page": 2, "page_size": 2, "sort_by": "name"},
    ).json()
    tree = client.get("/api/v1/locations/tree").json()

    assert second_root.status_code == 409
    assert child_building.status_code == 409
    assert orphan.status_code == 422
    assert detail["path"] == "Test House / Ground floor / Kitchen"
    assert [item["name"] for item in detail["breadcrumbs"]] == [
        "Test House",
        "Ground floor",
        "Kitchen",
    ]
    assert detail["direct_asset_count"] == 1
    assert detail["descendant_asset_count"] == 0
    assert root_detail["direct_asset_count"] == 0
    assert root_detail["descendant_asset_count"] == 1
    assert [item["id"] for item in search["items"]] == [kitchen["id"]]
    assert [item["id"] for item in filtered["items"]] == [kitchen["id"]]
    assert paged["total"] == 4
    assert paged["pages"] == 2
    assert tree[0]["id"] == root["id"]
    assert [item["name"] for item in tree[0]["children"]] == ["Ground floor", "Basement"]

    moved = client.post(
        f"/api/v1/locations/{kitchen['id']}/move",
        json={"parent_id": basement["id"]},
    )
    cycle = client.post(
        f"/api/v1/locations/{basement['id']}/move",
        json={"parent_id": kitchen["id"]},
    )
    self_parent = client.post(
        f"/api/v1/locations/{kitchen['id']}/move",
        json={"parent_id": kitchen["id"]},
    )

    assert moved.status_code == 200
    assert moved.json()["path"] == "Test House / Basement / Kitchen"
    assert cycle.status_code == 409
    assert self_parent.status_code == 409
    assert client.get(f"/api/v1/locations/{basement['id']}").json()["path"] == (
        "Test House / Basement"
    )


def test_archive_rules_and_archived_assignment_protection(
    spatial_client: tuple[TestClient, Engine],
) -> None:
    client, _ = spatial_client
    root = create_location(client, "Test House", "building")
    floor = create_location(client, "Ground floor", "floor", root["id"])
    room = create_location(client, "Office", "room", floor["id"])

    assert client.delete(f"/api/v1/locations/{root['id']}").status_code == 409
    child_conflict = client.delete(f"/api/v1/locations/{floor['id']}")
    assert child_conflict.status_code == 409
    assert "active child" in child_conflict.text

    asset_type = client.post("/api/v1/asset-types", json={"name": "Computer"}).json()
    assigned = client.post(
        "/api/v1/assets",
        json={
            "name": "Workstation",
            "asset_type_id": asset_type["id"],
            "location_id": room["id"],
        },
    )
    assert assigned.status_code == 201
    asset_conflict = client.delete(f"/api/v1/locations/{room['id']}")
    assert asset_conflict.status_code == 409
    assert "assigned assets" in asset_conflict.text

    archived = create_location(client, "Old storage", "area", root["id"])
    assert client.delete(f"/api/v1/locations/{archived['id']}").status_code == 204
    assert client.get(f"/api/v1/locations/{archived['id']}").status_code == 404
    historical = client.get(
        f"/api/v1/locations/{archived['id']}",
        params={"include_deleted": "true"},
    )
    child_assignment = client.post(
        "/api/v1/locations",
        json={
            "name": "Invalid child",
            "location_type": "room",
            "parent_id": archived["id"],
        },
    )
    asset_assignment = client.post(
        "/api/v1/assets",
        json={
            "name": "Invalid asset",
            "asset_type_id": asset_type["id"],
            "location_id": archived["id"],
        },
    )
    move_to_archived = client.post(
        f"/api/v1/locations/{floor['id']}/move",
        json={"parent_id": archived["id"]},
    )

    assert historical.status_code == 200
    assert historical.json()["deleted_at"] is not None
    assert child_assignment.status_code == 422
    assert asset_assignment.status_code == 422
    assert move_to_archived.status_code == 422


def test_database_enforces_root_type_and_foreign_key_constraints(
    spatial_client: tuple[TestClient, Engine],
) -> None:
    _, test_engine = spatial_client
    with Session(test_engine) as session:
        root = Location(name="Test House", location_type="building")
        session.add(root)
        session.commit()

        session.add(Location(name="Other House", location_type="building"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        session.add(Location(name="Invalid root", location_type="room"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        session.add(
            Location(
                name="Missing parent",
                location_type="room",
                parent_id=uuid4(),
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
