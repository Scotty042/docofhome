import json
import sqlite3
from io import BytesIO
from zipfile import ZipFile

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

from app import mcp_server as mcp
from app.core.restore_pending import apply_pending_restore
from app.core.settings import settings
from app.db.session import get_session
from app.main import app
from app.models.integration_setting import IntegrationSetting
from app.models.recipe import Recipe
from app.models.work import WorkItemEvent, WorkItemEventAttachment, WorkItemEventPaperlessLink
from app.schemas.mcp import McpSettingsWrite
from app.schemas.settings import IntegrationWrite
from app.schemas.work import WorkItemWrite, WorkSubjectWrite
from app.services.backups import BackupError, BackupService
from app.services.integration_checks import IntegrationCheckService
from app.services.mcp_settings import McpSettingsService
from app.services.release import EXPORT_MODELS, PortabilityService
from app.services.work import WorkService


@pytest.fixture
def database(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    settings.database_path.parent.mkdir(parents=True)
    engine = create_engine(
        f"sqlite:///{settings.database_path}", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(mcp, "engine", engine)

    def sessions():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = sessions
    with Session(engine) as session:
        service = McpSettingsService(session)
        token = service.rotate_token().token
        service.update(McpSettingsWrite(enabled=True, permission="admin"))
        yield session, token
    app.dependency_overrides.clear()
    engine.dispose()


def call(client, token, name, arguments, path=False):
    headers = {"Accept": "application/json, text/event-stream"}
    if not path:
        headers["Authorization"] = f"Bearer {token}"
    response = client.post(
        f"/mcp/{token}" if path else "/mcp",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "error" not in body
    assert not body["result"].get("isError"), body
    return body["result"].get("structuredContent") or json.loads(
        body["result"]["content"][0]["text"]
    )


def test_mcp_auth_and_tool_inventory_survive_repeated_lifespans(database):
    session, token = database
    headers = {"Accept": "application/json, text/event-stream"}
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    for _ in range(2):
        with TestClient(app) as client:
            assert client.post("/mcp/invalid", headers=headers, json=request).status_code == 401
            assert client.post("/mcp", headers=headers, json=request).status_code == 401
            response = client.post(f"/mcp/{token}", headers=headers, json=request)
            names = {tool["name"] for tool in response.json()["result"]["tools"]}
            assert len(names) == 49
            assert {"search_recipes", "save_recipe", "get_recipe", "delete_recipe"} <= names
            McpSettingsService(session).update(McpSettingsWrite(enabled=True, permission="read"))
            denied = client.post(
                f"/mcp/{token}",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "save_recipe",
                        "arguments": {"title": "Forbidden", "ingredients": [], "steps": []},
                    },
                },
            )
            assert denied.json()["result"]["isError"]
            assert call(client, token, "search_recipes", {})["total"] == 0


def test_mcp_preserves_profiles_kinds_and_supports_both_transports(database):
    session, token = database
    service = WorkService(session)
    subject = service.create_subject(WorkSubjectWrite(name="Auto", profile={"vin": "TEST123"}))
    activity = service.create(
        WorkItemWrite(
            title="Inspektion",
            item_type="maintenance",
            activity_kind="inspection",
            subject_id=subject.id,
        )
    )
    with TestClient(app) as client:
        call(client, token, "update_subject", {"subject_id": str(subject.id), "name": "Auto neu"})
        call(
            client,
            token,
            "update_activity",
            {"activity_id": str(activity.id), "title": "Inspektion neu"},
        )
        created = call(
            client,
            token,
            "save_recipe",
            {
                "title": "Reis",
                "ingredients": [{"name": "Reis", "amount": 100, "unit": "g"}],
                "steps": ["Kochen"],
            },
        )
        found = call(client, token, "search_recipes", {"query": "Reis"}, path=True)
        assert found["items"][0]["id"] == created["item"]["id"]
    session.expire_all()
    assert service.list_subjects()[0].profile == {"vin": "TEST123"}
    assert service.get(activity.id).activity_kind == "inspection"


def test_invalid_recipe_cannot_poison_list(database):
    session, token = database
    with TestClient(app) as client:
        for title in ("", "   ", "\t\n"):
            assert client.post("/api/v1/recipes", json={"title": title}).status_code == 422
        assert client.get("/api/v1/recipes").json() == []
        assert call(client, token, "search_recipes", {})["total"] == 0
    assert session.exec(select(Recipe)).all() == []


def test_recipe_pagination_is_complete(database):
    session, token = database
    session.add_all(Recipe(title=f"Reis {i:03}") for i in range(101))
    session.commit()
    with TestClient(app) as client:
        first = call(client, token, "search_recipes", {})
        second = call(client, token, "search_recipes", {"offset": first["next_offset"]})
    assert first["total"] == 101 and first["count"] == 100 and first["has_more"]
    assert second["count"] == 1 and second["next_offset"] is None
    assert len({x["id"] for x in first["items"] + second["items"]}) == 101


def test_full_backup_restores_images_config_and_database(database, tmp_path, monkeypatch):
    session, _ = database
    image = tmp_path / "uploads/recipe-images/test.webp"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"test image content")
    config = tmp_path / "backups/config.json"
    config.parent.mkdir()
    config.write_text('{"enabled": true, "interval_hours": 48}')
    private_key = tmp_path / "secrets/docker-ssh/test-host"
    private_key.parent.mkdir(parents=True)
    private_key.write_text("private ssh test key")
    session.add(Recipe(title="Rezept mit Bild", image_url="/api/v1/recipes/images/test.webp"))
    session.commit()
    service = BackupService(session)
    backup = service.create_backup()
    content = service.archive_path(backup.filename).read_bytes()
    with ZipFile(BytesIO(content)) as archive:
        assert json.loads(archive.read("manifest.json"))["format_version"] == 2
        assert archive.read("uploads/recipe-images/test.webp") == image.read_bytes()
        assert archive.read("secrets/docker-ssh/test-host") == private_key.read_bytes()
    fresh = tmp_path / "fresh"
    monkeypatch.setattr(settings, "data_dir", fresh)
    target = BackupService(session)
    imported = target.import_backup(content)
    target.schedule_restore(imported.filename)
    assert apply_pending_restore()
    assert (fresh / "uploads/recipe-images/test.webp").read_bytes() == image.read_bytes()
    assert (fresh / "backups/config.json").read_bytes() == config.read_bytes()
    assert (fresh / "secrets/docker-ssh/test-host").read_bytes() == private_key.read_bytes()
    assert (fresh / "secrets/docker-ssh").stat().st_mode & 0o777 == 0o700
    assert (fresh / "secrets/docker-ssh/test-host").stat().st_mode & 0o777 == 0o600
    with sqlite3.connect(settings.database_path) as conn:
        assert conn.execute("SELECT title FROM recipes").fetchone()[0] == "Rezept mit Bild"
    assert not apply_pending_restore()


def test_legacy_backup_and_tamper_detection(database):
    session, _ = database
    service = BackupService(session)
    record = service.create_backup()
    with ZipFile(service.archive_path(record.filename)) as archive:
        db = archive.read("database.sqlite3")
        manifest = json.loads(archive.read("manifest.json"))
    manifest["format_version"] = 1
    manifest.pop("files")
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("database.sqlite3", db)
    imported = service.import_backup(output.getvalue())
    service.schedule_restore(imported.filename)
    assert apply_pending_restore()
    for name, payload in (("database.sqlite3", db + b"tampered"), ("../escape", b"x")):
        bad = BytesIO()
        with ZipFile(bad, "w") as archive:
            archive.writestr("manifest.json", json.dumps(manifest))
            archive.writestr("database.sqlite3", payload if name == "database.sqlite3" else db)
            if name != "database.sqlite3":
                archive.writestr(name, payload)
        with pytest.raises(BackupError):
            service.import_backup(bad.getvalue())


def test_export_roundtrip_includes_recipes_and_binary_attachments(database, tmp_path):
    session, _ = database
    service = WorkService(session)
    item = service.create(WorkItemWrite(title="Inspektion", item_type="maintenance"))
    event = WorkItemEvent(work_item_id=item.id, event_type="completed")
    session.add(event)
    session.flush()
    session.add(
        WorkItemEventAttachment(
            event_id=event.id,
            file_name="test.pdf",
            content_type="application/pdf",
            size_bytes=4,
            content=b"\xff\x00\x80\x01",
        )
    )
    session.add(WorkItemEventPaperlessLink(event_id=event.id, document_id=42, title="Rechnung"))
    session.add(Recipe(title="Reis", ingredients_json='[{"name":"Reis"}]'))
    session.commit()
    data = PortabilityService(session).export_payload()
    assert "recipes" in data["data"]
    assert {model.__tablename__ for _, model, _ in EXPORT_MODELS} | {"integration_settings"} == set(
        SQLModel.metadata.tables
    )
    assert not any(row["is_secret"] for row in data["data"]["system_settings"])
    engine = create_engine(f"sqlite:///{tmp_path / 'import.sqlite3'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as other:
        result = PortabilityService(other).apply(json.dumps(data).encode(), strategy="fail")
        assert result.created > 0
        assert other.exec(select(Recipe)).one().title == "Reis"
        assert other.exec(select(WorkItemEventAttachment)).one().content == b"\xff\x00\x80\x01"
        assert other.exec(select(WorkItemEventPaperlessLink)).one().document_id == 42
    engine.dispose()


def test_unsaved_integration_test_reuses_secret_without_writing(database):
    session, _ = database
    stored = IntegrationSetting(
        kind="home_assistant", enabled=True, base_url="http://original.test", secret="test-secret"
    )
    session.add(stored)
    session.commit()

    def handler(request):
        assert request.url.host == "draft.test"
        assert request.headers["Authorization"] == "Bearer test-secret"
        return httpx.Response(200, json={"version": "test", "location_name": "Test"})

    result = IntegrationCheckService(session, httpx.MockTransport(handler)).check_payload(
        IntegrationWrite(kind="home_assistant", enabled=True, base_url="http://draft.test")
    )
    assert result.success
    session.refresh(stored)
    assert stored.base_url == "http://original.test" and stored.secret == "test-secret"
