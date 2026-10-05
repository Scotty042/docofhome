import re
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class LegoSetWrite(BaseModel):
    set_number: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=200)
    theme: str = Field(default="", max_length=100)
    release_year: int | None = Field(default=None, ge=1949, le=2200)
    parts_count: int | None = Field(default=None, ge=0, le=10000000)
    image_url: str | None = Field(default=None, max_length=1000)
    location_id: UUID | None = None
    storage_note: str = Field(default="", max_length=300)
    condition: str = Field(default="", max_length=100)
    build_status: Literal["built", "disassembled", "sealed"] = "disassembled"
    complete: bool | None = None
    box_present: bool | None = None
    instructions_present: bool | None = None
    purchase_date: date | None = None
    purchase_price: Decimal | None = Field(default=None, ge=0, le=9999999999, decimal_places=2)
    seller: str = Field(default="", max_length=200)
    width_cm: float | None = Field(default=None, gt=0, le=100000, allow_inf_nan=False)
    depth_cm: float | None = Field(default=None, gt=0, le=100000, allow_inf_nan=False)
    height_cm: float | None = Field(default=None, gt=0, le=100000, allow_inf_nan=False)
    dimensions_note: str = Field(default="", max_length=500)
    source_url: str | None = Field(default=None, max_length=1000)
    researched_at: date | None = None
    notes: str = Field(default="", max_length=50000)

    @field_validator("set_number", mode="before")
    @classmethod
    def normalize_number(cls, value: object) -> str:
        text = str(value).strip()
        if not re.fullmatch(r"\d{1,20}(?:-\d{1,3})?", text):
            raise ValueError("Setnummer muss numerisch sein, optional mit Variante (z. B. 10305-1)")
        # The catalog suffix -1 and bare number refer to the same set.
        number, _, variant = text.partition("-")
        return str(int(number)) + (f"-{int(variant)}" if variant and int(variant) != 1 else "")

    @field_validator(
        "name",
        "theme",
        "storage_note",
        "condition",
        "seller",
        "dimensions_note",
        "notes",
        mode="before",
    )
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("source_url", "image_url")
    @classmethod
    def validate_url(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None or not value.strip():
            return None
        if info.field_name == "image_url" and re.fullmatch(
            r"/api/v1/(?:products|assets)/images/[A-Za-z0-9_.-]+", value
        ):
            return value
        from pydantic import AnyHttpUrl, TypeAdapter

        url = TypeAdapter(AnyHttpUrl).validate_python(value.strip())
        if url.username or url.password:
            raise ValueError("URL darf keine Zugangsdaten enthalten")
        return str(url)


class LegoSetRead(LegoSetWrite):
    id: UUID
    location_name: str | None = None
    created_at: datetime
    updated_at: datetime


class LegoDashboard(BaseModel):
    sets_count: int
    purchase_total: Decimal
    currency: Literal["EUR"] = "EUR"
    missing_prices: int
    parts_total: int
    missing_parts: int
