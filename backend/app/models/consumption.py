from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, Text, text
from sqlmodel import Field, SQLModel


class ConsumptionRecord(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)


class ConsumptionMeter(ConsumptionRecord, table=True):
    __tablename__ = "consumption_meters"
    __table_args__ = (
        CheckConstraint(
            "meter_type IN ('water', 'electricity_grid', 'electricity_pv', "
            "'electricity_feed_in', 'gas', "
            "'heat', 'oil', 'other')",
            name="ck_consumption_meters_type",
        ),
        CheckConstraint(
            "water_role IN ('none', 'main', 'eg_component')",
            name="ck_consumption_meters_water_role",
        ),
        CheckConstraint(
            "meter_type = 'water' OR water_role = 'none'",
            name="ck_consumption_meters_water_role_type",
        ),
        CheckConstraint(
            "decimals >= 0 AND decimals <= 6",
            name="ck_consumption_meters_decimals",
        ),
        CheckConstraint("sort_order >= 0", name="ck_consumption_meters_sort_order"),
        Index(
            "uq_consumption_meters_active_name",
            "name",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
        Index(
            "uq_consumption_meters_active_main_water",
            "water_role",
            unique=True,
            sqlite_where=text("deleted_at IS NULL AND water_role = 'main'"),
        ),
        Index(
            "uq_consumption_meters_active_primary_type",
            "meter_type",
            unique=True,
            sqlite_where=text("deleted_at IS NULL AND primary_for_dashboard = 1"),
        ),
        CheckConstraint(
            "reading_schedule_day IS NULL OR "
            "(reading_schedule_day >= 1 AND reading_schedule_day <= 31)",
            name="ck_consumption_meters_schedule_day",
        ),
        CheckConstraint(
            "NOT (reading_schedule_last_day = 1 AND reading_schedule_day IS NOT NULL)",
            name="ck_consumption_meters_schedule_choice",
        ),
    )

    name: str = Field(index=True, max_length=150)
    meter_type: str = Field(index=True, max_length=30)
    unit: str = Field(max_length=30)
    decimals: int = Field(default=3, ge=0, le=6)
    sort_order: int = Field(default=100, ge=0, index=True)
    serial_number: str | None = Field(default=None, index=True, max_length=200)
    asset_id: UUID | None = Field(default=None, foreign_key="assets.id", index=True)
    location_id: UUID | None = Field(default=None, foreign_key="locations.id", index=True)
    parent_meter_id: UUID | None = Field(
        default=None,
        foreign_key="consumption_meters.id",
        index=True,
    )
    home_assistant_entity_id: str | None = Field(default=None, index=True, max_length=255)
    home_assistant_power_entity_id: str | None = Field(default=None, index=True, max_length=255)
    home_assistant_voltage_entity_id: str | None = Field(default=None, index=True, max_length=255)
    water_role: str = Field(default="none", index=True, max_length=20)
    primary_for_dashboard: bool = Field(default=False, index=True)
    reading_schedule_day: int | None = Field(default=None, ge=1, le=31)
    reading_schedule_last_day: bool = False
    reminder_days_json: str = Field(default="[]", sa_type=Text)
    notes: str | None = Field(default=None, sa_type=Text)


class ConsumptionReading(ConsumptionRecord, table=True):
    __tablename__ = "consumption_readings"
    __table_args__ = (
        CheckConstraint("value >= 0", name="ck_consumption_readings_value"),
        CheckConstraint(
            "source IN ('manual', 'csv', 'legacy_sqlite', 'home_assistant')",
            name="ck_consumption_readings_source",
        ),
        Index(
            "uq_consumption_readings_active_meter_time",
            "meter_id",
            "measured_at",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
        Index(
            "ix_consumption_readings_active_time",
            "measured_at",
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    meter_id: UUID = Field(foreign_key="consumption_meters.id", index=True)
    measured_at: datetime = Field(index=True)
    value: float = Field(ge=0)
    note: str | None = Field(default=None, sa_type=Text)
    source: str = Field(default="manual", index=True, max_length=30)
    is_reset: bool = Field(default=False, index=True)
    immich_asset_id: str | None = Field(default=None, index=True, max_length=36)
    immich_original_file_name: str | None = Field(default=None, max_length=500)


class ConsumptionNote(ConsumptionRecord, table=True):
    __tablename__ = "consumption_notes"
    __table_args__ = (
        CheckConstraint(
            "scope IN ('general', 'month', 'year')",
            name="ck_consumption_notes_scope",
        ),
        Index(
            "ix_consumption_notes_active_date",
            "note_date",
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    note_date: datetime = Field(index=True)
    scope: str = Field(default="month", index=True, max_length=20)
    title: str = Field(max_length=200)
    note: str | None = Field(default=None, sa_type=Text)


class ConsumptionSetting(SQLModel, table=True):
    __tablename__ = "consumption_settings"
    __table_args__ = (
        CheckConstraint(
            "reminder_days >= 1 AND reminder_days <= 3650",
            name="ck_consumption_settings_reminder_days",
        ),
        CheckConstraint(
            "plausibility_threshold_percent >= 100 AND plausibility_threshold_percent <= 10000",
            name="ck_consumption_settings_plausibility_threshold",
        ),
    )

    id: int = Field(default=1, primary_key=True)
    reminder_days: int = Field(default=31, ge=1, le=3650)
    plausibility_threshold_percent: int = Field(default=150, ge=100, le=10000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
