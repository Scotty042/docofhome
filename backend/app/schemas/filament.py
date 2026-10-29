import re
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class SpoolWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    manufacturer: str = Field(default="", max_length=100)
    material: str = Field(min_length=1, max_length=100)
    variant: str = Field(default="", max_length=200)
    color_name: str = Field(default="", max_length=200)
    color_hex: str = Field(default="#808080", pattern=r"^#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?$")
    shop_code: str = Field(default="", max_length=100)
    condition: Literal["sealed", "open"] = "sealed"
    initial_g: float | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False)
    remaining_g: float | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False)
    remaining_percent: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    location_id: UUID | None = None
    storage_note: str = Field(default="", max_length=300)
    reorder: bool = False
    reorder_note: str = Field(default="", max_length=1000)
    notes: str = Field(default="", max_length=50000)
    image_url: str | None = Field(default=None, max_length=1000)
    rfid: str | None = Field(default=None, max_length=100)

    @field_validator(
        "material", "manufacturer", "variant", "color_name", "shop_code", mode="before"
    )
    @classmethod
    def stripped(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("rfid")
    @classmethod
    def identity(cls, value: str | None) -> str | None:
        if not value or not value.strip().strip("0"):
            return None
        return value.strip().upper()

    @field_validator("image_url")
    @classmethod
    def image(cls, value: str | None) -> str | None:
        if not value:
            return None
        if re.fullmatch(r"/api/v1/(?:products|assets|filament)/images/[A-Za-z0-9_.-]+", value):
            return value
        from pydantic import AnyHttpUrl, TypeAdapter

        url = TypeAdapter(AnyHttpUrl).validate_python(value)
        if url.username or url.password:
            raise ValueError("Bildadresse ohne Zugangsdaten angeben")
        return str(url)


class SpoolRead(SpoolWrite):
    id: UUID
    label_code: str
    location_name: str | None
    image_source_url: str | None
    image_verified: bool
    cloud_account: str | None
    cloud_id: str | None
    cloud_present: bool | None
    cloud_sync_at: datetime | None
    cloud_product_code: str
    printer_serial: str | None
    ams_id: str | None
    slot_id: str | None
    mount_source: str | None
    mount_observed_at: datetime | None
    last_seen_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class FilamentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    region: Literal["global", "cn"] = "global"
    interval_minutes: int = Field(default=30, ge=5, le=1440)
    public_url: str | None = Field(default=None, max_length=180)
    printer_serials: list[str] = Field(default_factory=list, max_length=20)
    mqtt_enabled: bool = False

    @field_validator("printer_serials")
    @classmethod
    def serials(cls, values: list[str]) -> list[str]:
        if any(not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", v.strip()) for v in values):
            raise ValueError("Ungültige Druckerkennung")
        return list(dict.fromkeys(v.strip() for v in values))

    @field_validator("public_url")
    @classmethod
    def public_address(cls, value: str | None) -> str | None:
        if not value:
            return None
        from pydantic import AnyHttpUrl, TypeAdapter

        url = TypeAdapter(AnyHttpUrl).validate_python(value)
        if url.username or url.password or url.query or url.fragment or url.path not in ("", "/"):
            raise ValueError("Öffentliche Adresse ohne Unterpfad oder Zugangsdaten angeben")
        return str(url).rstrip("/")


class CloudLogin(BaseModel):
    account: str = Field(min_length=3, max_length=255)
    password: SecretStr | None = None
    code: SecretStr | None = None
    access_token: SecretStr | None = None
    region: Literal["global", "cn"] = "global"


class SnapshotImport(BaseModel):
    spools: list[dict[str, Any]] = Field(max_length=5000)
    complete: bool = False
    account_reference: str = Field(default="offline-import", min_length=1, max_length=100)


class LabelRequest(BaseModel):
    ids: list[UUID] = Field(min_length=1, max_length=100)
    format: Literal["pdf", "jpg"] = "pdf"


class SlotBinding(BaseModel):
    spool_id: UUID | None = None
