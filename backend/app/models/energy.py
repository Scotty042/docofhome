from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, Text, text
from sqlmodel import Field, SQLModel


class EnergyConfiguration(SQLModel, table=True):
    __tablename__ = "energy_configurations"

    id: int = Field(default=1, primary_key=True)
    grid_connection_name: str | None = Field(default=None, max_length=200)
    grid_operator: str | None = Field(default=None, max_length=200)
    energy_supplier: str | None = Field(default=None, max_length=200)
    metering_point_id: str | None = Field(default=None, max_length=200)
    connection_capacity_kw: float | None = Field(default=None, gt=0, le=100000)
    grid_import_meter_id: UUID | None = Field(
        default=None, foreign_key="consumption_meters.id", index=True
    )
    pv_generation_meter_id: UUID | None = Field(
        default=None, foreign_key="consumption_meters.id", index=True
    )
    grid_export_meter_id: UUID | None = Field(
        default=None, foreign_key="consumption_meters.id", index=True
    )
    notes: str | None = Field(default=None, sa_type=Text)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EnergyComponent(SQLModel, table=True):
    __tablename__ = "energy_components"
    __table_args__ = (
        CheckConstraint(
            "component_type IN ('pv_source', 'inverter', 'storage')",
            name="ck_energy_components_type",
        ),
        CheckConstraint("sort_order >= 0", name="ck_energy_components_sort_order"),
        Index(
            "uq_energy_components_active_name_type",
            "component_type",
            "name",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    component_type: str = Field(index=True, max_length=30)
    name: str = Field(index=True, max_length=200)
    asset_id: UUID | None = Field(default=None, foreign_key="assets.id", index=True)
    manufacturer: str | None = Field(default=None, max_length=200)
    model: str | None = Field(default=None, max_length=200)
    serial_number: str | None = Field(default=None, max_length=200)
    rated_power_kw: float | None = Field(default=None, gt=0, le=100000)
    capacity_kwh: float | None = Field(default=None, gt=0, le=1000000)
    sort_order: int = Field(default=100, ge=0, index=True)
    notes: str | None = Field(default=None, sa_type=Text)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)
