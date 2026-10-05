from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, Numeric, Text
from sqlmodel import Field, SQLModel


class LegoSet(SQLModel, table=True):
    __tablename__ = "lego_sets"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_lego_name"),
        CheckConstraint("parts_count IS NULL OR parts_count >= 0", name="ck_lego_parts"),
        CheckConstraint("purchase_price IS NULL OR purchase_price >= 0", name="ck_lego_price"),
        CheckConstraint("build_status IN ('built','disassembled','sealed')", name="ck_lego_status"),
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    set_number: str = Field(max_length=30, unique=True, index=True)
    name: str = Field(max_length=200, index=True)
    theme: str = Field(default="", max_length=100)
    release_year: int | None = None
    parts_count: int | None = None
    image_url: str | None = Field(default=None, max_length=1000)
    location_id: UUID | None = Field(default=None, foreign_key="locations.id", index=True)
    storage_note: str = Field(default="", max_length=300)
    condition: str = Field(default="", max_length=100)
    build_status: str = Field(default="disassembled", max_length=20)
    complete: bool | None = None
    box_present: bool | None = None
    instructions_present: bool | None = None
    purchase_date: date | None = None
    purchase_price: Decimal | None = Field(default=None, sa_column=Column(Numeric(12, 2)))
    seller: str = Field(default="", max_length=200)
    width_cm: float | None = None
    depth_cm: float | None = None
    height_cm: float | None = None
    dimensions_note: str = Field(default="", max_length=500)
    source_url: str | None = Field(default=None, max_length=1000)
    researched_at: date | None = None
    notes: str = Field(default="", sa_type=Text)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
