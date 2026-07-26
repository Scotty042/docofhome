from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ConsumptionMeterType(StrEnum):
    WATER = "water"
    ELECTRICITY_GRID = "electricity_grid"
    ELECTRICITY_PV = "electricity_pv"
    ELECTRICITY_FEED_IN = "electricity_feed_in"
    GAS = "gas"
    HEAT = "heat"
    OIL = "oil"
    OTHER = "other"


class ConsumptionWaterRole(StrEnum):
    NONE = "none"
    MAIN = "main"
    EG_COMPONENT = "eg_component"


class ConsumptionReadingSource(StrEnum):
    MANUAL = "manual"
    CSV = "csv"
    LEGACY_SQLITE = "legacy_sqlite"
    HOME_ASSISTANT = "home_assistant"


class ConsumptionNoteScope(StrEnum):
    GENERAL = "general"
    MONTH = "month"
    YEAR = "year"


class ConsumptionMeterWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=150)
    meter_type: ConsumptionMeterType
    unit: str = Field(min_length=1, max_length=30)
    decimals: int = Field(default=3, ge=0, le=6)
    sort_order: int = Field(default=100, ge=0, le=100000)
    serial_number: str | None = Field(default=None, max_length=200)
    asset_id: UUID | None = None
    location_id: UUID | None = None
    parent_meter_id: UUID | None = None
    home_assistant_entity_id: str | None = Field(default=None, max_length=255)
    home_assistant_power_entity_id: str | None = Field(default=None, max_length=255)
    home_assistant_voltage_entity_id: str | None = Field(default=None, max_length=255)
    water_role: ConsumptionWaterRole = ConsumptionWaterRole.NONE
    primary_for_dashboard: bool = False
    reading_schedule_day: int | None = Field(default=None, ge=1, le=31)
    reading_schedule_last_day: bool = False
    reminder_days: list[int] = Field(default_factory=list, max_length=10)
    notes: str | None = Field(default=None, max_length=20000)

    @field_validator("name", "unit")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Das Feld darf nicht leer sein")
        return normalized

    @field_validator(
        "serial_number",
        "home_assistant_entity_id",
        "home_assistant_power_entity_id",
        "home_assistant_voltage_entity_id",
        "notes",
    )
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()

    @model_validator(mode="after")
    def validate_water_role(self) -> "ConsumptionMeterWrite":
        if (
            self.meter_type != ConsumptionMeterType.WATER
            and self.water_role != ConsumptionWaterRole.NONE
        ):
            raise ValueError("Wasserrollen sind nur für Wasserzähler zulässig")
        if self.reading_schedule_day is not None and self.reading_schedule_last_day:
            raise ValueError("Ablesetag und letzter Monatstag schließen sich aus")
        if len(self.reminder_days) != len(set(self.reminder_days)):
            raise ValueError("Erinnerungstage dürfen nicht doppelt vorkommen")
        if any(day < 1 or day > 31 for day in self.reminder_days):
            raise ValueError("Erinnerungstage müssen zwischen 1 und 31 liegen")
        self.reminder_days.sort()
        return self


class ConsumptionMeterRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    meter_type: ConsumptionMeterType
    unit: str
    decimals: int
    sort_order: int
    serial_number: str | None
    asset_id: UUID | None
    asset_name: str | None
    asset_code: str | None
    location_id: UUID | None
    location_name: str | None
    location_path: str | None
    parent_meter_id: UUID | None
    parent_meter_name: str | None
    home_assistant_entity_id: str | None
    home_assistant_power_entity_id: str | None
    home_assistant_voltage_entity_id: str | None
    water_role: ConsumptionWaterRole
    primary_for_dashboard: bool
    reading_schedule_day: int | None
    reading_schedule_last_day: bool
    reminder_days: list[int]
    notes: str | None
    latest_value: float | None
    latest_measured_at: datetime | None
    reading_count: int = Field(ge=0)
    due_for_reading: bool = False
    archived: bool
    created_at: datetime
    updated_at: datetime


class ConsumptionMeterLiveRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meter_id: UUID
    power_entity_id: str | None
    voltage_entity_id: str | None
    power_w: float | None
    voltage_v: float | None
    power_updated_at: datetime | None
    voltage_updated_at: datetime | None
    available: bool
    warning: str | None = None


class ConsumptionReadingWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meter_id: UUID
    measured_at: datetime
    value: float = Field(ge=0)
    note: str | None = Field(default=None, max_length=5000)
    source: ConsumptionReadingSource = ConsumptionReadingSource.MANUAL
    is_reset: bool = False
    immich_asset_id: UUID | None = None
    immich_original_file_name: str | None = Field(default=None, max_length=500)

    @field_validator("note", "immich_original_file_name")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()


class ConsumptionReadingRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    meter_id: UUID
    meter_name: str
    unit: str
    decimals: int
    measured_at: datetime
    value: float
    previous_value: float | None
    delta: float | None
    note: str | None
    source: ConsumptionReadingSource
    is_reset: bool
    immich_asset_id: UUID | None
    immich_original_file_name: str | None
    immich_thumbnail_url: str | None
    plausibility_warning: bool = False
    plausibility_message: str | None = None
    created_at: datetime
    updated_at: datetime


class ConsumptionNoteWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note_date: datetime
    scope: ConsumptionNoteScope = ConsumptionNoteScope.MONTH
    title: str = Field(min_length=1, max_length=200)
    note: str | None = Field(default=None, max_length=20000)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Der Titel darf nicht leer sein")
        return normalized

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()


class ConsumptionNoteRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    note_date: datetime
    scope: ConsumptionNoteScope
    title: str
    note: str | None
    created_at: datetime
    updated_at: datetime


class ConsumptionSettingsWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reminder_days: int = Field(default=31, ge=1, le=3650)
    plausibility_threshold_percent: int = Field(default=150, ge=100, le=10000)


class ConsumptionSettingsRead(ConsumptionSettingsWrite):
    updated_at: datetime


class ConsumptionPeriodResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float | None
    estimated: bool
    incomplete: bool
    reset_detected: bool


class ConsumptionSeriesPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    period_start: datetime
    period_end: datetime
    result: ConsumptionPeriodResult


class ConsumptionSeries(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    name: str
    meter_id: UUID | None
    meter_type: ConsumptionMeterType
    unit: str
    decimals: int
    virtual: bool
    description: str | None = None
    points: list[ConsumptionSeriesPoint] = Field(default_factory=list)


class ConsumptionStatisticsRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    months: int
    series: list[ConsumptionSeries]


class ConsumptionVirtualResultRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    name: str
    description: str
    unit: str
    decimals: int
    result: ConsumptionPeriodResult


class ConsumptionSummaryRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meter_count: int = Field(ge=0)
    reading_count: int = Field(ge=0)
    readings_last_30_days: int = Field(ge=0)
    meters_without_readings: int = Field(ge=0)
    meters_due_for_reading: int = Field(ge=0)
    last_reading_at: datetime | None
    current_month: list[ConsumptionVirtualResultRead] = Field(default_factory=list)


class ConsumptionImportPreviewRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: str
    file_name: str
    meter_count: int = Field(ge=0)
    reading_count: int = Field(ge=0)
    note_count: int = Field(default=0, ge=0)
    matched_meters: list[str] = Field(default_factory=list)
    missing_meters: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ConsumptionImportResultRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: str
    file_name: str
    meters_created: int = Field(ge=0)
    readings_created: int = Field(ge=0)
    readings_updated: int = Field(ge=0)
    duplicates_skipped: int = Field(ge=0)
    rows_skipped: int = Field(ge=0)
    notes_created: int = Field(default=0, ge=0)
    settings_imported: bool = False
    errors: list[str] = Field(default_factory=list)


class ConsumptionDefaultSeedRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    created: int = Field(ge=0)
    existing: int = Field(ge=0)
    meters: list[ConsumptionMeterRead]


class ConsumptionComparisonRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    medium: str
    name: str
    meter_id: UUID | None
    unit: str | None
    decimals: int
    current_value: float | None
    previous_value: float | None
    difference: float | None
    percent_change: float | None
    trend: str
    comparison_available: bool
    incomplete: bool


class ConsumptionReadingReminderRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meter_id: UUID
    meter_name: str
    unit: str
    due_at: datetime
    days_remaining: int
    status: str
