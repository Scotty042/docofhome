from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SmartMeterMeasurementPhase(StrEnum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    N = "N"


class SmartMeterMeasurementDirection(StrEnum):
    UNSPECIFIED = "unspecified"
    SOURCE_TO_TARGET = "source_to_target"
    TARGET_TO_SOURCE = "target_to_source"


class SmartMeterMeasurementEntityRole(StrEnum):
    POWER = "power"
    CURRENT = "current"
    VOLTAGE = "voltage"
    ENERGY = "energy"
    ENERGY_IMPORT = "energy_import"
    ENERGY_EXPORT = "energy_export"
    FREQUENCY = "frequency"
    POWER_FACTOR = "power_factor"
    ADDITIONAL = "additional"


class SmartMeterMeasurementEntityWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(min_length=3, max_length=255)
    role: SmartMeterMeasurementEntityRole = SmartMeterMeasurementEntityRole.ADDITIONAL

    @field_validator("entity_id")
    @classmethod
    def normalize_entity_id(cls, value: str) -> str:
        normalized = value.strip()
        if "." not in normalized or normalized.startswith(".") or normalized.endswith("."):
            raise ValueError("Eine Home-Assistant-Entität benötigt eine gültige entity_id")
        return normalized


class SmartMeterMeasurementPointWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    connection_id: UUID
    channel_name: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    phase: SmartMeterMeasurementPhase | None = None
    direction: SmartMeterMeasurementDirection = SmartMeterMeasurementDirection.UNSPECIFIED
    inverted: bool = False
    transformer_nominal_current_a: float | None = Field(default=None, gt=0, le=100000)
    transformer_ratio: str | None = Field(default=None, max_length=80)
    notes: str | None = None
    entities: list[SmartMeterMeasurementEntityWrite] = Field(default_factory=list, max_length=50)

    @field_validator("channel_name", "name")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Die Bezeichnung darf nicht leer sein")
        return normalized

    @field_validator("transformer_ratio", "notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def entities_are_unique(self) -> "SmartMeterMeasurementPointWrite":
        entity_ids = [item.entity_id for item in self.entities]
        if len(entity_ids) != len(set(entity_ids)):
            raise ValueError("Jede Home-Assistant-Entität darf pro Messpunkt nur einmal vorkommen")
        roles = [
            item.role
            for item in self.entities
            if item.role != SmartMeterMeasurementEntityRole.ADDITIONAL
        ]
        if len(roles) != len(set(roles)):
            raise ValueError("Jede Messrolle darf pro Messpunkt nur einmal vergeben werden")
        return self


class SmartMeterMeasurementEntityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_id: str
    role: SmartMeterMeasurementEntityRole
    created_at: datetime
    updated_at: datetime


class SmartMeterMeasurementPointRead(BaseModel):
    id: UUID
    smart_meter_asset_id: UUID
    smart_meter_asset_name: str
    smart_meter_asset_code: str
    connection_id: UUID
    connection_source_name: str
    connection_target_name: str
    connection_label: str | None
    channel_name: str
    name: str
    phase: SmartMeterMeasurementPhase | None
    direction: SmartMeterMeasurementDirection
    inverted: bool
    transformer_nominal_current_a: float | None
    transformer_ratio: str | None
    notes: str | None
    entities: list[SmartMeterMeasurementEntityRead]
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
