from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import get_session
from app.main import app


@pytest.fixture
def archive_client(tmp_path: Path) -> Generator[TestClient]:
    test_engine = create_engine(
        f"sqlite:///{tmp_path / 'archive.sqlite3'}",
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


def test_archived_asset_is_available_only_through_archive_api(
    archive_client: TestClient,
) -> None:
    asset_type = archive_client.post(
        "/api/v1/asset-types",
        json={"name": "Archive test", "icon": "mdi-archive-outline"},
    ).json()
    asset_response = archive_client.post(
        "/api/v1/assets",
        json={
            "name": "Historical device",
            "asset_type_id": asset_type["id"],
            "status": "active",
            "label_ids": [],
        },
    )
    assert asset_response.status_code == 201
    asset = asset_response.json()

    assert archive_client.get(f"/api/v1/archive/assets/{asset['id']}").status_code == 404
    assert archive_client.delete(f"/api/v1/assets/{asset['id']}").status_code == 204
    assert archive_client.get(f"/api/v1/assets/{asset['id']}").status_code == 404

    archived = archive_client.get(f"/api/v1/archive/assets/{asset['id']}")
    assert archived.status_code == 200
    assert archived.json()["id"] == asset["id"]
    assert archived.json()["deleted_at"] is not None
