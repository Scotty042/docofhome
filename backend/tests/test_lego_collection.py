import json
import sqlite3
from decimal import Decimal
from uuid import uuid4

import pytest
import test_release_1718 as release_tests
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlmodel import Session, SQLModel, create_engine, select

from app.core.restore_pending import apply_pending_restore
from app.core.settings import settings
from app.main import app
from app.models.lego import LegoSet
from app.schemas.lego import LegoSetWrite
from app.schemas.mcp import McpSettingsWrite
from app.services.backups import BackupService
from app.services.lego import LegoConflictError, LegoService
from app.services.mcp_settings import McpSettingsService
from app.services.release import PortabilityService, ReleaseConflictError

call = release_tests.call


@pytest.fixture
def database(tmp_path, monkeypatch):
    yield from release_tests.database.__wrapped__(tmp_path, monkeypatch)


def test_normalization_duplicate_and_precise_dashboard(session):
    service = LegoService(session)
    first = service.save(
        LegoSetWrite(
            set_number=" 010305-1 ", name=" Castle ", parts_count=4514, purchase_price="249.99"
        )
    )
    assert first.set_number == "10305" and first.name == "Castle"
    with pytest.raises(LegoConflictError):
        service.save(LegoSetWrite(set_number="10305", name="Duplicate"))
    service.save(
        LegoSetWrite(set_number="21338", name="Cabin", purchase_price="0.00", parts_count=0)
    )
    service.save(LegoSetWrite(set_number="10313", name="Flowers"))
    totals = service.dashboard()
    assert totals.sets_count == 3 and totals.purchase_total == Decimal("249.99")
    assert totals.parts_total == 4514
    assert totals.missing_prices == totals.missing_parts == 1
    assert service.search(set_number="10305-1")["items"][0]["id"] == str(first.id)


@pytest.mark.parametrize(
    "fields",
    [
        {"name": " "},
        {"parts_count": -1},
        {"purchase_price": "1.001"},
        {"width_cm": 0},
        {"width_cm": float("nan")},
        {"source_url": "javascript:alert(1)"},
        {"set_number": "abc"},
    ],
)
def test_invalid_data(fields):
    with pytest.raises(ValidationError):
        LegoSetWrite.model_validate({"set_number": "10305", "name": "Castle", **fields})


def test_search_pagination_and_update_collision(session):
    service = LegoService(session)
    for n in range(103):
        service.save(LegoSetWrite(set_number=str(90000 + n), name=f"Set {n:03}"))
    page = service.search(limit=100)
    assert page["total"] == 103 and page["next_offset"] == 100
    assert len(service.search(offset=100)["items"]) == 3
    first, second = page["items"][:2]
    from uuid import UUID

    with pytest.raises(LegoConflictError):
        service.save(
            LegoSetWrite(set_number=second["set_number"], name="Conflict"), UUID(first["id"])
        )


def test_mcp_real_transport_partial_update_permissions(database):
    session, token = database
    with TestClient(app) as client:
        assert (
            call(client, token, "search_lego_sets", {"set_number": "10305"}, path=True)["total"]
            == 0
        )
        saved = call(
            client,
            token,
            "save_lego_set",
            {
                "data": {
                    "set_number": "10305",
                    "name": "Castle",
                    "purchase_price": "199.99",
                    "parts_count": 4514,
                    "width_cm": 44,
                    "source_url": "https://example.org/set",
                }
            },
        )["item"]
        changed = call(
            client,
            token,
            "save_lego_set",
            {"set_id": saved["id"], "data": {"storage_note": "Box 3"}},
            path=True,
        )["item"]
        assert changed["name"] == "Castle" and changed["purchase_price"] == "199.99"
        assert changed["width_cm"] == 44 and changed["storage_note"] == "Box 3"
        assert call(client, token, "get_lego_set", {"set_id": saved["id"]})["parts_count"] == 4514
        assert call(client, token, "get_lego_dashboard", {})["sets_count"] == 1
        McpSettingsService(session).update(McpSettingsWrite(enabled=True, permission="read"))
        denied = client.post(
            f"/mcp/{token}",
            headers={"Accept": "application/json, text/event-stream"},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "save_lego_set",
                    "arguments": {"data": {"set_number": "10313", "name": "Denied"}},
                },
            },
        )
        assert denied.json()["result"]["isError"]
        McpSettingsService(session).update(McpSettingsWrite(enabled=True, permission="admin"))
        call(client, token, "delete_lego_set", {"set_id": saved["id"]})
        assert call(client, token, "get_lego_dashboard", {})["sets_count"] == 0


def test_rest_validation_duplicate_update_delete(database):
    with TestClient(app) as client:
        saved = client.post("/api/v1/lego/sets", json={"set_number": "10305", "name": "Castle"})
        assert saved.status_code == 201
        set_id = saved.json()["id"]
        assert (
            client.post(
                "/api/v1/lego/sets", json={"set_number": "10305-1", "name": "Duplicate"}
            ).status_code
            == 409
        )
        assert (
            client.post(
                "/api/v1/lego/sets", json={"set_number": "10313", "name": " ", "height_cm": -1}
            ).status_code
            == 422
        )
        assert client.get("/api/v1/lego/sets?set_number=10305-1").json()["total"] == 1
        assert (
            client.put(
                f"/api/v1/lego/sets/{set_id}",
                json={
                    "set_number": "10305",
                    "name": "New",
                    "image_url": "/api/v1/products/images/test.webp",
                },
            ).status_code
            == 200
        )
        assert client.delete(f"/api/v1/lego/sets/{set_id}").status_code == 204
        assert client.get(f"/api/v1/lego/sets/{set_id}").status_code == 404


def test_json_csv_roundtrip_and_number_conflict(session):
    service = LegoService(session)
    service.save(
        LegoSetWrite(
            set_number="10305",
            name="Castle",
            purchase_price="123.45",
            width_cm=44,
            notes="My notes",
        )
    )
    export = PortabilityService(session)
    content = json.dumps(export.export_payload()).encode()
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as fresh:
        target = PortabilityService(fresh)
        assert target.apply(content, strategy="fail").created == 1
        row = LegoService(fresh).search()["items"][0]
        assert row["purchase_price"] == "123.45" and row["width_cm"] == 44
        payload = json.loads(content)
        payload["data"]["lego_sets"][0]["id"] = str(uuid4())
        duplicate = json.dumps(payload).encode()
        assert target.preview(duplicate).conflicts
        assert target.apply(duplicate, strategy="skip").skipped == 1
        with pytest.raises(ReleaseConflictError):
            target.apply(duplicate, strategy="fail")
    with Session(engine) as fresh:
        for row in fresh.exec(select(LegoSet)).all():
            fresh.delete(row)
        fresh.commit()
        assert (
            PortabilityService(fresh)
            .apply(export.csv_export("lego_sets").encode(), strategy="fail")
            .created
            == 1
        )
        assert LegoService(fresh).dashboard().purchase_total == Decimal("123.45")


def test_full_backup_restore_preserves_lego_and_local_image(database, tmp_path, monkeypatch):
    session, _ = database
    image = tmp_path / "uploads/product-images/lego.webp"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"test image bytes")
    LegoService(session).save(
        LegoSetWrite(
            set_number="10305",
            name="Castle",
            image_url="/api/v1/products/images/lego.webp",
            height_cm=27,
        )
    )
    service = BackupService(session)
    backup = service.create_backup()
    content = service.archive_path(backup.filename).read_bytes()
    fresh = tmp_path / "restored"
    monkeypatch.setattr(settings, "data_dir", fresh)
    target = BackupService(session)
    imported = target.import_backup(content)
    target.schedule_restore(imported.filename)
    assert apply_pending_restore()
    with sqlite3.connect(settings.database_path) as connection:
        assert connection.execute("SELECT set_number,height_cm FROM lego_sets").fetchone() == (
            "10305",
            27,
        )
    assert (fresh / "uploads/product-images/lego.webp").read_bytes() == image.read_bytes()


def test_migration_keeps_existing_module_choices_and_supports_downgrade(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = Config("alembic.ini")
    command.upgrade(config, "0058")
    with sqlite3.connect(settings.database_path) as connection:
        connection.execute(
            "INSERT INTO application_settings "
            "(id,installation_name,language,timezone,theme,enabled_modules_json,"
            "main_menu_modules_json,online_product_image_search_enabled,"
            "product_image_source_wikimedia_enabled,product_image_source_duckduckgo_enabled,"
            "created_at,updated_at) VALUES "
            "(1,'Home','de','Europe/Berlin','dark','[\"assets\"]','[]',0,0,0,"
            "CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
        )
    command.upgrade(config, "head")
    with sqlite3.connect(settings.database_path) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "0059"
        row = connection.execute(
            "SELECT enabled_modules_json,main_menu_modules_json FROM application_settings"
        ).fetchone()
        assert json.loads(row[0]) == ["assets", "lego"] and json.loads(row[1]) == ["lego"]
    command.downgrade(config, "0058")
    with sqlite3.connect(settings.database_path) as connection:
        assert connection.execute(
            "SELECT enabled_modules_json,main_menu_modules_json FROM application_settings"
        ).fetchone() == ('["assets"]', "[]")
    command.upgrade(config, "head")
