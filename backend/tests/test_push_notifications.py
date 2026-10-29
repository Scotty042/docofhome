import json
import sqlite3
from datetime import UTC, date, datetime, timedelta
from urllib.parse import parse_qs

import httpx
import pytest
import test_release_1718 as release_tests
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.restore_pending import apply_pending_restore
from app.core.settings import settings
from app.main import app
from app.models.consumption import ConsumptionMeter, ConsumptionReading
from app.models.work import WorkItem
from app.schemas.notifications import PushConfig, PushWrite
from app.services.backups import BackupService
from app.services.notifications import PushError, PushService
from app.services.release import PortabilityService

NOW = datetime(2026, 10, 29, 8, tzinfo=UTC)
APP_TOKEN = "A" * 30
USER_KEY = "B" * 30
NTFY_TOKEN = "tk_private_test_token"


@pytest.fixture
def database(tmp_path, monkeypatch):
    yield from release_tests.database.__wrapped__(tmp_path, monkeypatch)


def configured(**overrides):
    return PushWrite.model_validate(
        {
            "enabled": True,
            "pushover_enabled": True,
            "ntfy_enabled": True,
            "pushover_app_token": APP_TOKEN,
            "pushover_user_key": USER_KEY,
            "ntfy_access_token": NTFY_TOKEN,
            "ntfy_url": "https://ntfy.example.test",
            "ntfy_topic": "private-reminders",
            "public_url": "https://home.example.test",
            **overrides,
        }
    )


def add_task(session, **overrides):
    row = WorkItem(
        **{"item_type": "maintenance", "title": "Filter wechseln", "due_at": NOW, **overrides}
    )
    session.add(row)
    session.commit()
    return row


def accepted(request):
    if request.url.host == "api.pushover.net":
        return httpx.Response(200, json={"status": 1})
    return httpx.Response(200, json={"id": "accepted-test-message"})


def test_default_disabled_and_secret_roundtrip_export(session):
    requests = []
    service = PushService(
        session, transport=httpx.MockTransport(lambda req: requests.append(req) or accepted(req))
    )
    assert not service.read().enabled
    assert service.run_once(now=NOW) == 0 and not requests
    stored = service.save(configured())
    public = stored.model_dump_json()
    for secret in (APP_TOKEN, USER_KEY, NTFY_TOKEN):
        assert secret not in public
    assert stored.pushover_app_token_configured and stored.ntfy_access_token_configured
    service.save(
        PushWrite.model_validate(
            {
                **PushConfig.model_validate(
                    stored.model_dump(include=PushConfig.model_fields.keys())
                ).model_dump(),
                "send_hour": 9,
            }
        )
    )
    assert service.read().pushover_app_token_configured
    exported = json.dumps(PortabilityService(session).export_payload())
    assert "private-reminders" not in exported
    for secret in (APP_TOKEN, USER_KEY, NTFY_TOKEN):
        assert secret not in exported
    service.save(configured(enabled=False, pushover_app_token=None, clear_pushover_app_token=True))
    assert not service.read().pushover_app_token_configured


def test_draft_test_both_protocols_unicode_and_no_save(session):
    requests = []
    service = PushService(
        session, transport=httpx.MockTransport(lambda req: requests.append(req) or accepted(req))
    )
    assert service.test("pushover", configured())
    assert service.test("ntfy", configured())
    assert not service.read().enabled and not service.read().pushover_app_token_configured
    pushover, ntfy = requests
    body = parse_qs(pushover.content.decode())
    assert body["token"] == [APP_TOKEN] and body["user"] == [USER_KEY]
    assert body["url"] == ["https://home.example.test/"]
    assert pushover.url == "https://api.pushover.net/1/messages.json"
    assert ntfy.headers["Authorization"] == f"Bearer {NTFY_TOKEN}"
    assert json.loads(ntfy.content)["topic"] == "private-reminders"
    assert all(row.status == "sent" for row in service.history())


def test_daily_delivery_deduplicates_across_sessions_and_both_services(session):
    requests = []
    transport = httpx.MockTransport(lambda req: requests.append(req) or accepted(req))
    add_task(session)
    service = PushService(session, transport=transport)
    service.save(configured())
    assert service.run_once(now=NOW.replace(hour=5)) == 0
    assert service.run_once(now=NOW) == 2
    assert service.run_once(now=NOW + timedelta(minutes=1)) == 0
    with Session(session.bind) as second:
        assert (
            PushService(second, transport=transport).run_once(now=NOW + timedelta(minutes=2)) == 0
        )
    assert len(requests) == 2
    assert "Filter wechseln" in parse_qs(requests[0].content.decode())["message"][0]
    assert service.run_once(now=NOW + timedelta(days=1)) == 2


def test_failures_retry_independently_and_stop_after_three(session):
    calls = []

    def response(request):
        calls.append(request.url.host)
        return (
            httpx.Response(429, text=f"SECRET {APP_TOKEN}")
            if request.url.host == "api.pushover.net"
            else accepted(request)
        )

    service = PushService(session, transport=httpx.MockTransport(response))
    add_task(session)
    service.save(configured())
    assert service.run_once(now=NOW) == 1
    assert service.run_once(now=NOW + timedelta(minutes=5)) == 0
    assert service.run_once(now=NOW + timedelta(minutes=15)) == 0
    assert service.run_once(now=NOW + timedelta(minutes=30)) == 0
    assert service.run_once(now=NOW + timedelta(minutes=60)) == 0
    assert calls.count("api.pushover.net") == 3 and calls.count("ntfy.example.test") == 1
    assert APP_TOKEN not in json.dumps([h.model_dump(mode="json") for h in service.history()])


def test_stale_claims_recover_but_active_claims_are_not_stolen(session):
    service = PushService(session)
    assert service._claim("claim-test", "ntfy", NOW) is not None
    assert service._claim("claim-test", "ntfy", NOW + timedelta(minutes=2)) is None
    assert service._claim("claim-test", "ntfy", NOW + timedelta(minutes=15)) is not None


def test_readings_categories_completion_and_duplicate_automation(session):
    meter = ConsumptionMeter(
        name="Hauptstrom",
        meter_type="electricity_grid",
        unit="kWh",
        reading_schedule_day=29,
        created_at=datetime(2026, 10, 1, tzinfo=UTC),
    )
    session.add(meter)
    session.commit()
    add_task(session)
    add_task(session, item_type="task", title="Termin")
    add_task(
        session,
        item_type="task",
        title="Keine Doppelmeldung",
        automation_key=f"meter-reading:{meter.id}:2026-10",
    )
    add_task(session, title="Erledigt", status="completed")
    add_task(session, title="Archiviert", deleted_at=NOW)
    add_task(session, title="Später", due_at=NOW + timedelta(days=20))
    service = PushService(session)
    digest = service.digest(PushConfig(), date(2026, 10, 29))
    assert digest and "3 offene Erinnerungen" in digest[0]
    assert "Hauptstrom" in digest[0] and "Termin" in digest[0]
    for absent in ("Doppelmeldung", "Erledigt", "Archiviert", "Später"):
        assert absent not in digest[0]
    only_readings = PushConfig(maintenance_enabled=False, tasks_enabled=False)
    assert service.digest(only_readings, date(2026, 10, 29))[1] == "/consumption"
    reading = ConsumptionReading(meter_id=meter.id, measured_at=NOW, value=123, source="manual")
    session.add(reading)
    session.commit()
    assert service.digest(only_readings, date(2026, 10, 29)) is None
    work_only = service.digest(PushConfig(readings_enabled=False), date(2026, 10, 29))
    assert work_only and "Hauptstrom" not in work_only[0]


def test_no_empty_messages_disabled_categories_and_bounded_digest(session):
    calls = []
    service = PushService(
        session, transport=httpx.MockTransport(lambda r: calls.append(r) or accepted(r))
    )
    service.save(configured())
    assert service.run_once(now=NOW) == 0
    for n in range(40):
        add_task(session, title=f"Wartung {n} äöü " + "a" * 120)
    message, _ = service.digest(PushConfig(), NOW.date())
    assert len(message) <= 1024 and len(message.encode()) <= 4096 and "weitere" in message
    assert (
        service.digest(
            PushConfig(readings_enabled=False, maintenance_enabled=False, tasks_enabled=False),
            NOW.date(),
        )
        is None
    )


def test_dst_repeated_hour_sends_once(session):
    service = PushService(session, transport=httpx.MockTransport(accepted))
    add_task(session, due_at=datetime(2026, 10, 25, 10, tzinfo=UTC))
    service.save(configured(ntfy_enabled=False, send_hour=2, send_minute=15))
    assert service.run_once(now=datetime(2026, 10, 25, 0, 30, tzinfo=UTC)) == 1
    assert service.run_once(now=datetime(2026, 10, 25, 1, 30, tzinfo=UTC)) == 0


@pytest.mark.parametrize("status", [302, 401, 500])
def test_remote_failure_is_sanitized_and_redirects_not_followed(session, status):
    service = PushService(
        session,
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                status, headers={"Location": "https://wrong.example.test"}, text=NTFY_TOKEN
            )
        ),
    )
    assert not service.test("ntfy", configured())
    assert NTFY_TOKEN not in json.dumps([h.model_dump(mode="json") for h in service.history()])


def test_api_secret_safe_validation_and_unsaved_test(database, monkeypatch):
    monkeypatch.setattr(PushService, "_send", lambda *args: None)
    with TestClient(app) as client:
        assert not client.get("/api/v1/settings/notifications").json()["enabled"]
        data = configured().model_dump(mode="json")
        data.update(
            pushover_app_token=APP_TOKEN, pushover_user_key=USER_KEY, ntfy_access_token=NTFY_TOKEN
        )
        assert client.post("/api/v1/settings/notifications/test/pushover", json=data).json()[
            "success"
        ]
        assert not client.get("/api/v1/settings/notifications").json()["enabled"]
        saved = client.put("/api/v1/settings/notifications", json=data)
        assert saved.status_code == 200 and APP_TOKEN not in saved.text
        bad = client.put(
            "/api/v1/settings/notifications", json={"pushover_app_token": "secret with spaces"}
        )
        assert bad.status_code == 422 and "secret with spaces" not in bad.text
        assert (
            client.post("/api/v1/settings/notifications/test/unknown", json={}).status_code == 422
        )


def test_invalid_enabled_settings(session):
    service = PushService(session)
    with pytest.raises(PushError):
        service.save(PushWrite(enabled=True))
    with pytest.raises(PushError):
        service.save(PushWrite(enabled=True, pushover_enabled=True))
    with pytest.raises(PushError):
        service.save(configured(clear_pushover_app_token=True))


@pytest.mark.parametrize("body", [[], "unexpected", None])
def test_malformed_success_responses_are_safe_failures(session, body):
    service = PushService(
        session, transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body))
    )
    assert not service.test("pushover", configured())
    assert not service.test("ntfy", configured())


def test_backup_restore_preserves_secrets_and_daily_claim(database, tmp_path, monkeypatch):
    session, _ = database
    service = PushService(session, transport=httpx.MockTransport(accepted))
    add_task(session)
    service.save(configured())
    assert service.run_once(now=NOW) == 2
    backups = BackupService(session)
    content = backups.archive_path(backups.create_backup().filename).read_bytes()
    monkeypatch.setattr(settings, "data_dir", tmp_path / "restored")
    target = BackupService(session)
    imported = target.import_backup(content)
    target.schedule_restore(imported.filename)
    assert apply_pending_restore()
    with sqlite3.connect(settings.database_path) as conn:
        assert (
            conn.execute("SELECT COUNT(*) FROM push_deliveries WHERE status='sent'").fetchone()[0]
            == 2
        )
        assert conn.execute(
            "SELECT value,is_secret FROM system_settings WHERE key='push.pushover_app_token'"
        ).fetchone() == (APP_TOKEN, 1)


def test_upgrade_and_downgrade_preserve_lego_and_default_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = Config("alembic.ini")
    command.upgrade(config, "0059")
    with sqlite3.connect(settings.database_path) as conn:
        conn.execute(
            "INSERT INTO system_settings (id,key,value,is_secret,created_at,updated_at) "
            "VALUES ('12345678123456781234567812345678','existing','kept',0,"
            "CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
        )
    command.upgrade(config, "0060")
    with sqlite3.connect(settings.database_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM push_deliveries").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM lego_sets").fetchone()[0] == 0
        assert (
            conn.execute("SELECT COUNT(*) FROM system_settings WHERE key LIKE 'push.%'").fetchone()[
                0
            ]
            == 0
        )
    command.downgrade(config, "0059")
    command.upgrade(config, "head")
    with sqlite3.connect(settings.database_path) as conn:
        assert (
            conn.execute("SELECT value FROM system_settings WHERE key='existing'").fetchone()[0]
            == "kept"
        )
