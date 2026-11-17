"""Exercise timer lifecycle and persistent single-timer enforcement."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.api.v1.time_tracking import router
from app.db.session import get_session


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    app = FastAPI()
    app.include_router(router)

    def session():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_session] = session
    with TestClient(app) as client:
        yield client
    engine.dispose()


def test_pause_switch_resume_end(client):
    data = {"ticket": " 123 ", "customer": "Kunde", "info": "Analyse"}
    first = client.post("/time-tracking/start", json=data)
    assert first.status_code == 201
    first = first.json()
    assert first["ticket"] == "123"
    assert client.post("/time-tracking/start", json=data).status_code == 409
    paused = client.post(f"/time-tracking/{first['id']}/pause").json()
    assert paused["ended_at"] >= paused["started_at"]
    assert not paused["running"] and not paused["completed"]
    other = client.post("/time-tracking/start", json={**data, "ticket": "456"}).json()
    assert client.post(f"/time-tracking/{other['id']}/end").json()["completed"]
    resumed = client.post("/time-tracking/start", json=data).json()
    assert resumed["id"] != first["id"]
    assert client.post(f"/time-tracking/{first['id']}/end").status_code == 409
    assert client.post(f"/time-tracking/{resumed['id']}/end").status_code == 200
    entries = client.get("/time-tracking").json()
    assert len(entries) == 3
    assert sum(i["ticket"] == "123" for i in entries) == 2
    assert all(i["ended_at"] is not None for i in entries)


def test_required_fields(client):
    assert (
        client.post("/time-tracking/start", json={"ticket": " ", "customer": "K"}).status_code
        == 422
    )
    assert (
        client.post("/time-tracking/start", json={"ticket": "1", "customer": ""}).status_code == 422
    )


def manual_data(start="2026-01-10T08:00:00+01:00", end="2026-01-10T09:00:00+01:00"):
    return {
        "ticket": "T-1",
        "customer": "Kunde",
        "info": "Nachtrag",
        "started_at": start,
        "ended_at": end,
    }


def test_manual_entry_and_edit_preserve_id_and_recalculate(client):
    created = client.post("/time-tracking/manual", json=manual_data())
    assert created.status_code == 201
    row = created.json()
    assert not row["running"] and row["completed"]
    assert row["ended_at"] - row["started_at"] == 3600
    changed = client.put(
        f"/time-tracking/{row['id']}",
        json={
            **manual_data(end="2026-01-10T10:30:00+01:00"),
            "ticket": "T-2",
            "info": "Korrigiert",
        },
    )
    assert changed.status_code == 200
    changed = changed.json()
    assert changed["id"] == row["id"] and changed["ticket"] == "T-2"
    assert changed["ended_at"] - changed["started_at"] == 9000
    assert len(client.get("/time-tracking").json()) == 1


def test_overlapping_entries_and_extended_end_time_are_allowed(client):
    first = client.post("/time-tracking/manual", json=manual_data()).json()
    second = client.post(
        "/time-tracking/manual",
        json={
            **manual_data(start="2026-01-10T08:30:00+01:00", end="2026-01-10T10:00:00+01:00"),
            "ticket": "parallel",
        },
    )
    assert second.status_code == 201
    changed = client.put(
        f"/time-tracking/{first['id']}", json=manual_data(end="2026-01-10T09:30:00+01:00")
    )
    assert changed.status_code == 200
    assert changed.json()["id"] == first["id"]
    assert changed.json()["ended_at"] - changed.json()["started_at"] == 5400
    rows = client.get("/time-tracking").json()
    assert len(rows) == 2
    assert sum(row["ended_at"] - row["started_at"] for row in rows) == 10800
    assert next(row for row in rows if row["id"] == second.json()["id"]) == second.json()


def test_manual_entry_may_overlap_an_active_timer(client):
    from datetime import UTC, datetime

    running = client.post("/time-tracking/start", json={"ticket": "live", "customer": "K"}).json()
    data = manual_data(
        datetime.fromtimestamp(running["started_at"] - 60, UTC).isoformat(),
        datetime.now(UTC).isoformat(),
    )
    assert client.post("/time-tracking/manual", json=data).status_code == 201
    rows = client.get("/time-tracking").json()
    assert next(row for row in rows if row["id"] == running["id"])["running"]
    assert len(rows) == 2


@pytest.mark.parametrize(
    "start,end",
    [
        ("2026-01-10T08:00:00+01:00", "2026-01-10T08:00:00+01:00"),
        ("2026-01-10T09:00:00+01:00", "2026-01-10T08:00:00+01:00"),
        ("2026-01-10T08:00:00", "2026-01-10T09:00:00"),
        ("2099-01-10T08:00:00+01:00", "2099-01-10T09:00:00+01:00"),
    ],
)
def test_manual_invalid_times(client, start, end):
    assert client.post("/time-tracking/manual", json=manual_data(start, end)).status_code == 422
    assert client.get("/time-tracking").json() == []


def test_running_entry_cannot_be_edited_and_missing_entry_is_404(client):
    running = client.post("/time-tracking/start", json={"ticket": "T", "customer": "K"}).json()
    assert client.put(f"/time-tracking/{running['id']}", json=manual_data()).status_code == 409
    assert client.put("/time-tracking/missing", json=manual_data()).status_code == 404
    assert client.get("/time-tracking").json()[0]["running"]


def test_new_installations_offer_time_tracking_by_default():
    import json

    from app.models.application_setting import ApplicationSetting

    settings = ApplicationSetting(installation_name="Test", timezone="Europe/Berlin")
    assert "time_tracking" in json.loads(settings.enabled_modules_json)
    assert "time_tracking" in json.loads(settings.main_menu_modules_json)


def test_delete_removes_only_one_interval_and_frees_time_range(client):
    first = client.post("/time-tracking/manual", json=manual_data()).json()
    second = client.post(
        "/time-tracking/manual",
        json=manual_data(start="2026-01-10T09:00:00+01:00", end="2026-01-10T10:00:00+01:00"),
    ).json()
    response = client.delete(f"/time-tracking/{first['id']}")
    assert response.status_code == 204 and response.content == b""
    assert [row["id"] for row in client.get("/time-tracking").json()] == [second["id"]]
    assert client.delete(f"/time-tracking/{first['id']}").status_code == 404
    assert client.post("/time-tracking/manual", json=manual_data()).status_code == 201


def test_delete_rejects_running_interval(client):
    running = client.post("/time-tracking/start", json={"ticket": "T", "customer": "K"}).json()
    assert client.delete(f"/time-tracking/{running['id']}").status_code == 409
    assert client.get("/time-tracking").json()[0]["running"]
    client.post(f"/time-tracking/{running['id']}/pause")
    assert client.delete(f"/time-tracking/{running['id']}").status_code == 204
    assert client.get("/time-tracking").json() == []


def test_bcs_persists_and_time_edits_do_not_clear_it(client):
    row = client.post("/time-tracking/manual", json=manual_data()).json()
    assert row["bcs"] is False
    marked = client.patch(f"/time-tracking/{row['id']}/bcs", json={"bcs": True})
    assert marked.status_code == 200 and marked.json()["bcs"] is True
    assert marked.json()["started_at"] == row["started_at"]
    assert client.get("/time-tracking").json()[0]["bcs"] is True
    edited = client.put(
        f"/time-tracking/{row['id']}", json=manual_data(end="2026-01-10T10:00:00+01:00")
    )
    assert edited.status_code == 200 and edited.json()["bcs"] is True
    assert (
        client.patch(f"/time-tracking/{row['id']}/bcs", json={"bcs": False}).json()["bcs"] is False
    )
    assert client.get("/time-tracking").json()[0]["bcs"] is False


def test_bcs_on_active_timer_does_not_stop_or_change_it(client):
    row = client.post("/time-tracking/start", json={"ticket": "BCS", "customer": "K"}).json()
    marked = client.patch(f"/time-tracking/{row['id']}/bcs", json={"bcs": True}).json()
    assert marked["running"] and marked["ended_at"] is None
    assert marked["started_at"] == row["started_at"] and marked["bcs"]
    assert client.post(f"/time-tracking/{row['id']}/end").json()["bcs"]
    assert client.patch("/time-tracking/unknown/bcs", json={"bcs": True}).status_code == 404
    assert client.patch(f"/time-tracking/{row['id']}/bcs", json={"bcs": "yes"}).status_code == 422
