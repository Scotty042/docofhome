from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, UniqueConstraint, text
from sqlmodel import Field, SQLModel


class SmartMeterMeasurementPoint(SQLModel, table=True):
    """Non-conductive CT clamp measurement attached to an electrical connection."""

    __tablename__ = "smart_meter_measurement_points"
    __table_args__ = (
        CheckConstraint(
            "phase IS NULL OR phase IN ('L1', 'L2', 'L3', 'N')",
            name="ck_smart_meter_measurement_points_phase",
        ),
        CheckConstraint(
            "direction IN ('unspecified', 'source_to_target', 'target_to_source')",
            name="ck_smart_meter_measurement_points_direction",
        ),
        CheckConstraint(
            "transformer_nominal_current_a IS NULL OR "
            "(transformer_nominal_current_a > 0 AND transformer_nominal_current_a <= 100000)",
            name="ck_smart_meter_measurement_points_nominal_current",
        ),
        Index(
            "uq_smart_meter_measurement_points_active_channel",
            "smart_meter_asset_id",
            "channel_name",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    smart_meter_asset_id: UUID = Field(foreign_key="assets.id", index=True)
    connection_id: UUID = Field(foreign_key="electrical_connections.id", index=True)
    channel_name: str = Field(max_length=50)
    name: str = Field(max_length=150)
    phase: str | None = Field(default=None, max_length=2)
    direction: str = Field(default="unspecified", max_length=20)
    inverted: bool = False
    transformer_nominal_current_a: float | None = Field(default=None, gt=0, le=100000)
    transformer_ratio: str | None = Field(default=None, max_length=80)
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)


class SmartMeterMeasurementEntity(SQLModel, table=True):
    __tablename__ = "smart_meter_measurement_entities"
    __table_args__ = (
        CheckConstraint(
            "role IN ('power', 'current', 'voltage', 'energy', 'energy_import', "
            "'energy_export', 'frequency', 'power_factor', 'additional')",
            name="ck_smart_meter_measurement_entities_role",
        ),
        CheckConstraint(
            "length(trim(entity_id)) BETWEEN 3 AND 255 AND instr(entity_id, '.') > 1",
            name="ck_smart_meter_measurement_entities_entity_id",
        ),
        UniqueConstraint(
            "measurement_point_id",
            "entity_id",
            name="uq_smart_meter_measurement_entities_point_entity",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    measurement_point_id: UUID = Field(
        foreign_key="smart_meter_measurement_points.id",
        index=True,
    )
    entity_id: str = Field(index=True, max_length=255)
    role: str = Field(max_length=30)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
