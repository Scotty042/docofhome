from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.smart_meter import SmartMeterMeasurementPointRead


class ElectricalEndpointKind(StrEnum):
    GRID_CONNECTION = "grid_connection"
    ASSET = "asset"
    DISTRIBUTION = "distribution"
    PROTECTIVE_DEVICE = "protective_device"
    CABINET_COMPONENT = "cabinet_component"
    CIRCUIT = "circuit"


class ElectricalConnectionType(StrEnum):
    UNKNOWN = "unknown"
    CABLE = "cable"
    WIRE = "wire"
    BUSBAR = "busbar"
    INTERNAL = "internal"


class ElectricalPhase(StrEnum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    N = "N"
    PE = "PE"


class ElectricalEndpointRead(BaseModel):
    key: str
    kind: ElectricalEndpointKind
    id: UUID
    name: str
    code: str | None
    type_name: str
    location_name: str | None
    device_type: str | None = None
    effective_phases: list[ElectricalPhase] | None = None
    deleted_at: datetime | None = None


class ElectricalConnectionWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_kind: ElectricalEndpointKind
    source_id: UUID
    target_kind: ElectricalEndpointKind
    target_id: UUID
    connection_type: ElectricalConnectionType = ElectricalConnectionType.UNKNOWN
    label: str | None = Field(default=None, max_length=150)
    phases: list[ElectricalPhase] = Field(default_factory=list, max_length=5)
    cable_type: str | None = Field(default=None, max_length=150)
    cores: int | None = Field(default=None, ge=1, le=100)
    cross_section_mm2: float | None = Field(default=None, gt=0, le=1000)
    length_m: float | None = Field(default=None, gt=0, le=100000)
    route: str | None = None
    notes: str | None = None

    @field_validator("label", "cable_type", "route", "notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()

    @field_validator("phases")
    @classmethod
    def phases_are_unique(
        cls,
        value: list[ElectricalPhase],
    ) -> list[ElectricalPhase]:
        if len(value) != len(set(value)):
            raise ValueError("Each conductor may only be selected once")
        order = {phase: index for index, phase in enumerate(ElectricalPhase)}
        return sorted(value, key=order.__getitem__)

    @model_validator(mode="after")
    def endpoints_are_distinct(self) -> "ElectricalConnectionWrite":
        if self.target_kind == ElectricalEndpointKind.GRID_CONNECTION:
            raise ValueError("Der Netzanschluss kann nur Quelle, nicht Ziel einer Verbindung sein")
        if self.source_kind == self.target_kind and self.source_id == self.target_id:
            raise ValueError("A connection requires two different endpoints")
        return self


class ElectricalConnectionRead(BaseModel):
    id: UUID
    source: ElectricalEndpointRead
    target: ElectricalEndpointRead
    connection_type: ElectricalConnectionType
    label: str | None
    phases: list[ElectricalPhase]
    effective_phases: list[ElectricalPhase]
    phase_warnings: list[str] = Field(default_factory=list)
    cable_type: str | None
    cores: int | None
    cross_section_mm2: float | None
    length_m: float | None
    route: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class ElectricalTopologyNodeRead(BaseModel):
    endpoint: ElectricalEndpointRead
    source_names: list[str]
    incoming_phases: list[ElectricalPhase]
    downstream_protective_device_count: int
    downstream_circuit_count: int
    downstream_asset_count: int


class ElectricalTopologyRead(BaseModel):
    nodes: list[ElectricalTopologyNodeRead]
    connections: list[ElectricalConnectionRead]
    measurement_points: list[SmartMeterMeasurementPointRead] = Field(default_factory=list)
