from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, text
from sqlmodel import Field, SQLModel


class AssetEngineRecord(SQLModel):
    """Shared persistent fields for soft-deletable asset engine records."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)


class AssetType(AssetEngineRecord, table=True):
    __tablename__ = "asset_types"
    __table_args__ = (
        CheckConstraint(
            "module_width IS NULL OR (module_width >= 1 AND module_width <= 100)",
            name="ck_asset_types_module_width",
        ),
        CheckConstraint(
            "breaker_characteristic IS NULL OR "
            "breaker_characteristic IN ('B', 'C', 'D', 'K', 'Z')",
            name="ck_asset_types_breaker_characteristic",
        ),
        CheckConstraint(
            "rated_current_a IS NULL OR (rated_current_a > 0 AND rated_current_a <= 10000)",
            name="ck_asset_types_rated_current",
        ),
        CheckConstraint(
            "coil_voltage_v IS NULL OR (coil_voltage_v > 0 AND coil_voltage_v <= 10000)",
            name="ck_asset_types_coil_voltage",
        ),
        CheckConstraint(
            "coil_voltage_type IS NULL OR coil_voltage_type IN ('AC', 'DC')",
            name="ck_asset_types_coil_voltage_type",
        ),
        CheckConstraint(
            "contact_count IS NULL OR (contact_count >= 1 AND contact_count <= 100)",
            name="ck_asset_types_contact_count",
        ),
        CheckConstraint(
            "contact_type IS NULL OR "
            "contact_type IN ('normally_open', 'normally_closed', 'changeover')",
            name="ck_asset_types_contact_type",
        ),
    )

    name: str = Field(index=True, max_length=100)
    code_prefix: str = Field(index=True, max_length=20, unique=True)
    description: str | None = None
    icon: str | None = Field(default=None, max_length=100)
    module_width: int | None = Field(default=None, ge=1, le=100)
    breaker_characteristic: str | None = Field(default=None, max_length=2)
    rated_current_a: float | None = Field(default=None, gt=0, le=10000)
    coil_voltage_v: float | None = Field(default=None, gt=0, le=10000)
    coil_voltage_type: str | None = Field(default=None, max_length=2)
    contact_count: int | None = Field(default=None, ge=1, le=100)
    contact_type: str | None = Field(default=None, max_length=30)


class Product(AssetEngineRecord, table=True):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(
            "image_source IN ('url', 'upload', 'immich', 'online')",
            name="ck_products_image_source",
        ),
        CheckConstraint(
            "module_width IS NULL OR (module_width >= 1 AND module_width <= 100)",
            name="ck_products_module_width",
        ),
    )

    name: str = Field(index=True, max_length=150)
    manufacturer: str | None = Field(default=None, index=True, max_length=150)
    model_number: str | None = Field(default=None, index=True, max_length=150)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=1000)
    image_source: str = Field(default="url", max_length=20)
    image_reference: str | None = Field(default=None, max_length=1000)
    din_rail_mount: bool = False
    module_width: int | None = Field(default=None, ge=1, le=100)
    asset_type_id: UUID | None = Field(default=None, foreign_key="asset_types.id", index=True)


class Location(AssetEngineRecord, table=True):
    __tablename__ = "locations"
    __table_args__ = (
        CheckConstraint(
            "location_type IN ('building', 'floor', 'room', 'area', 'cabinet', "
            "'installation_point', 'outdoor') AND "
            "((parent_id IS NULL AND location_type = 'building') OR "
            "(parent_id IS NOT NULL AND location_type <> 'building'))",
            name="ck_locations_type_and_hierarchy",
        ),
        Index(
            "uq_locations_single_active_root",
            "location_type",
            unique=True,
            sqlite_where=text("parent_id IS NULL AND deleted_at IS NULL"),
        ),
    )

    name: str = Field(index=True, max_length=150)
    location_type: str = Field(default="area", index=True, max_length=30)
    description: str | None = None
    parent_id: UUID | None = Field(default=None, foreign_key="locations.id", index=True)
    short_name: str | None = Field(default=None, index=True, max_length=80)
    sort_order: int | None = Field(default=None, index=True, ge=0)
    notes: str | None = None


class Label(AssetEngineRecord, table=True):
    __tablename__ = "labels"

    name: str = Field(index=True, max_length=100)
    normalized_name: str = Field(index=True, max_length=100, unique=True)
    color: str = Field(default="#26c6da", max_length=7)


class Asset(AssetEngineRecord, table=True):
    __tablename__ = "assets"
    __table_args__ = (
        CheckConstraint(
            "module_width IS NULL OR (module_width >= 1 AND module_width <= 100)",
            name="ck_assets_module_width",
        ),
        CheckConstraint(
            "breaker_characteristic IS NULL OR "
            "breaker_characteristic IN ('B', 'C', 'D', 'K', 'Z')",
            name="ck_assets_breaker_characteristic",
        ),
        CheckConstraint(
            "rated_current_a IS NULL OR (rated_current_a > 0 AND rated_current_a <= 10000)",
            name="ck_assets_rated_current",
        ),
        CheckConstraint(
            "coil_voltage_v IS NULL OR (coil_voltage_v > 0 AND coil_voltage_v <= 10000)",
            name="ck_assets_coil_voltage",
        ),
        CheckConstraint(
            "coil_voltage_type IS NULL OR coil_voltage_type IN ('AC', 'DC')",
            name="ck_assets_coil_voltage_type",
        ),
        CheckConstraint(
            "contact_count IS NULL OR (contact_count >= 1 AND contact_count <= 100)",
            name="ck_assets_contact_count",
        ),
        CheckConstraint(
            "contact_type IS NULL OR "
            "contact_type IN ('normally_open', 'normally_closed', 'changeover')",
            name="ck_assets_contact_type",
        ),
        Index(
            "uq_assets_inventory_number_global",
            "inventory_number",
            unique=True,
            sqlite_where=text("inventory_number IS NOT NULL AND trim(inventory_number) <> ''"),
        ),
    )

    name: str = Field(index=True, max_length=150)
    jarvis_code: str = Field(index=True, max_length=32, unique=True)
    description: str | None = None
    asset_type_id: UUID = Field(foreign_key="asset_types.id", index=True)
    product_id: UUID | None = Field(default=None, foreign_key="products.id", index=True)
    location_id: UUID | None = Field(default=None, foreign_key="locations.id", index=True)
    serial_number: str | None = Field(default=None, index=True, max_length=200)
    inventory_number: str | None = Field(default=None, index=True, max_length=200)
    module_width: int | None = Field(default=None, ge=1, le=100)
    breaker_characteristic: str | None = Field(default=None, max_length=2)
    rated_current_a: float | None = Field(default=None, gt=0, le=10000)
    coil_voltage_v: float | None = Field(default=None, gt=0, le=10000)
    coil_voltage_type: str | None = Field(default=None, max_length=2)
    contact_count: int | None = Field(default=None, ge=1, le=100)
    contact_type: str | None = Field(default=None, max_length=30)
    status: str = Field(default="active", index=True, max_length=30)


class AssetLabelLink(SQLModel, table=True):
    __tablename__ = "asset_label_links"

    asset_id: UUID = Field(foreign_key="assets.id", primary_key=True)
    label_id: UUID = Field(foreign_key="labels.id", primary_key=True)


class Relationship(AssetEngineRecord, table=True):
    __tablename__ = "relationships"

    source_asset_id: UUID = Field(foreign_key="assets.id", index=True)
    target_asset_id: UUID = Field(foreign_key="assets.id", index=True)
    relationship_type: str = Field(index=True, max_length=100)
    description: str | None = None


class AssetCodeCounter(SQLModel, table=True):
    __tablename__ = "asset_code_counters"

    prefix: str = Field(primary_key=True, max_length=20)
    next_value: int = Field(default=1, ge=1)
