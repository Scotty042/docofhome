import re
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import get_session
from app.main import app
from app.models.asset_engine import Asset, AssetType, Label
from app.schemas.asset_engine import AssetTypeWrite, AssetWrite
from app.services.asset_engine import AssetService, AssetTypeService


@pytest.fixture
def asset_client(tmp_path: Path) -> Generator[TestClient]:
    database_path = tmp_path / "assets.sqlite3"
    test_engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(test_engine)

    def override_session() -> Generator[Session]:
        with Session(test_engine) as session:
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


def asset_references(client: TestClient) -> dict[str, dict[str, Any]]:
    asset_type = create(
        client,
        "asset-types",
        {"name": "Computer", "description": "Computing devices", "icon": "mdi-laptop"},
    )
    product = create(
        client,
        "products",
        {
            "name": "Workstation",
            "manufacturer": "Example Corp",
            "model_number": "W-1",
            "asset_type_id": asset_type["id"],
        },
    )
    root = create(
        client,
        "locations",
        {"name": "Test House", "location_type": "building"},
    )
    location = create(
        client,
        "locations",
        {"name": "Office", "location_type": "room", "parent_id": root["id"]},
    )
    label = create(client, "labels", {"name": "Important", "color": "#FF8800"})
    return {
        "asset_type": asset_type,
        "product": product,
        "location": location,
        "label": label,
    }


def asset_payload(refs: dict[str, dict[str, Any]], name: str = "Desk computer") -> dict[str, Any]:
    return {
        "name": name,
        "description": "Primary office computer",
        "asset_type_id": refs["asset_type"]["id"],
        "product_id": refs["product"]["id"],
        "location_id": refs["location"]["id"],
        "serial_number": f"SERIAL-{name}",
        "inventory_number": f"INV-{name}",
        "status": "active",
        "label_ids": [refs["label"]["id"]],
    }


@pytest.mark.parametrize(
    ("endpoint", "payload", "update"),
    [
        (
            "asset-types",
            {"name": "Appliance", "description": "Home appliance", "icon": "mdi-fridge"},
            {"name": "Kitchen appliance", "description": None, "icon": "mdi-stove"},
        ),
        (
            "products",
            {"name": "Generic product", "manufacturer": "Example", "model_number": "A1"},
            {"name": "Updated product", "manufacturer": "Example", "model_number": "A2"},
        ),
        (
            "labels",
            {"name": "Warranty", "color": "#336699"},
            {"name": "Warranty expired", "color": "#993333"},
        ),
    ],
)
def test_reference_resource_crud_and_soft_delete(
    asset_client: TestClient,
    endpoint: str,
    payload: dict[str, Any],
    update: dict[str, Any],
) -> None:
    created = create(asset_client, endpoint, payload)

    listed = asset_client.get(f"/api/v1/{endpoint}")
    fetched = asset_client.get(f"/api/v1/{endpoint}/{created['id']}")
    updated = asset_client.put(f"/api/v1/{endpoint}/{created['id']}", json=update)
    deleted = asset_client.delete(f"/api/v1/{endpoint}/{created['id']}")

    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert fetched.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["name"] == update["name"]
    assert deleted.status_code == 204
    assert asset_client.get(f"/api/v1/{endpoint}/{created['id']}").status_code == 404

    active = asset_client.get(f"/api/v1/{endpoint}").json()
    with_deleted = asset_client.get(
        f"/api/v1/{endpoint}", params={"include_deleted": "true"}
    ).json()
    assert active["total"] == 0
    assert with_deleted["total"] == 1
    assert with_deleted["items"][0]["deleted_at"] is not None


def test_asset_crud_nested_references_and_label_assignment(asset_client: TestClient) -> None:
    refs = asset_references(asset_client)
    created = create(asset_client, "assets", asset_payload(refs))

    assert created["asset_type"] == {"id": refs["asset_type"]["id"], "name": "Computer"}
    assert created["product"]["name"] == "Workstation"
    assert created["location"]["name"] == "Office"
    assert created["labels"][0]["name"] == "Important"
    assert created["labels"][0]["color"] == "#ff8800"

    update = asset_payload(refs, "Edited computer")
    update["status"] = "maintenance"
    update["label_ids"] = []
    updated = asset_client.put(f"/api/v1/assets/{created['id']}", json=update)

    assert updated.status_code == 200
    assert updated.json()["name"] == "Edited computer"
    assert updated.json()["status"] == "maintenance"
    assert updated.json()["labels"] == []
    assert asset_client.delete(f"/api/v1/assets/{created['id']}").status_code == 204
    assert asset_client.get(f"/api/v1/assets/{created['id']}").status_code == 404
    assert asset_client.get("/api/v1/assets").json()["total"] == 0
    assert (
        asset_client.get("/api/v1/assets", params={"include_deleted": "true"}).json()["total"] == 1
    )


def test_asset_search_filter_sort_and_pagination(asset_client: TestClient) -> None:
    refs = asset_references(asset_client)
    other_label = create(asset_client, "labels", {"name": "Portable", "color": "#009688"})
    names = ["Zulu workstation", "Alpha notebook", "Beta tablet"]
    created_assets = []
    for index, name in enumerate(names):
        payload = asset_payload(refs, name)
        payload["status"] = "maintenance" if index == 1 else "active"
        payload["label_ids"] = [other_label["id"]] if index == 2 else [refs["label"]["id"]]
        created_assets.append(create(asset_client, "assets", payload))

    first_page = asset_client.get(
        "/api/v1/assets",
        params={"page": 1, "page_size": 2, "sort_by": "name", "sort_order": "asc"},
    ).json()
    search = asset_client.get("/api/v1/assets", params={"search": "notebook"}).json()
    status_filter = asset_client.get("/api/v1/assets", params={"status": "maintenance"}).json()
    label_filter = asset_client.get("/api/v1/assets", params={"label_id": other_label["id"]}).json()

    assert first_page["total"] == 3
    assert first_page["pages"] == 2
    assert [item["name"] for item in first_page["items"]] == ["Alpha notebook", "Beta tablet"]
    assert search["total"] == 1
    assert search["items"][0]["id"] == created_assets[1]["id"]
    assert status_filter["total"] == 1
    assert label_filter["total"] == 1
    assert label_filter["items"][0]["id"] == created_assets[2]["id"]


def test_relationship_crud_filters_and_soft_delete(asset_client: TestClient) -> None:
    refs = asset_references(asset_client)
    source = create(asset_client, "assets", asset_payload(refs, "Server"))
    target = create(asset_client, "assets", asset_payload(refs, "UPS"))
    relationship = create(
        asset_client,
        "relationships",
        {
            "source_asset_id": source["id"],
            "target_asset_id": target["id"],
            "relationship_type": "powered_by",
            "description": "Protected circuit",
        },
    )

    filtered = asset_client.get(
        "/api/v1/relationships",
        params={"source_asset_id": source["id"], "relationship_type": "powered_by"},
    )
    updated = asset_client.put(
        f"/api/v1/relationships/{relationship['id']}",
        json={
            "source_asset_id": source["id"],
            "target_asset_id": target["id"],
            "relationship_type": "depends_on",
        },
    )

    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert updated.status_code == 200
    assert updated.json()["relationship_type"] == "depends_on"
    assert asset_client.delete(f"/api/v1/relationships/{relationship['id']}").status_code == 204
    assert asset_client.get("/api/v1/relationships").json()["total"] == 0


def test_invalid_references_and_relationship_self_link_are_rejected(
    asset_client: TestClient,
) -> None:
    refs = asset_references(asset_client)
    invalid_asset = asset_payload(refs)
    invalid_asset["asset_type_id"] = "00000000-0000-0000-0000-000000000000"
    asset = create(asset_client, "assets", asset_payload(refs, "Only asset"))

    missing_reference = asset_client.post("/api/v1/assets", json=invalid_asset)
    self_link = asset_client.post(
        "/api/v1/relationships",
        json={
            "source_asset_id": asset["id"],
            "target_asset_id": asset["id"],
            "relationship_type": "connected_to",
        },
    )

    assert missing_reference.status_code == 422
    assert "does not exist" in missing_reference.text
    assert self_link.status_code == 422


def test_location_cycles_and_invalid_sort_are_rejected(asset_client: TestClient) -> None:
    root = create(
        asset_client,
        "locations",
        {"name": "Test House", "location_type": "building"},
    )
    parent = create(
        asset_client,
        "locations",
        {"name": "Parent", "location_type": "floor", "parent_id": root["id"]},
    )
    child = create(
        asset_client,
        "locations",
        {"name": "Child", "location_type": "room", "parent_id": parent["id"]},
    )

    cycle = asset_client.put(
        f"/api/v1/locations/{parent['id']}",
        json={"name": "Parent", "location_type": "floor", "parent_id": child["id"]},
    )
    invalid_sort = asset_client.get("/api/v1/assets", params={"sort_by": "secret"})
    invalid_page_size = asset_client.get("/api/v1/assets", params={"page_size": 101})

    assert cycle.status_code == 409
    assert "cycle" in cycle.text
    assert invalid_sort.status_code == 422
    assert invalid_page_size.status_code == 422


def test_jarvis_codes_are_automatic_searchable_and_immutable(asset_client: TestClient) -> None:
    refs = asset_references(asset_client)
    first = create(asset_client, "assets", asset_payload(refs, "First computer"))
    second = create(asset_client, "assets", asset_payload(refs, "Second computer"))

    assert re.fullmatch(r"COM-\d{3}", first["jarvis_code"])
    assert int(second["jarvis_code"].rsplit("-", 1)[1]) == (
        int(first["jarvis_code"].rsplit("-", 1)[1]) + 1
    )
    search = asset_client.get("/api/v1/assets", params={"search": first["jarvis_code"]})
    assert search.status_code == 200
    assert [item["id"] for item in search.json()["items"]] == [first["id"]]

    renamed_payload = asset_payload(refs, "Renamed computer")
    renamed = asset_client.put(f"/api/v1/assets/{first['id']}", json=renamed_payload)
    assert renamed.status_code == 200
    assert renamed.json()["jarvis_code"] == first["jarvis_code"]

    attempted_override = {**renamed_payload, "jarvis_code": "MANUAL-999"}
    override_response = asset_client.put(f"/api/v1/assets/{first['id']}", json=attempted_override)
    assert override_response.status_code == 422
    assert asset_client.delete(f"/api/v1/assets/{first['id']}").status_code == 204
    archived = asset_client.get(
        "/api/v1/assets", params={"include_deleted": "true", "search": first["jarvis_code"]}
    ).json()["items"][0]
    assert archived["id"] == first["id"]
    assert archived["jarvis_code"] == first["jarvis_code"]


def test_parallel_asset_code_allocation_is_unique(tmp_path: Path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'parallel-codes.sqlite3'}",
        connect_args={"check_same_thread": False, "timeout": 15},
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        asset_type = AssetTypeService(session).create(payload=AssetTypeWrite(name="Sensor"))
        asset_type_id = asset_type.id

    barrier = Barrier(4)

    def add_asset(index: int) -> str:
        with Session(engine) as session:
            barrier.wait()
            created = AssetService(session).create(
                AssetWrite(name=f"Sensor {index}", asset_type_id=asset_type_id)
            )
            return created.jarvis_code

    with ThreadPoolExecutor(max_workers=4) as executor:
        codes = list(executor.map(add_asset, range(4)))

    assert len(set(codes)) == 4
    assert sorted(int(code.rsplit("-", 1)[1]) for code in codes) == [1, 2, 3, 4]


def test_sqlite_enforces_foreign_keys_and_unique_asset_constraints(tmp_path: Path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'constraints.sqlite3'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1

    with Session(engine) as session:
        invalid = Asset(
            name="Invalid",
            jarvis_code="INV-001",
            asset_type_id=uuid4(),
        )
        session.add(invalid)
        with pytest.raises(IntegrityError):
            session.commit()

    asset_type_id = uuid4()
    with Session(engine) as session:
        session.add(AssetType(id=asset_type_id, name="Computer", code_prefix="COM"))
        session.commit()
        session.add_all(
            [
                Asset(name="One", jarvis_code="COM-001", asset_type_id=asset_type_id),
                Asset(name="Two", jarvis_code="COM-001", asset_type_id=asset_type_id),
            ]
        )
        with pytest.raises(IntegrityError):
            session.commit()

    with Session(engine) as session:
        session.add_all(
            [
                Label(name="Warranty", normalized_name="warranty"),
                Label(name=" warranty ", normalized_name="warranty"),
            ]
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_product_type_must_match_asset_type_and_existing_assets(
    asset_client: TestClient,
) -> None:
    computer = create(asset_client, "asset-types", {"name": "Computer"})
    appliance = create(asset_client, "asset-types", {"name": "Appliance"})
    product = create(
        asset_client,
        "products",
        {"name": "Desktop", "asset_type_id": computer["id"]},
    )
    payload = {
        "name": "Mismatched asset",
        "asset_type_id": appliance["id"],
        "product_id": product["id"],
    }

    mismatch = asset_client.post("/api/v1/assets", json=payload)
    assert mismatch.status_code == 422
    assert "does not match" in mismatch.text

    valid = create(
        asset_client,
        "assets",
        {**payload, "name": "Valid asset", "asset_type_id": computer["id"]},
    )
    product_update = asset_client.put(
        f"/api/v1/products/{product['id']}",
        json={"name": "Desktop", "asset_type_id": appliance["id"]},
    )
    assert valid["product_id"] == product["id"]
    assert product_update.status_code == 422
    assert "conflicts with an active asset" in product_update.text
    stored_product = asset_client.get(f"/api/v1/products/{product['id']}").json()
    assert stored_product["asset_type_id"] == computer["id"]


def test_replacement_workflow_preserves_history_and_is_immutable(asset_client: TestClient) -> None:
    refs = asset_references(asset_client)
    original = create(asset_client, "assets", asset_payload(refs, "Old computer"))
    response = asset_client.post(
        f"/api/v1/assets/{original['id']}/replacement",
        json={
            "replacement": asset_payload(refs, "New computer"),
            "reason": "Hardware refresh",
        },
    )

    assert response.status_code == 201, response.text
    result = response.json()
    assert result["archived"]["id"] == original["id"]
    assert result["archived"]["name"] == "Old computer"
    assert result["archived"]["jarvis_code"] == original["jarvis_code"]
    assert result["archived"]["status"] == "retired"
    assert result["replacement"]["id"] != original["id"]
    assert result["replacement"]["jarvis_code"] != original["jarvis_code"]
    relationship = result["relationship"]
    assert relationship["source_asset_id"] == original["id"]
    assert relationship["target_asset_id"] == result["replacement"]["id"]
    assert relationship["relationship_type"] == "replaced_by"
    assert relationship["description"] == "Hardware refresh"

    mutation = {
        "source_asset_id": original["id"],
        "target_asset_id": result["replacement"]["id"],
        "relationship_type": "depends_on",
    }
    assert (
        asset_client.put(f"/api/v1/relationships/{relationship['id']}", json=mutation).status_code
        == 409
    )
    assert asset_client.delete(f"/api/v1/relationships/{relationship['id']}").status_code == 409
    immutable_update = asset_client.put(
        f"/api/v1/assets/{original['id']}", json=asset_payload(refs, "Changed old asset")
    )
    assert immutable_update.status_code == 409
    assert asset_client.delete(f"/api/v1/assets/{original['id']}").status_code == 409
    assert (
        asset_client.post(
            f"/api/v1/assets/{original['id']}/replacement",
            json={"replacement": asset_payload(refs, "Another computer")},
        ).status_code
        == 409
    )
    assert (
        asset_client.post(
            "/api/v1/relationships",
            json={**mutation, "relationship_type": "replaced_by"},
        ).status_code
        == 409
    )


def test_soft_deleted_references_keep_historical_assets_readable(
    asset_client: TestClient,
) -> None:
    refs = asset_references(asset_client)
    asset = create(asset_client, "assets", asset_payload(refs))
    for endpoint, key in (
        ("labels", "label"),
        ("products", "product"),
        ("asset-types", "asset_type"),
    ):
        assert asset_client.delete(f"/api/v1/{endpoint}/{refs[key]['id']}").status_code == 204

    historical = asset_client.get(f"/api/v1/assets/{asset['id']}")
    rejected_assignment = asset_client.post(
        "/api/v1/assets", json=asset_payload(refs, "Invalid new assignment")
    )
    assert historical.status_code == 200
    assert historical.json()["asset_type"]["name"] == "Computer"
    assert historical.json()["product"]["name"] == "Workstation"
    assert historical.json()["location"]["name"] == "Office"
    assert historical.json()["labels"][0]["name"] == "Important"
    assert rejected_assignment.status_code == 422


def test_normalized_label_names_are_unique(asset_client: TestClient) -> None:
    create(asset_client, "labels", {"name": "Warranty", "color": "#336699"})
    duplicate = asset_client.post("/api/v1/labels", json={"name": " warranty ", "color": "#993333"})
    assert duplicate.status_code == 409


def test_asset_duplicate_and_series_leave_unique_fields_unset(asset_client: TestClient) -> None:
    refs = asset_references(asset_client)
    source = create(asset_client, "assets", asset_payload(refs, "Sicherung"))

    duplicate = asset_client.post(
        f"/api/v1/assets/{source['id']}/duplicate",
        json={
            "name": "Sicherung Kopie",
            "copy_location": True,
            "copy_labels": True,
            "copy_electrical_role": False,
        },
    )
    assert duplicate.status_code == 201, duplicate.text
    duplicate_body = duplicate.json()
    assert duplicate_body["name"] == "Sicherung Kopie"
    assert duplicate_body["serial_number"] is None
    assert duplicate_body["inventory_number"] is None
    assert duplicate_body["product_id"] == source["product_id"]
    assert duplicate_body["location_id"] == source["location_id"]
    assert [item["id"] for item in duplicate_body["labels"]] == [refs["label"]["id"]]
    assert duplicate_body["jarvis_code"] != source["jarvis_code"]

    series = asset_client.post(
        f"/api/v1/assets/{source['id']}/series",
        json={
            "count": 3,
            "start_number": 1,
            "name_template": "Sicherung {n:02}",
            "copy_location": True,
            "copy_labels": True,
            "copy_electrical_role": False,
            "place_sequentially": False,
        },
    )
    assert series.status_code == 201, series.text
    body = series.json()
    assert body["created_count"] == 3
    assert [item["name"] for item in body["items"]] == [
        "Sicherung 01",
        "Sicherung 02",
        "Sicherung 03",
    ]
    assert all(item["serial_number"] is None for item in body["items"])
    assert all(item["inventory_number"] is None for item in body["items"])
