from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ElectricalCircuitWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    distribution_id: UUID
    protective_device_id: UUID | None = None
    protective_device_asset_id: UUID | None = None
    name: str = Field(min_length=1, max_length=150)
    circuit_number: str | None = Field(default=None, max_length=50)
    description: str | None = None
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Circuit name must not be empty")
        return normalized

    @field_validator("circuit_number", "description", "notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()

    @model_validator(mode="after")
    def exactly_one_protective_device_reference(self) -> "ElectricalCircuitWrite":
        references = (
            self.protective_device_id is not None,
            self.protective_device_asset_id is not None,
        )
        if sum(references) != 1:
            raise ValueError(
                "Wähle genau eine konkrete Sicherung oder ein FI/LS-Schutzgerät aus."
            )
        return self


class ElectricalCircuitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    distribution_id: UUID
    distribution_name: str
    protective_device_id: UUID | None
    protective_device_asset_id: UUID | None
    protective_device_name: str | None
    protective_device_code: str | None
    protective_device_type: str | None = None
    protective_device_rating: str | None = None
    protective_device_position: str | None = None
    protective_device_phases: list[str] = Field(default_factory=list)
    protective_device_assignment_missing: bool = False
    name: str
    circuit_number: str | None
    description: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class ElectricalCircuitAssetWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: UUID


class ElectricalCircuitAssetRead(BaseModel):
    link_id: UUID
    circuit_id: UUID
    asset_id: UUID
    asset_name: str
    asset_code: str
    asset_status: str
    asset_type_name: str
    location_name: str | None
    asset_deleted_at: datetime | None
    assigned_at: datetime
    removed_at: datetime | None


class ElectricalProtectiveDeviceOptionRead(BaseModel):
    id: UUID
    reference_type: Literal["legacy_device", "asset"]
    label: str
    device_type: str
    rated_current_a: float | None
    characteristic: str | None
    position: str
    phases: list[str] = Field(default_factory=list)
    occupied: bool = False
    occupied_by_circuit_id: UUID | None = None
    occupied_by_circuit_name: str | None = None
