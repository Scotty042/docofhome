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


def test_overlap_rejected_but_adjacent_entries_allowed(client):
    row = client.post("/time-tracking/manual", json=manual_data()).json()
    assert client.post("/time-tracking/manual", json=manual_data()).status_code == 409
    adjacent = manual_data(start="2026-01-10T09:00:00+01:00", end="2026-01-10T10:00:00+01:00")
    assert client.post("/time-tracking/manual", json=adjacent).status_code == 201
    assert (
        client.put(
            f"/time-tracking/{row['id']}", json=manual_data(end="2026-01-10T09:30:00+01:00")
        ).status_code
        == 409
    )
    assert client.get("/time-tracking").json()[-1]["ended_at"] == row["ended_at"]


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
