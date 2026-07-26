from collections.abc import Callable

import httpx
from sqlmodel import Session, SQLModel, create_engine

from app.models.integration_setting import IntegrationSetting
from app.schemas.settings import IntegrationKind
from app.services.integration_checks import IntegrationCheckService


def service_with_setting(
    setting: IntegrationSetting,
    handler: Callable[[httpx.Request], httpx.Response],
) -> IntegrationCheckService:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    session.add(setting)
    session.commit()
    return IntegrationCheckService(session, transport=httpx.MockTransport(handler))


def test_home_assistant_check_validates_token_and_reports_version() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/config"
        assert request.headers["authorization"] == "Bearer ha-secret"
        return httpx.Response(200, json={"version": "2026.7.1"})

    service = service_with_setting(
        IntegrationSetting(
            kind="home_assistant",
            enabled=True,
            base_url="http://home-assistant.local:8123",
            secret="ha-secret",
        ),
        handler,
    )

    result = service.check(IntegrationKind.HOME_ASSISTANT)

    assert result.success is True
    assert result.service_version == "2026.7.1"
    assert "ha-secret" not in result.model_dump_json()


def test_immich_check_uses_api_key_and_api_base_once() -> None:
    requested_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_paths.append(request.url.path)
        assert request.headers["x-api-key"] == "immich-secret"
        if request.url.path == "/api/api-keys/me":
            return httpx.Response(200, json={"id": "key-id", "name": "Tectoryn"})
        return httpx.Response(200, json={"major": 2, "minor": 1, "patch": 0})

    service = service_with_setting(
        IntegrationSetting(
            kind="immich",
            enabled=True,
            base_url="http://immich.local/api",
            secret="immich-secret",
        ),
        handler,
    )

    result = service.check(IntegrationKind.IMMICH)

    assert result.success is True
    assert result.service_version == "2.1.0"
    assert requested_paths == ["/api/api-keys/me", "/api/server/version"]


def test_nextcloud_check_is_read_only_propfind() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PROPFIND"
        assert request.url.path == "/remote.php/dav/files/docs-user/"
        assert request.headers["depth"] == "0"
        assert request.headers["authorization"].startswith("Basic ")
        return httpx.Response(207, text="<d:multistatus xmlns:d='DAV:' />")

    service = service_with_setting(
        IntegrationSetting(
            kind="nextcloud",
            enabled=True,
            base_url="https://nextcloud.local",
            account="docs-user",
            secret="nextcloud-secret",
        ),
        handler,
    )

    result = service.check(IntegrationKind.NEXTCLOUD)

    assert result.success is True
    assert result.service_version is None


def test_rejected_credentials_return_safe_message() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "secret remote response"})

    service = service_with_setting(
        IntegrationSetting(
            kind="home_assistant",
            enabled=True,
            base_url="https://home-assistant.local",
            secret="wrong-secret",
        ),
        handler,
    )

    result = service.check(IntegrationKind.HOME_ASSISTANT)

    assert result.success is False
    assert result.message == "Die Zugangsdaten wurden vom Server abgelehnt."
    assert "secret remote response" not in result.model_dump_json()
    assert "wrong-secret" not in result.model_dump_json()


def test_disabled_and_incomplete_integrations_do_not_open_connections() -> None:
    def unexpected(_: httpx.Request) -> httpx.Response:
        raise AssertionError("No request expected")

    disabled = service_with_setting(
        IntegrationSetting(kind="immich", enabled=False),
        unexpected,
    ).check(IntegrationKind.IMMICH)
    missing_account = service_with_setting(
        IntegrationSetting(
            kind="nextcloud",
            enabled=True,
            base_url="https://nextcloud.local",
            secret="nextcloud-secret",
        ),
        unexpected,
    ).check(IntegrationKind.NEXTCLOUD)

    assert disabled.success is False
    assert "deaktiviert" in disabled.message
    assert missing_account.success is False
    assert "Konto" in missing_account.message
