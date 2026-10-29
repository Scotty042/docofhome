import re
from datetime import datetime
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator

Provider = Literal["pushover", "ntfy"]


class PushConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    readings_enabled: bool = True
    maintenance_enabled: bool = True
    tasks_enabled: bool = True
    send_hour: int = Field(default=8, ge=0, le=23)
    send_minute: int = Field(default=0, ge=0, le=59)
    days_ahead: int = Field(default=3, ge=0, le=31)
    public_url: str | None = Field(default=None, max_length=400)
    pushover_enabled: bool = False
    pushover_device: str = Field(default="", max_length=100)
    ntfy_enabled: bool = False
    ntfy_url: str = Field(default="https://ntfy.sh", max_length=500)
    ntfy_topic: str = Field(default="", max_length=100)

    @field_validator("public_url", "ntfy_url")
    @classmethod
    def http_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        from pydantic import AnyHttpUrl, TypeAdapter

        parsed = TypeAdapter(AnyHttpUrl).validate_python(value.strip())
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("URL ohne Zugangsdaten, Query oder Fragment angeben")
        return str(parsed).rstrip("/")

    @field_validator("ntfy_topic", "pushover_device")
    @classmethod
    def identifiers(cls, value: str) -> str:
        value = value.strip()
        if value and not re.fullmatch(r"[A-Za-z0-9_,\-]+", value):
            raise ValueError("Nur Buchstaben, Zahlen, Unterstrich und Bindestrich verwenden")
        return value

    @model_validator(mode="after")
    def topic_rules(self) -> "PushConfig":
        if "," in self.ntfy_topic:
            raise ValueError("ntfy: genau ein Topic angeben")
        if self.public_url and urlsplit(self.public_url).path not in ("", "/"):
            raise ValueError("Öffentliche DocOfHome-Adresse ohne Unterpfad angeben")
        return self


class PushWrite(PushConfig):
    pushover_app_token: SecretStr | None = None
    pushover_user_key: SecretStr | None = None
    ntfy_access_token: SecretStr | None = None
    clear_pushover_app_token: bool = False
    clear_pushover_user_key: bool = False
    clear_ntfy_access_token: bool = False

    @field_validator("pushover_app_token", "pushover_user_key", "ntfy_access_token")
    @classmethod
    def secret_format(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None or not value.get_secret_value().strip():
            return None
        raw = value.get_secret_value().strip()
        if len(raw) > 500 or any(c.isspace() for c in raw):
            raise ValueError("Ungültiger Schlüssel")
        return SecretStr(raw)


class PushRead(PushConfig):
    pushover_app_token_configured: bool = False
    pushover_user_key_configured: bool = False
    ntfy_access_token_configured: bool = False


class PushResult(BaseModel):
    success: bool
    message: str


class PushDeliveryRead(BaseModel):
    provider: Provider
    kind: str
    status: str
    attempts: int
    detail: str | None
    last_attempt_at: datetime | None
    next_retry_at: datetime | None
