from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
import test_release_1718 as release_tests
from fastapi.testclient import TestClient
from test_release_1718 import call

from app.main import app
from app.models.time_tracking import WorkInterval
from app.schemas.mcp import McpSettingsWrite
from app.services.mcp_settings import McpSettingsService
from app.services.release import PortabilityService

database = release_tests.database


def test_mcp_timer_lifecycle_export_and_permissions(database):
    session, token = database
    with TestClient(app) as client:
        first = call(client, token, "start_work_interval", {"ticket": "123", "customer": "K"})
        page = call(client, token, "list_work_intervals", {"limit": 1}, path=True)
        assert page["items"][0]["id"] == first["id"]
        call(client, token, "stop_work_interval", {"interval_id": first["id"], "action": "pause"})
        resumed = call(client, token, "start_work_interval", {"ticket": "123", "customer": "K"})
        assert resumed["id"] != first["id"]
        call(client, token, "stop_work_interval", {"interval_id": resumed["id"], "action": "end"})
        page = call(client, token, "list_work_intervals", {"limit": 1})
        assert page["has_more"] and page["next_offset"] == 1
        assert len(call(client, token, "list_work_intervals", {"offset": 1})["items"]) == 1
        assert len(PortabilityService(session).export_payload()["data"]["work_intervals"]) == 2
        McpSettingsService(session).update(McpSettingsWrite(enabled=True, permission="read"))
        assert call(client, token, "list_work_intervals", {})["items"]
        response = client.post(
            "/mcp",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json, text/event-stream",
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "start_work_interval",
                    "arguments": {"ticket": "X", "customer": "K"},
                },
            },
        )
        assert response.json()["result"]["isError"]


@pytest.mark.parametrize("day,hours", [("2026-03-29", 23), ("2026-10-25", 25)])
def test_day_summary_handles_clock_changes(database, day, hours):
    session, token = database
    zone = ZoneInfo("Europe/Berlin")
    selected = date.fromisoformat(day)
    start = datetime.combine(selected, time.min, zone).timestamp()
    end = datetime.combine(selected + timedelta(days=1), time.min, zone).timestamp()
    session.add(
        WorkInterval(
            ticket="DST", customer="K", started_at=start - 3600, ended_at=end + 3600, running=False
        )
    )
    session.commit()
    with TestClient(app) as client:
        summary = call(client, token, "get_work_day", {"day": day})
        assert summary["seconds"] == hours * 3600
        assert summary["tickets"][0]["seconds"] == hours * 3600


def test_mcp_manual_and_edit(database):
    session, token = database
    with TestClient(app) as client:
        data = {
            "ticket": "M-1",
            "customer": "K",
            "info": "Manuell",
            "started_at": "2026-01-10T08:00:00+01:00",
            "ended_at": "2026-01-10T09:00:00+01:00",
        }
        first = call(client, token, "save_work_interval", data)
        updated = call(
            client,
            token,
            "save_work_interval",
            {**data, "interval_id": first["id"], "ended_at": "2026-01-10T10:00:00+01:00"},
        )
        assert updated["id"] == first["id"]
        assert updated["ended_at"] - updated["started_at"] == 7200
        assert call(client, token, "get_work_day", {"day": "2026-01-10"})["seconds"] == 7200
        McpSettingsService(session).update(McpSettingsWrite(enabled=True, permission="read"))
        response = client.post(
            "/mcp",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json, text/event-stream",
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "save_work_interval",
                    "arguments": {**data, "interval_id": first["id"]},
                },
            },
        )
        assert response.json()["result"]["isError"]


def test_mcp_delete_requires_admin_and_updates_summaries(database):
    session, token = database
    with TestClient(app) as client:
        data = {
            "ticket": "DELETE-1",
            "customer": "K",
            "started_at": "2026-01-10T08:00:00+01:00",
            "ended_at": "2026-01-10T09:00:00+01:00",
        }
        first = call(client, token, "save_work_interval", data)
        for permission in ("read", "write"):
            McpSettingsService(session).update(
                McpSettingsWrite(enabled=True, permission=permission)
            )
            response = client.post(
                "/mcp",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json, text/event-stream",
                },
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "delete_work_interval",
                        "arguments": {"interval_id": first["id"]},
                    },
                },
            )
            assert response.json()["result"]["isError"]
            assert len(call(client, token, "list_work_intervals", {})["items"]) == 1
        McpSettingsService(session).update(McpSettingsWrite(enabled=True, permission="admin"))
        result = call(
            client, token, "delete_work_interval", {"interval_id": first["id"]}, path=True
        )
        assert result["status"] == "deleted"
        assert call(client, token, "list_work_intervals", {})["items"] == []
        assert call(client, token, "get_work_day", {"day": "2026-01-10"})["seconds"] == 0


def test_mcp_can_save_and_extend_parallel_intervals(database):
    session, token = database
    with TestClient(app) as client:
        first_data = {
            "ticket": "parallel-A",
            "customer": "K",
            "started_at": "2026-01-10T08:00:00+01:00",
            "ended_at": "2026-01-10T09:00:00+01:00",
        }
        first = call(client, token, "save_work_interval", first_data)
        second = call(
            client,
            token,
            "save_work_interval",
            {
                **first_data,
                "ticket": "parallel-B",
                "started_at": "2026-01-10T08:30:00+01:00",
                "ended_at": "2026-01-10T10:00:00+01:00",
            },
        )
        changed = call(
            client,
            token,
            "save_work_interval",
            {**first_data, "interval_id": first["id"], "ended_at": "2026-01-10T09:30:00+01:00"},
        )
        assert changed["id"] == first["id"]
        assert second["id"] != first["id"]
        summary = call(client, token, "get_work_day", {"day": "2026-01-10"})
        assert summary["seconds"] == 10800
        assert {group["ticket"]: group["seconds"] for group in summary["tickets"]} == {
            "parallel-A": 5400,
            "parallel-B": 5400,
        }


def test_mcp_bcs_permissions_and_export(database):
    session, token = database
    with TestClient(app) as client:
        data = {
            "ticket": "BCS",
            "customer": "K",
            "started_at": "2026-01-10T08:00:00+01:00",
            "ended_at": "2026-01-10T09:00:00+01:00",
        }
        row = call(client, token, "save_work_interval", data)
        McpSettingsService(session).update(McpSettingsWrite(enabled=True, permission="write"))
        marked = call(
            client,
            token,
            "set_work_interval_bcs",
            {"interval_id": row["id"], "bcs": True},
            path=True,
        )
        assert marked["bcs"] is True
        changed = call(client, token, "save_work_interval", {**data, "interval_id": row["id"]})
        assert changed["bcs"] is True
        exported = PortabilityService(session).export_payload()["data"]["work_intervals"]
        assert exported[0]["bcs"] is True
        assert "bcs" in PortabilityService(session).csv_export("work_intervals")
        McpSettingsService(session).update(McpSettingsWrite(enabled=True, permission="read"))
        response = client.post(
            "/mcp",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json, text/event-stream",
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "set_work_interval_bcs",
                    "arguments": {"interval_id": row["id"], "bcs": False},
                },
            },
        )
        assert response.json()["result"]["isError"]
        assert call(client, token, "list_work_intervals", {})["items"][0]["bcs"] is True


def test_mcp_day_totals_include_customer_and_separate_identical_tickets(database):
    session, token = database
    with TestClient(app) as client:
        for customer in ("KD", "KD2"):
            call(
                client,
                token,
                "save_work_interval",
                {
                    "ticket": "T-1",
                    "customer": customer,
                    "started_at": "2026-01-10T08:00:00+01:00",
                    "ended_at": "2026-01-10T09:00:00+01:00",
                },
            )
        summary = call(client, token, "get_work_day", {"day": "2026-01-10"})
        assert summary["seconds"] == 7200
        assert {row["customer"]: row["seconds"] for row in summary["tickets"]} == {
            "KD": 3600,
            "KD2": 3600,
        }


def test_monthly_export_mcp_permissions_and_configuration(database):
    session, token = database
    with TestClient(app) as client:
        initial = call(client, token, "get_time_exports", {})
        assert not initial["configuration"]["enabled"]
        saved = call(client, token, "configure_time_exports", {"enabled": True})
        assert saved["enabled"] and not saved["upload_to_nextcloud"]
        result = call(client, token, "run_time_export", {}, path=True)
        assert result["last_error"] is None
        assert call(client, token, "get_time_exports", {})["files"]
        McpSettingsService(session).update(McpSettingsWrite(enabled=True, permission="read"))
        response = client.post(
            "/mcp",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json, text/event-stream",
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "configure_time_exports", "arguments": {"enabled": False}},
            },
        )
        assert response.json()["result"]["isError"]
