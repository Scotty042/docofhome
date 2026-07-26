from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EnergyComponentType(StrEnum):
    PV_SOURCE = "pv_source"
    INVERTER = "inverter"
    STORAGE = "storage"


class EnergyConfigurationWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grid_connection_name: str | None = Field(default=None, max_length=200)
    grid_operator: str | None = Field(default=None, max_length=200)
    energy_supplier: str | None = Field(default=None, max_length=200)
    metering_point_id: str | None = Field(default=None, max_length=200)
    connection_capacity_kw: float | None = Field(default=None, gt=0, le=100000)
    grid_import_meter_id: UUID | None = None
    pv_generation_meter_id: UUID | None = None
    grid_export_meter_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=20000)

    @field_validator(
        "grid_connection_name",
        "grid_operator",
        "energy_supplier",
        "metering_point_id",
        "notes",
    )
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()


class EnergyConfigurationRead(EnergyConfigurationWrite):
    grid_import_meter_name: str | None
    pv_generation_meter_name: str | None
    grid_export_meter_name: str | None
    complete_for_balance: bool
    updated_at: datetime


class EnergyComponentWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component_type: EnergyComponentType
    name: str = Field(min_length=1, max_length=200)
    asset_id: UUID | None = None
    manufacturer: str | None = Field(default=None, max_length=200)
    model: str | None = Field(default=None, max_length=200)
    serial_number: str | None = Field(default=None, max_length=200)
    rated_power_kw: float | None = Field(default=None, gt=0, le=100000)
    capacity_kwh: float | None = Field(default=None, gt=0, le=1000000)
    sort_order: int = Field(default=100, ge=0, le=100000)
    notes: str | None = Field(default=None, max_length=20000)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Der Name darf nicht leer sein")
        return normalized

    @field_validator("manufacturer", "model", "serial_number", "notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()

    @model_validator(mode="after")
    def validate_capacity(self) -> "EnergyComponentWrite":
        if self.component_type != EnergyComponentType.STORAGE and self.capacity_kwh is not None:
            raise ValueError("Eine Speicherkapazität ist nur bei Speichern zulässig")
        return self


class EnergyComponentRead(EnergyComponentWrite):
    id: UUID
    asset_name: str | None
    archived: bool
    created_at: datetime
    updated_at: datetime


class EnergyBalancePeriodRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    period_start: datetime
    period_end: datetime
    grid_import_kwh: float | None
    pv_generation_kwh: float | None
    grid_export_kwh: float | None
    house_consumption_kwh: float | None
    self_consumption_kwh: float | None
    autonomy_percent: float | None
    self_consumption_rate_percent: float | None
    estimated: bool
    incomplete: bool


class EnergyBalanceRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    months: int
    configuration_complete: bool
    periods: list[EnergyBalancePeriodRead]
