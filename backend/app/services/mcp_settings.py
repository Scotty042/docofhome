from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models.system_setting import SystemSetting
from app.schemas.mcp import McpPermission, McpSettingsRead, McpSettingsWrite, McpTokenCreated


class McpSettingsError(ValueError):
    """Raised when MCP configuration is incomplete or inconsistent."""


class McpSettingsService:
    ENABLED_KEY = "mcp.enabled"
    PERMISSION_KEY = "mcp.permission"
    TOKEN_HASH_KEY = "mcp.token_sha256"
    PUBLIC_URL_KEY = "mcp.public_url"

    _RANK = {
        McpPermission.READ: 0,
        McpPermission.WRITE: 1,
        McpPermission.ADMIN: 2,
    }

    def __init__(self, session: Session) -> None:
        self.session = session

    def read(self) -> McpSettingsRead:
        enabled = self._read_bool(self.ENABLED_KEY, default=False)
        raw_permission = self._read_value(self.PERMISSION_KEY)
        try:
            permission = McpPermission(raw_permission) if raw_permission else McpPermission.READ
        except ValueError:
            permission = McpPermission.READ
        public_url = self._read_value(self.PUBLIC_URL_KEY) or None
        return McpSettingsRead(
            enabled=enabled,
            permission=permission,
            public_url=public_url,
            token_configured=bool(self._read_value(self.TOKEN_HASH_KEY)),
        )

    def update(self, payload: McpSettingsWrite) -> McpSettingsRead:
        if payload.enabled and not self._read_value(self.TOKEN_HASH_KEY):
            raise McpSettingsError("Erzeuge zuerst einen MCP-Token, bevor MCP aktiviert wird")
        self._write_value(self.ENABLED_KEY, "true" if payload.enabled else "false")
        self._write_value(self.PERMISSION_KEY, payload.permission.value)
        self._write_value(self.PUBLIC_URL_KEY, payload.public_url or "")
        self.session.commit()
        return self.read()

    def rotate_token(self) -> McpTokenCreated:
        # 32 random bytes provide 256 bits of entropy. Only the SHA-256 digest is persisted.
        token = f"doh_mcp_{secrets.token_urlsafe(32)}"
        digest = self.hash_token(token)
        self._write_value(self.TOKEN_HASH_KEY, digest, is_secret=True)
        self.session.commit()
        return McpTokenCreated(token=token, settings=self.read())

    def verify_token(self, token: str) -> bool:
        settings = self.read()
        if not settings.enabled or not settings.token_configured:
            return False
        configured_hash = self._read_value(self.TOKEN_HASH_KEY)
        if not configured_hash:
            return False
        return hmac.compare_digest(configured_hash, self.hash_token(token))

    def require_permission(self, required: McpPermission) -> McpSettingsRead:
        current = self.read()
        if not current.enabled:
            raise PermissionError("MCP ist in DocOfHome deaktiviert")
        if not current.token_configured:
            raise PermissionError("Für MCP ist kein Token eingerichtet")
        if self._RANK[current.permission] < self._RANK[required]:
            raise PermissionError(
                f"Die MCP-Berechtigung '{current.permission.value}' erlaubt diese Aktion nicht"
            )
        return current

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _read_bool(self, key: str, *, default: bool) -> bool:
        value = self._read_value(key)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def _read_value(self, key: str) -> str | None:
        row = self.session.exec(select(SystemSetting).where(SystemSetting.key == key)).one_or_none()
        return row.value if row is not None else None

    def _write_value(self, key: str, value: str, *, is_secret: bool = False) -> None:
        row = self.session.exec(select(SystemSetting).where(SystemSetting.key == key)).one_or_none()
        now = datetime.now(UTC)
        if row is None:
            row = SystemSetting(key=key, value=value, is_secret=is_secret)
        else:
            row.value = value
            row.is_secret = is_secret
            row.updated_at = now
        self.session.add(row)
