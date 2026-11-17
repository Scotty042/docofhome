import csv
import io
from datetime import UTC, datetime

import pytest
import test_release_1718 as release_tests
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.v1.time_exports import router
from app.core.restore_pending import apply_pending_restore
from app.core.settings import settings
from app.db.session import get_session
from app.models.time_tracking import WorkInterval
from app.services.backups import BackupError, BackupService
from app.services.time_exports import TimeExportService, TimeExportWrite

database = release_tests.database
NOW = datetime(2026, 11, 17, 12, tzinfo=UTC)


def at(value):
    return datetime.fromisoformat(value).timestamp()


def add(
    session,
    ticket="T-1",
    start="2026-10-10T08:00:00+02:00",
    end="2026-10-10T09:00:00+02:00",
    **extra,
):
    row = WorkInterval(
        ticket=ticket,
        customer="Kunde",
        info="Info",
        started_at=at(start),
        ended_at=at(end) if end else None,
        running=end is None,
        completed=end is not None,
        **extra,
    )
    session.add(row)
    session.commit()
    return row


def service(session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    return TimeExportService(session)


def read_csv(path):
    return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig")), delimiter=";"))


def test_disabled_by_default_and_monthly_idempotency(session, tmp_path, monkeypatch):
    export = service(session, tmp_path, monkeypatch)
    row = add(session)
    assert not export.run_once(now=NOW).enabled
    assert not export.root.exists()
    export.write(TimeExportWrite(enabled=True), now=NOW)
    assert export.run_once(now=NOW).last_exported_month == "2026-10"
    path = export.download("docofhome-zeiten-2026-10.csv")
    original = path.read_bytes()
    assert original.startswith(b"\xef\xbb\xbf")
    row.ended_at += 1800
    session.add(row)
    session.commit()
    export.run_once(now=NOW)
    assert path.read_bytes() == original
    export.run_once(force=True, now=NOW)
    assert read_csv(path)[0]["Dauer"] == "01:30:00"
    assert export.files()[0]["month"] == "2026-10"


def test_month_boundaries_timezone_bcs_and_formula_safety(session, tmp_path, monkeypatch):
    export = service(session, tmp_path, monkeypatch)
    row = add(
        session,
        ticket="=SUM(1;2)",
        start="2026-09-30T23:00:00+02:00",
        end="2026-10-01T01:00:00+02:00",
        bcs=True,
    )
    add(session, ticket="T-2", start="2026-10-31T23:30:00+01:00", end="2026-11-01T00:30:00+01:00")
    path = export.create("2026-10")
    rows = read_csv(path)
    assert len(rows) == 2
    assert rows[0]["Tätigkeit/Ticketnr"].startswith("'=")
    assert rows[0]["Anfang"] == "2026-10-01T00:00:00+02:00"
    assert rows[0]["DauerSekunden"] == "3600" and rows[0]["BCS"] == "1"
    assert rows[1]["DauerSekunden"] == "1800"
    session.refresh(row)
    assert row.started_at == at("2026-09-30T23:00:00+02:00")


def test_catch_up_after_downtime_and_disable(session, tmp_path, monkeypatch):
    export = service(session, tmp_path, monkeypatch)
    export.write(TimeExportWrite(enabled=True), now=NOW)
    later = datetime(2027, 1, 5, tzinfo=UTC)
    assert export.run_once(now=later).last_exported_month == "2026-12"
    assert [file["month"] for file in export.files()] == ["2026-12", "2026-11", "2026-10"]
    export.write(TimeExportWrite(enabled=False), now=later)
    export.run_once(now=datetime(2027, 2, 1, tzinfo=UTC))
    assert len(export.files()) == 3


def test_nextcloud_failure_keeps_local_csv_and_retries_same_snapshot(
    session, tmp_path, monkeypatch
):
    export = service(session, tmp_path, monkeypatch)
    row = add(session)
    export.write(TimeExportWrite(enabled=True, upload_to_nextcloud=True), now=NOW)
    attempts = []

    def upload(self, path, folder):
        attempts.append(path.read_bytes())
        if len(attempts) == 1:
            raise BackupError("Nextcloud upload failed (403)")

    monkeypatch.setattr(BackupService, "upload_to_nextcloud", upload)
    failed = export.run_once(now=NOW)
    assert "403" in failed.last_error and failed.last_exported_month is None
    assert len(export.files()) == 1
    row.ended_at += 60
    session.add(row)
    session.commit()
    assert export.run_once(now=NOW).last_exported_month == "2026-10"
    assert attempts[0] == attempts[1]


def test_api_configuration_run_download_and_unsafe_paths(session, tmp_path, monkeypatch):
    service(session, tmp_path, monkeypatch)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as client:
        assert not client.get("/time-exports").json()["configuration"]["enabled"]
        assert client.put("/time-exports/configuration", json={"enabled": True}).status_code == 200
        assert client.post("/time-exports/run").status_code == 200
        files = client.get("/time-exports").json()["files"]
        response = client.get(f"/time-exports/{files[0]['filename']}/download")
        assert response.status_code == 200 and "text/csv" in response.headers["content-type"]
        assert client.get("/time-exports/config.json/download").status_code == 404
        assert (
            client.put(
                "/time-exports/configuration", json={"nextcloud_folder": "../bad"}
            ).status_code
            == 422
        )
    with pytest.raises(ValidationError):
        TimeExportWrite(nextcloud_folder="../bad")


def test_export_files_and_configuration_survive_full_backup(database, tmp_path, monkeypatch):
    session, _ = database
    export = TimeExportService(session)
    add(session, bcs=True)
    export.write(TimeExportWrite(enabled=True), now=NOW)
    export.run_once(now=NOW)
    original_csv = export.download("docofhome-zeiten-2026-10.csv").read_bytes()
    backup = BackupService(session)
    record = backup.create_backup()
    content = backup.archive_path(record.filename).read_bytes()
    monkeypatch.setattr(settings, "data_dir", tmp_path / "restored")
    target = BackupService(session)
    imported = target.import_backup(content)
    target.schedule_restore(imported.filename)
    assert apply_pending_restore()
    restored = TimeExportService(session)
    assert restored.read().enabled
    assert restored.read().last_exported_month == "2026-10"
    assert restored.download("docofhome-zeiten-2026-10.csv").read_bytes() == original_csv


def test_restore_of_older_backup_disables_later_export_job(database):
    session, _ = database
    backup = BackupService(session)
    record = backup.create_backup()
    content = backup.archive_path(record.filename).read_bytes()
    export = TimeExportService(session)
    export.write(TimeExportWrite(enabled=True), now=NOW)
    assert export.read().enabled
    imported = backup.import_backup(content)
    backup.schedule_restore(imported.filename)
    assert apply_pending_restore()
    assert not export.read().enabled
    assert list(
        (settings.data_dir / "backups/pre-restore").glob("*/exports/time-tracking/config.json")
    )


def test_export_uses_installation_timezone_at_month_boundary(session, tmp_path, monkeypatch):
    from app.models.application_setting import ApplicationSetting

    export = service(session, tmp_path, monkeypatch)
    session.add(ApplicationSetting(id=1, installation_name="Test", timezone="America/Los_Angeles"))
    session.commit()
    utc_november = datetime(2026, 11, 1, 0, tzinfo=UTC)
    export.write(TimeExportWrite(enabled=True), now=utc_november)
    assert export.run_once(now=utc_november).last_exported_month == "2026-09"
    assert (
        export.run_once(now=datetime(2026, 11, 1, 9, tzinfo=UTC)).last_exported_month == "2026-10"
    )
