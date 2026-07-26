from datetime import datetime
from enum import StrEnum
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
    SecretStr,
    TypeAdapter,
    field_validator,
    model_validator,
)


class IntegrationKind(StrEnum):
    HOME_ASSISTANT = "home_assistant"
    IMMICH = "immich"
    NEXTCLOUD = "nextcloud"
    FRITZBOX = "fritzbox"


class ModuleKey(StrEnum):
    LOCATIONS = "locations"
    ELECTRICAL = "electrical"
    ASSETS = "assets"
    MASTER_DATA = "master_data"
    NETWORK = "network"
    SMART_HOME = "smart_home"
    CONSUMPTION = "consumption"
    WIKI = "wiki"
    MAINTENANCE = "maintenance"
    QUALITY = "quality"


class ThemePreference(StrEnum):
    DARK = "dark"
    LIGHT = "light"


class Language(StrEnum):
    GERMAN = "de"
    ENGLISH = "en"


def default_enabled_modules() -> list[ModuleKey]:
    return list(ModuleKey)


class IntegrationWrite(BaseModel):
    kind: IntegrationKind
    enabled: bool = False
    base_url: str | None = None
    account: str | None = Field(default=None, max_length=255)
    secret: SecretStr | None = None
    selected_album_id: UUID | None = None
    document_root: str | None = Field(default=None, max_length=500)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        validated = TypeAdapter(AnyHttpUrl).validate_python(value.strip())
        if validated.username is not None or validated.password is not None:
            raise ValueError("URL must not contain a username or password")
        return str(validated).rstrip("/")

    @field_validator("account")
    @classmethod
    def normalize_account(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()

    @field_validator("secret")
    @classmethod
    def normalize_secret(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None or not value.get_secret_value().strip():
            return None
        return SecretStr(value.get_secret_value().strip())

    @field_validator("document_root")
    @classmethod
    def normalize_document_root(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip()
        if normalized.startswith("/") or normalized.endswith("/") or "//" in normalized:
            raise ValueError("Invalid Nextcloud document root")
        parts = [part.strip() for part in normalized.split("/")]
        if (
            not parts
            or any(not part or part in {".", ".."} for part in parts)
            or any("\\" in part or len(part) > 255 for part in parts)
            or any(
                any(ord(character) < 32 or ord(character) == 127 for character in part)
                for part in parts
            )
        ):
            raise ValueError("Invalid Nextcloud document root")
        return "/".join(parts)

    @model_validator(mode="after")
    def integration_specific_fields_match_kind(self) -> "IntegrationWrite":
        if self.kind != IntegrationKind.IMMICH and self.selected_album_id is not None:
            raise ValueError("An album can only be selected for the Immich integration")
        if self.kind != IntegrationKind.NEXTCLOUD and self.document_root is not None:
            raise ValueError("A document root can only be configured for Nextcloud")
        if (
            self.kind in {IntegrationKind.NEXTCLOUD, IntegrationKind.FRITZBOX}
            and self.account is not None
        ):
            if (
                "/" in self.account
                or "\\" in self.account
                or any(ord(character) < 32 or ord(character) == 127 for character in self.account)
            ):
                raise ValueError("Invalid Nextcloud account or username")
        return self


class ConfigurationWrite(BaseModel):
    installation_name: str = Field(min_length=1, max_length=100)
    language: Language = Language.GERMAN
    timezone: str = Field(min_length=1, max_length=100)
    theme: ThemePreference = ThemePreference.DARK
    online_product_image_search_enabled: bool = False
    enabled_modules: list[ModuleKey] = Field(
        default_factory=default_enabled_modules,
        max_length=len(ModuleKey),
    )
    integrations: list[IntegrationWrite] = Field(default_factory=list, max_length=4)

    @field_validator("installation_name")
    @classmethod
    def normalize_installation_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Installation name must not be empty")
        return normalized

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        normalized = value.strip()
        try:
            ZoneInfo(normalized)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown IANA timezone") from exc
        return normalized

    @field_validator("enabled_modules")
    @classmethod
    def modules_are_unique(cls, value: list[ModuleKey]) -> list[ModuleKey]:
        if len(value) != len(set(value)):
            raise ValueError("Each module may only be configured once")
        return value

    @model_validator(mode="after")
    def integrations_are_unique(self) -> "ConfigurationWrite":
        kinds = [integration.kind for integration in self.integrations]
        if len(kinds) != len(set(kinds)):
            raise ValueError("Each integration may only be configured once")
        return self


class IntegrationRead(BaseModel):
    kind: IntegrationKind
    enabled: bool
    base_url: str | None
    account: str | None
    secret_configured: bool
    selected_album_id: UUID | None
    document_root: str | None


class IntegrationTestResult(BaseModel):
    kind: IntegrationKind
    success: bool
    message: str
    service_version: str | None = None
    response_time_ms: int = Field(ge=0)


class ConfigurationRead(BaseModel):
    installation_name: str
    language: Language
    timezone: str
    theme: ThemePreference
    online_product_image_search_enabled: bool
    enabled_modules: list[ModuleKey]
    setup_completed_at: datetime
    integrations: list[IntegrationRead]


class SetupStatusRead(BaseModel):
    setup_required: bool
    completed: bool
