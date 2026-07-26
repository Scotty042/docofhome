import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.core.settings import settings
from app.db.session import get_session
from app.main import app


@pytest.fixture
def backup_client(tmp_path: Path, monkeypatch) -> Generator[TestClient]:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(settings.database_path)
    try:
        source.execute("CREATE TABLE sample (value TEXT NOT NULL)")
        source.execute("INSERT INTO sample VALUES ('api')")
        source.commit()
    finally:
        source.close()

    test_engine = create_engine(
        f"sqlite:///{tmp_path / 'api.sqlite3'}",
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


def create_backup(backup_client: TestClient) -> str:
    created = backup_client.post(
        "/api/v1/backups",
        json={
            "upload_to_nextcloud": False,
            "nextcloud_folder": "Tectoryn/Backups",
        },
    )
    assert created.status_code == 201
    return str(created.json()["filename"])


def test_backup_api_creates_validates_and_schedules_restore(
    backup_client: TestClient,
    tmp_path: Path,
) -> None:
    filename = create_backup(backup_client)

    listed = backup_client.get("/api/v1/backups")
    assert listed.status_code == 200
    assert listed.json()["items"][0]["filename"] == filename

    validated = backup_client.post(f"/api/v1/backups/{filename}/validate")
    assert validated.status_code == 200
    assert validated.json()["valid"] is True

    rejected = backup_client.post(
        f"/api/v1/backups/{filename}/restore",
        json={"confirmation": "restore"},
    )
    assert rejected.status_code == 422

    accepted = backup_client.post(
        f"/api/v1/backups/{filename}/restore",
        json={"confirmation": "WIEDERHERSTELLEN"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["restart_required"] is True
    assert (tmp_path / "restore" / "pending.json").is_file()

    delete_pending = backup_client.delete(f"/api/v1/backups/{filename}")
    assert delete_pending.status_code == 409


def test_backup_download_delete_and_import_roundtrip(backup_client: TestClient) -> None:
    filename = create_backup(backup_client)

    downloaded = backup_client.get(f"/api/v1/backups/{filename}/download")
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"] == "application/zip"
    assert downloaded.content.startswith(b"PK")

    deleted = backup_client.delete(f"/api/v1/backups/{filename}")
    assert deleted.status_code == 204
    assert backup_client.get("/api/v1/backups").json()["items"] == []

    imported = backup_client.post(
        "/api/v1/backups/import",
        content=downloaded.content,
        headers={"Content-Type": "application/zip"},
    )
    assert imported.status_code == 201
    imported_filename = imported.json()["filename"]
    assert imported_filename != filename
    assert (
        backup_client.post(f"/api/v1/backups/{imported_filename}/validate").json()["valid"] is True
    )


def test_backup_import_rejects_invalid_content(backup_client: TestClient) -> None:
    wrong_type = backup_client.post(
        "/api/v1/backups/import",
        content=b"not a backup",
        headers={"Content-Type": "text/plain"},
    )
    assert wrong_type.status_code == 415

    invalid_zip = backup_client.post(
        "/api/v1/backups/import",
        content=b"PK-not-a-valid-zip",
        headers={"Content-Type": "application/zip"},
    )
    assert invalid_zip.status_code == 422
    assert backup_client.get("/api/v1/backups").json()["items"] == []


def test_backup_schedule_api_persists_configuration(backup_client: TestClient) -> None:
    response = backup_client.put(
        "/api/v1/backups/schedule",
        json={
            "enabled": True,
            "interval_hours": 168,
            "retention_count": 7,
            "upload_to_nextcloud": False,
            "nextcloud_folder": "Tectoryn/Backups",
        },
    )
    assert response.status_code == 200
    assert response.json()["enabled"] is True
    assert response.json()["retention_count"] == 7

    stored = backup_client.get("/api/v1/backups/schedule")
    assert stored.status_code == 200
    assert stored.json()["interval_hours"] == 168
