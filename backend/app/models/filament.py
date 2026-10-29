from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


class FilamentSpool(SQLModel, table=True):
    __tablename__ = "filament_spools"
    __table_args__ = (
        UniqueConstraint("cloud_account", "cloud_id", name="uq_filament_cloud_identity"),
        CheckConstraint("condition IN ('sealed','open')", name="ck_filament_condition"),
        CheckConstraint("remaining_g IS NULL OR remaining_g >= 0", name="ck_filament_remaining"),
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    label_code: str = Field(unique=True, index=True, max_length=40)
    manufacturer: str = Field(default="", max_length=100)
    material: str = Field(max_length=100, index=True)
    variant: str = Field(default="", max_length=200)
    color_name: str = Field(default="", max_length=200)
    color_hex: str = Field(default="#808080", max_length=9)
    shop_code: str = Field(default="", max_length=100)
    condition: str = Field(default="sealed", max_length=20)
    initial_g: float | None = None
    remaining_g: float | None = None
    remaining_percent: float | None = None
    location_id: UUID | None = Field(default=None, foreign_key="locations.id", index=True)
    storage_note: str = Field(default="", max_length=300)
    reorder: bool = False
    reorder_note: str = Field(default="", max_length=1000)
    notes: str = Field(default="", sa_type=Text)
    image_url: str | None = Field(default=None, max_length=1000)
    image_source_url: str | None = Field(default=None, max_length=1000)
    image_verified: bool = False
    cloud_account: str | None = Field(default=None, max_length=64)
    cloud_id: str | None = Field(default=None, max_length=100)
    rfid: str | None = Field(default=None, max_length=100, index=True)
    cloud_present: bool | None = None
    cloud_sync_at: datetime | None = None
    cloud_product_code: str = Field(default="", max_length=100)
    printer_serial: str | None = Field(default=None, max_length=100)
    ams_id: str | None = Field(default=None, max_length=100)
    slot_id: str | None = Field(default=None, max_length=100)
    mount_source: str | None = Field(default=None, max_length=20)
    mount_observed_at: datetime | None = None
    last_seen_at: datetime | None = None
    archived_at: datetime | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FilamentSlot(SQLModel, table=True):
    __tablename__ = "filament_slots"
    __table_args__ = (
        UniqueConstraint("printer_serial", "ams_id", "slot_id", name="uq_filament_slot"),
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    printer_serial: str = Field(max_length=100)
    ams_id: str = Field(max_length=100)
    slot_id: str = Field(max_length=100)
    spool_id: UUID | None = Field(default=None, foreign_key="filament_spools.id")
    rfid: str | None = Field(default=None, max_length=100)
    tag_uid: str | None = Field(default=None, max_length=100)
    material: str = Field(default="", max_length=100)
    color_hex: str = Field(default="#808080", max_length=9)
    remaining_percent: float | None = None
    occupied: bool = False
    manual_binding: bool = False
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
