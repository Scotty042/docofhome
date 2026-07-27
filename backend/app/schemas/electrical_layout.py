from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.electrical_topology import ElectricalPhase


class DistributionLayoutMode(StrEnum):
    ROWS = "rows"
    SECTIONS = "sections"
    JUNCTION_BOX = "junction_box"


class DistributionAreaType(StrEnum):
    DEVICE_ROWS = "device_rows"
    METER = "meter"
    CONNECTION = "connection"
    NEUTRAL_RAIL = "neutral_rail"
    PROTECTIVE_EARTH_RAIL = "protective_earth_rail"
    TECHNOLOGY = "technology"
    RESERVE = "reserve"
    COVER = "cover"


class DistributionAreaWidth(StrEnum):
    FULL = "full"
    HALF = "half"


class DistributionAreaSide(StrEnum):
    LEFT = "left"
    RIGHT = "right"


class DistributionSectionWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=150)
    position: int = Field(ge=1, le=50)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Section name must not be empty")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class DistributionAreaWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=150)
    area_type: DistributionAreaType
    position: int = Field(ge=1, le=100)
    rows: int | None = Field(default=None, ge=1, le=100)
    modules_per_row: int | None = Field(default=None, ge=1, le=1000)
    width: DistributionAreaWidth = DistributionAreaWidth.FULL
    side: DistributionAreaSide | None = None
    description: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Area name must not be empty")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def validate_capacity(self) -> "DistributionAreaWrite":
        if self.area_type != DistributionAreaType.DEVICE_ROWS and (
            self.rows is not None or self.modules_per_row is not None
        ):
            raise ValueError("Only a device-row area may define capacity")
        if self.width == DistributionAreaWidth.FULL and self.side is not None:
            raise ValueError("Ein Bereich voller Breite darf keine Seite festlegen")
        if self.width == DistributionAreaWidth.HALF and self.side is None:
            raise ValueError("Bei halber Breite muss links oder rechts ausgewählt werden")
        return self


class DistributionAreaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    section_id: UUID
    name: str
    area_type: DistributionAreaType
    position: int
    rows: int | None
    modules_per_row: int | None
    width: DistributionAreaWidth
    side: DistributionAreaSide | None
    description: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class DistributionSectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    distribution_id: UUID
    name: str
    position: int
    description: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    areas: list[DistributionAreaRead] = Field(default_factory=list)


class ElectricalMeterPlacementWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    area_id: UUID
    position: int = Field(default=1, ge=1, le=100)


class ElectricalMeterPlacementRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    distribution_id: UUID
    area_id: UUID
    area_name: str
    position: int
    source_kind: str
    meter_id: UUID | None
    meter_name: str
    meter_type: str
    unit: str
    serial_number: str | None
    asset_id: UUID | None
    asset_name: str | None
    asset_code: str | None
    location_path: str | None
    latest_value: float | None
    latest_measured_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ElectricalCabinetComponentType(StrEnum):
    PHASE_DISTRIBUTION_BLOCK = "phase_distribution_block"
    BUSBAR = "busbar"
    PHASE_RAIL = "phase_rail"
    NEUTRAL_RAIL = "neutral_rail"
    PROTECTIVE_EARTH_RAIL = "protective_earth_rail"
    TERMINAL_BLOCK = "terminal_block"
    CONNECTION_BLOCK = "connection_block"
    POTENTIAL_DISTRIBUTION = "potential_distribution"
    OTHER = "other"


class ElectricalRailMountingSide(StrEnum):
    ABOVE = "above"
    BELOW = "below"


class ElectricalCabinetComponentWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=150)
    component_type: ElectricalCabinetComponentType
    area_id: UUID | None = None
    row_number: int = Field(ge=1, le=100)
    start_position: int = Field(ge=1, le=1000)
    module_width: int = Field(ge=1, le=100)
    phases: list[ElectricalPhase] = Field(default_factory=list, max_length=5)
    rated_current_a: float | None = Field(default=None, gt=0, le=10000)
    max_cross_section_mm2: float | None = Field(default=None, gt=0, le=1000)
    outgoing_connections: int | None = Field(default=None, ge=1, le=1000)
    linked_rcd_device_id: UUID | None = None
    start_phase: ElectricalPhase | None = None
    mounting_side: ElectricalRailMountingSide | None = None
    description: str | None = None
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_component_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Die Bezeichnung darf nicht leer sein")
        return normalized

    @field_validator("description", "notes")
    @classmethod
    def normalize_optional_component_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("phases")
    @classmethod
    def component_phases_are_unique(
        cls, value: list[ElectricalPhase]
    ) -> list[ElectricalPhase]:
        if len(value) != len(set(value)):
            raise ValueError("Jeder Leiter darf nur einmal ausgewählt werden")
        order = {phase: index for index, phase in enumerate(ElectricalPhase)}
        return sorted(value, key=order.__getitem__)

    @model_validator(mode="after")
    def component_specific_values_are_valid(self) -> "ElectricalCabinetComponentWrite":
        line_phases = [phase for phase in self.phases if phase in {
            ElectricalPhase.L1, ElectricalPhase.L2, ElectricalPhase.L3
        }]
        rail_types = {
            ElectricalCabinetComponentType.BUSBAR,
            ElectricalCabinetComponentType.PHASE_RAIL,
        }
        if self.component_type in rail_types:
            if not line_phases:
                raise ValueError("Eine Kamm-/Phasenschiene benötigt mindestens eine Phase")
            if self.start_phase is None:
                self.start_phase = line_phases[0]
            if self.start_phase not in line_phases:
                raise ValueError("Die Startphase muss auf der Schiene vorhanden sein")
            if self.mounting_side is None:
                self.mounting_side = ElectricalRailMountingSide.BELOW
        else:
            self.start_phase = None
            self.mounting_side = None
        if self.component_type == ElectricalCabinetComponentType.NEUTRAL_RAIL:
            if self.phases != [ElectricalPhase.N]:
                raise ValueError(
                    "Eine N-Schiene muss ausschließlich dem Neutralleiter N "
                    "zugeordnet sein"
                )
        return self


class ElectricalCabinetComponentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    distribution_id: UUID
    distribution_name: str
    area_id: UUID | None
    area_name: str
    name: str
    component_type: ElectricalCabinetComponentType
    row_number: int
    start_position: int
    module_width: int
    phases: list[ElectricalPhase]
    rated_current_a: float | None
    max_cross_section_mm2: float | None
    outgoing_connections: int | None
    linked_rcd_device_id: UUID | None
    linked_rcd_name: str | None
    start_phase: ElectricalPhase | None
    mounting_side: ElectricalRailMountingSide | None
    description: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class ElectricalLiveValueRead(BaseModel):
    entity_id: str
    name: str
    role: str
    state: str
    unit: str | None
    available: bool
    last_updated: datetime | None


class ElectricalAssetPlacementWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    area_id: UUID | None = None
    row_number: int = Field(ge=1, le=100)
    start_position: int = Field(ge=1, le=1000)
    module_width: int | None = Field(default=None, ge=1, le=100)


class ElectricalAssetPlacementRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    distribution_id: UUID
    area_id: UUID | None
    area_name: str
    asset_id: UUID
    asset_name: str
    asset_code: str
    asset_type_name: str = "Unbekannter Asset-Typ"
    product_name: str | None
    location_path: str | None
    row_number: int
    start_position: int
    module_width: int
    effective_breaker_characteristic: str | None = None
    effective_rated_current_a: float | None = None
    technical_short_label: str | None = None
    primary_live_value: ElectricalLiveValueRead | None = None
    live_values: list[ElectricalLiveValueRead] = Field(default_factory=list)
    live_warning: str | None = None
    created_at: datetime
    updated_at: datetime
