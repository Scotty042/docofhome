from sqlmodel import Session, select

from app.models.system_setting import SystemSetting
from app.schemas.mcp import McpPermission, McpSettingsWrite
from app.services.mcp_settings import McpSettingsError, McpSettingsService


def test_mcp_defaults_to_disabled_read_only(session: Session) -> None:
    settings = McpSettingsService(session).read()

    assert settings.enabled is False
    assert settings.permission == McpPermission.READ
    assert settings.public_url is None
    assert settings.token_configured is False


def test_mcp_token_is_only_stored_as_hash(session: Session) -> None:
    service = McpSettingsService(session)

    created = service.rotate_token()

    assert created.token.startswith("doh_mcp_")
    assert created.settings.token_configured is True
    rows = list(session.exec(select(SystemSetting)).all())
    token_row = next(row for row in rows if row.key == McpSettingsService.TOKEN_HASH_KEY)
    assert created.token not in token_row.value
    assert token_row.value == service.hash_token(created.token)
    assert token_row.is_secret is True


def test_mcp_cannot_be_enabled_without_token(session: Session) -> None:
    service = McpSettingsService(session)

    try:
        service.update(
            McpSettingsWrite(enabled=True, permission=McpPermission.WRITE, public_url=None)
        )
    except McpSettingsError as exc:
        assert "MCP-Token" in str(exc)
    else:
        raise AssertionError("MCP must not be enabled without a token")


def test_mcp_token_and_permission_are_enforced(session: Session) -> None:
    service = McpSettingsService(session)
    token = service.rotate_token().token
    stored = service.update(
        McpSettingsWrite(
            enabled=True,
            permission=McpPermission.WRITE,
            public_url="https://mcp.example.test/mcp",
        )
    )

    assert stored.public_url == "https://mcp.example.test/mcp"
    assert service.verify_token(token) is True
    assert service.verify_token("wrong-token") is False
    assert service.require_permission(McpPermission.READ).permission == McpPermission.WRITE
    assert service.require_permission(McpPermission.WRITE).permission == McpPermission.WRITE
    try:
        service.require_permission(McpPermission.ADMIN)
    except PermissionError:
        pass
    else:
        raise AssertionError("write permission must not grant admin access")
