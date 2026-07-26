from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine, select

from app.db.session import get_session
from app.main import app
from app.models.asset_engine import Location
from app.models.integration_setting import IntegrationSetting


@pytest.fixture
def settings_client(tmp_path: Path) -> Generator[tuple[TestClient, Engine]]:
    database_path = tmp_path / "settings.sqlite3"
    test_engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(test_engine)

    def override_session() -> Generator[Session]:
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client, test_engine
    app.dependency_overrides.clear()


def configuration_payload(secret: str = "test-only-secret") -> dict[str, object]:
    return {
        "installation_name": "Test House",
        "language": "de",
        "timezone": "Europe/Berlin",
        "theme": "dark",
        "integrations": [
            {
                "kind": "home_assistant",
                "enabled": True,
                "base_url": "https://home-assistant.example.test",
                "secret": secret,
            },
            {"kind": "immich", "enabled": False},
            {"kind": "nextcloud", "enabled": False},
        ],
    }


def test_first_start_requires_setup(settings_client: tuple[TestClient, Engine]) -> None:
    client, _ = settings_client

    response = client.get("/api/v1/setup/status")

    assert response.status_code == 200
    assert response.json() == {"setup_required": True, "completed": False}


def test_configuration_is_persisted_and_survives_new_client(
    settings_client: tuple[TestClient, Engine],
) -> None:
    client, _ = settings_client

    completed = client.post("/api/v1/setup/complete", json=configuration_payload())
    assert completed.status_code == 201

    with TestClient(app) as restarted_client:
        status = restarted_client.get("/api/v1/setup/status")
        stored = restarted_client.get("/api/v1/settings")

    assert status.json() == {"setup_required": False, "completed": True}
    assert stored.status_code == 200
    assert stored.json()["installation_name"] == "Test House"

    with Session(settings_client[1]) as session:
        roots = list(
            session.exec(
                select(Location).where(
                    Location.parent_id.is_(None),
                    Location.deleted_at.is_(None),
                )
            ).all()
        )
    assert len(roots) == 1
    assert roots[0].name == "Test House"
    assert roots[0].location_type == "building"


def test_completed_setup_cannot_be_repeated(settings_client: tuple[TestClient, Engine]) -> None:
    client, _ = settings_client
    first = client.post("/api/v1/setup/complete", json=configuration_payload())
    changed = configuration_payload()
    changed["installation_name"] = "Unexpected replacement"

    repeated = client.post("/api/v1/setup/complete", json=changed)
    stored = client.get("/api/v1/settings")

    assert first.status_code == 201
    assert repeated.status_code == 409
    assert stored.json()["installation_name"] == "Test House"


def test_setup_renames_existing_migration_root_without_replacing_uuid(
    settings_client: tuple[TestClient, Engine],
) -> None:
    client, test_engine = settings_client
    with Session(test_engine) as session:
        migration_root = Location(name="Home", location_type="building", sort_order=0)
        session.add(migration_root)
        session.commit()
        root_id = migration_root.id

    completed = client.post("/api/v1/setup/complete", json=configuration_payload())

    assert completed.status_code == 201
    with Session(test_engine) as session:
        roots = list(session.exec(select(Location)).all())
    assert len(roots) == 1
    assert roots[0].id == root_id
    assert roots[0].name == "Test House"


def test_secrets_are_redacted_and_preserved_on_update(
    settings_client: tuple[TestClient, Engine],
) -> None:
    client, test_engine = settings_client
    secret = "never-return-this-secret"
    completed = client.post(
        "/api/v1/setup/complete",
        json=configuration_payload(secret=secret),
    )

    assert completed.status_code == 201
    assert secret not in completed.text
    home_assistant = completed.json()["integrations"][0]
    assert home_assistant["secret_configured"] is True
    assert "secret" not in home_assistant

    update = configuration_payload()
    integrations = update["integrations"]
    assert isinstance(integrations, list)
    integrations[0].pop("secret")
    updated = client.put("/api/v1/settings", json=update)
    assert updated.status_code == 200
    assert secret not in updated.text

    with Session(test_engine) as session:
        statement = select(IntegrationSetting).where(IntegrationSetting.kind == "home_assistant")
        stored = session.exec(statement).one()
    assert stored.secret == secret


def test_invalid_enabled_integration_is_not_committed(
    settings_client: tuple[TestClient, Engine],
) -> None:
    client, test_engine = settings_client
    payload = configuration_payload()
    integrations = payload["integrations"]
    assert isinstance(integrations, list)
    integrations[0].pop("secret")

    response = client.post("/api/v1/setup/complete", json=payload)
    status_response = client.get("/api/v1/setup/status")

    assert response.status_code == 422
    assert status_response.json()["setup_required"] is True
    with Session(test_engine) as session:
        assert session.exec(select(Location)).all() == []


def test_invalid_integration_url_is_rejected(settings_client: tuple[TestClient, Engine]) -> None:
    client, _ = settings_client
    payload = configuration_payload()
    integrations = payload["integrations"]
    assert isinstance(integrations, list)
    integrations[0]["base_url"] = "not-a-url"

    response = client.post("/api/v1/setup/complete", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "url",
    [
        "https://user@example.test",
        "https://user:password@example.test",
    ],
)
def test_integration_url_with_userinfo_is_rejected(
    settings_client: tuple[TestClient, Engine],
    url: str,
) -> None:
    client, _ = settings_client
    payload = configuration_payload()
    integrations = payload["integrations"]
    assert isinstance(integrations, list)
    integrations[0]["base_url"] = url

    response = client.post("/api/v1/setup/complete", json=payload)
    status_response = client.get("/api/v1/setup/status")

    assert response.status_code == 422
    assert "username or password" in response.text
    assert status_response.json()["setup_required"] is True


def test_optional_account_is_persisted_without_exposing_secret(
    settings_client: tuple[TestClient, Engine],
) -> None:
    client, _ = settings_client
    payload = configuration_payload()
    integrations = payload["integrations"]
    assert isinstance(integrations, list)
    integrations[2] = {
        "kind": "nextcloud",
        "enabled": True,
        "base_url": "https://nextcloud.example.test",
        "account": " documentation-user ",
        "secret": "nextcloud-test-secret",
        "document_root": " Haus / Dokumente ",
    }

    completed = client.post("/api/v1/setup/complete", json=payload)
    stored = client.get("/api/v1/settings")

    assert completed.status_code == 201
    nextcloud = next(item for item in stored.json()["integrations"] if item["kind"] == "nextcloud")
    assert nextcloud["account"] == "documentation-user"
    assert nextcloud["secret_configured"] is True
    assert nextcloud["document_root"] == "Haus/Dokumente"
    assert "nextcloud-test-secret" not in stored.text
    assert "secret" not in nextcloud


def test_selected_immich_album_is_persisted_and_readable(
    settings_client: tuple[TestClient, Engine],
) -> None:
    client, test_engine = settings_client
    album_id = "11111111-1111-4111-8111-111111111111"
    payload = configuration_payload()
    integrations = payload["integrations"]
    assert isinstance(integrations, list)
    integrations[1] = {
        "kind": "immich",
        "enabled": True,
        "base_url": "https://immich.example.test",
        "secret": "immich-test-secret",
        "selected_album_id": album_id,
    }

    completed = client.post("/api/v1/setup/complete", json=payload)
    stored = client.get("/api/v1/settings")

    assert completed.status_code == 201
    immich = next(item for item in stored.json()["integrations"] if item["kind"] == "immich")
    assert immich["selected_album_id"] == album_id
    with Session(test_engine) as session:
        integration = session.exec(
            select(IntegrationSetting).where(IntegrationSetting.kind == "immich")
        ).one()
    assert integration.selected_album_id == album_id


def test_album_selection_is_rejected_for_non_immich_integration(
    settings_client: tuple[TestClient, Engine],
) -> None:
    client, _ = settings_client
    payload = configuration_payload()
    integrations = payload["integrations"]
    assert isinstance(integrations, list)
    integrations[0]["selected_album_id"] = "11111111-1111-4111-8111-111111111111"

    response = client.post("/api/v1/setup/complete", json=payload)

    assert response.status_code == 422


def test_document_root_is_rejected_for_non_nextcloud_integration(
    settings_client: tuple[TestClient, Engine],
) -> None:
    client, _ = settings_client
    payload = configuration_payload()
    integrations = payload["integrations"]
    assert isinstance(integrations, list)
    integrations[0]["document_root"] = "docofhome/Documents"

    response = client.post("/api/v1/setup/complete", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "document_root",
    [
        "/docofhome/Documents",
        "docofhome/Documents/",
        "docofhome//Documents",
        "docofhome/../Documents",
        "docofhome\\Documents",
    ],
)
def test_unsafe_nextcloud_document_root_is_rejected(
    settings_client: tuple[TestClient, Engine],
    document_root: str,
) -> None:
    client, _ = settings_client
    payload = configuration_payload()
    integrations = payload["integrations"]
    assert isinstance(integrations, list)
    integrations[2] = {
        "kind": "nextcloud",
        "enabled": True,
        "base_url": "https://nextcloud.example.test",
        "account": "documentation-user",
        "secret": "nextcloud-test-secret",
        "document_root": document_root,
    }

    response = client.post("/api/v1/setup/complete", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize("account", ["user/name", "user\\name", "user\nname"])
def test_unsafe_nextcloud_account_is_rejected(
    settings_client: tuple[TestClient, Engine],
    account: str,
) -> None:
    client, _ = settings_client
    payload = configuration_payload()
    integrations = payload["integrations"]
    assert isinstance(integrations, list)
    integrations[2] = {
        "kind": "nextcloud",
        "enabled": True,
        "base_url": "https://nextcloud.example.test",
        "account": account,
        "secret": "nextcloud-test-secret",
        "document_root": "docofhome/Documents",
    }

    response = client.post("/api/v1/setup/complete", json=payload)

    assert response.status_code == 422
