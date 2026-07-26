import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from sqlmodel import Session, SQLModel, create_engine

from app.core.restore_pending import apply_pending_restore
from app.core.settings import settings
from app.models.integration_setting import IntegrationSetting
from app.schemas.backups import BackupScheduleRead, BackupScheduleWrite
from app.services.backup_schedule import BackupScheduler, BackupScheduleStore
from app.services.backups import BackupService


def create_database(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE sample (value TEXT NOT NULL)")
        connection.execute("INSERT INTO sample (value) VALUES (?)", (value,))
        connection.commit()
    finally:
        connection.close()


def read_value(path: Path) -> str:
    connection = sqlite3.connect(path)
    try:
        row = connection.execute("SELECT value FROM sample").fetchone()
    finally:
        connection.close()
    assert row is not None
    return str(row[0])


def empty_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def nextcloud_session() -> Session:
    session = empty_session()
    session.add(
        IntegrationSetting(
            kind="nextcloud",
            enabled=True,
            base_url="https://nextcloud.local",
            account="backup-user",
            secret="app-password",
        )
    )
    session.commit()
    return session


def test_create_validate_schedule_and_apply_restore(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    create_database(settings.database_path, "before")
    service = BackupService(empty_session())

    record = service.create_backup()

    assert record.filename.startswith("tectoryn-backup-")
    assert service.validate_backup(record.filename).sha256 == record.sha256
    connection = sqlite3.connect(settings.database_path)
    try:
        connection.execute("UPDATE sample SET value = 'after'")
        connection.commit()
    finally:
        connection.close()

    service.schedule_restore(record.filename)
    assert (tmp_path / "restore" / "pending.json").is_file()
    assert apply_pending_restore() is True
    assert read_value(settings.database_path) == "before"
    assert list((tmp_path / "backups" / "pre-restore").glob("*.sqlite3"))
    assert apply_pending_restore() is False


def test_nextcloud_upload_creates_folders_and_puts_archive(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    create_database(settings.database_path, "upload")
    session = nextcloud_session()
    requests: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append((request.method, request.url.path))
        assert request.headers["authorization"].startswith("Basic ")
        if request.method == "MKCOL":
            return httpx.Response(201)
        assert request.method == "PUT"
        assert len(request.content) > 0
        return httpx.Response(201)

    service = BackupService(session, transport=httpx.MockTransport(handler))
    record = service.create_backup(
        upload_to_nextcloud=True,
        nextcloud_folder="Tectoryn/Backups",
    )

    assert record.nextcloud_uploaded is True
    assert requests[0] == (
        "MKCOL",
        "/remote.php/dav/files/backup-user/Tectoryn",
    )
    assert requests[1] == (
        "MKCOL",
        "/remote.php/dav/files/backup-user/Tectoryn/Backups",
    )
    assert requests[2][0] == "PUT"
    assert requests[2][1].endswith(record.filename)


def test_nextcloud_list_import_and_delete(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    create_database(settings.database_path, "remote")
    session = nextcloud_session()
    local_service = BackupService(session)
    created = local_service.create_backup()
    archive_path = local_service.archive_path(created.filename)
    archive_bytes = archive_path.read_bytes()
    archive_path.unlink()
    requests: list[tuple[str, str]] = []

    multistatus = f"""<?xml version="1.0" encoding="utf-8"?>
<d:multistatus xmlns:d="DAV:">
  <d:response>
    <d:href>/remote.php/dav/files/backup-user/Tectoryn/Backups/</d:href>
    <d:propstat><d:prop><d:resourcetype><d:collection/></d:resourcetype></d:prop></d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/backup-user/Tectoryn/Backups/{created.filename}</d:href>
    <d:propstat><d:prop>
      <d:resourcetype/>
      <d:getcontentlength>{len(archive_bytes)}</d:getcontentlength>
      <d:getlastmodified>Tue, 21 Jul 2026 12:00:00 GMT</d:getlastmodified>
    </d:prop></d:propstat>
  </d:response>
</d:multistatus>"""

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append((request.method, request.url.path))
        assert request.headers["authorization"].startswith("Basic ")
        if request.method == "PROPFIND":
            assert request.headers["depth"] == "1"
            return httpx.Response(207, content=multistatus.encode())
        if request.method == "GET":
            return httpx.Response(
                200,
                content=archive_bytes,
                headers={"Content-Length": str(len(archive_bytes))},
            )
        if request.method == "DELETE":
            return httpx.Response(204)
        raise AssertionError(f"Unexpected WebDAV method: {request.method}")

    service = BackupService(session, transport=httpx.MockTransport(handler))
    remote = service.list_nextcloud_backups("Tectoryn/Backups")
    assert len(remote) == 1
    assert remote[0].filename == created.filename
    assert remote[0].size_bytes == len(archive_bytes)
    assert remote[0].local_available is False

    imported = service.import_from_nextcloud(created.filename, "Tectoryn/Backups")
    assert imported.filename == created.filename
    assert service.validate_backup(created.filename).sha256 == imported.sha256
    assert service.list_nextcloud_backups("Tectoryn/Backups")[0].local_available is True

    service.delete_from_nextcloud(created.filename, "Tectoryn/Backups")
    assert ("DELETE", requests[-1][1]) == requests[-1]
    assert requests[-1][1].endswith(created.filename)


def test_schedule_store_preserves_run_state(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    store = BackupScheduleStore()
    configured = store.write(
        BackupScheduleWrite(
            enabled=True,
            interval_hours=168,
            retention_count=5,
            upload_to_nextcloud=False,
            nextcloud_folder="Tectoryn/Backups",
        )
    )
    assert configured.enabled is True
    assert configured.interval_hours == 168
    assert store.read().retention_count == 5

    succeeded = store.mark_result(success=True)
    assert succeeded.last_attempt_at is not None
    assert succeeded.last_success_at is not None
    assert succeeded.last_error is None

    changed = store.write(
        BackupScheduleWrite(
            enabled=False,
            interval_hours=24,
            retention_count=3,
            upload_to_nextcloud=False,
            nextcloud_folder="Backups",
        )
    )
    assert changed.last_success_at == succeeded.last_success_at
    assert changed.retention_count == 3


def test_schedule_due_calculation() -> None:
    now = datetime.now(UTC)
    due = BackupScheduleRead(
        enabled=True,
        interval_hours=24,
        retention_count=10,
        upload_to_nextcloud=False,
        nextcloud_folder="Backups",
        last_attempt_at=now - timedelta(hours=25),
    )
    not_due = due.model_copy(update={"last_attempt_at": now - timedelta(hours=1)})

    assert BackupScheduler._is_due(due) is True
    assert BackupScheduler._is_due(not_due) is False
