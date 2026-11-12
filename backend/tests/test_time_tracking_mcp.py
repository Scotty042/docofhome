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
