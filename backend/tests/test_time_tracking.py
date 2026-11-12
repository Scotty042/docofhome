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
