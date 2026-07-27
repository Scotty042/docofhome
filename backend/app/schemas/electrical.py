from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.electrical_layout import (
    DistributionAreaRead,
    DistributionAreaType,
    DistributionAreaWrite,
    DistributionLayoutMode,
    DistributionSectionRead,
    DistributionSectionWrite,
    ElectricalPhase,
)


class ElectricalRole(StrEnum):
    DISTRIBUTION = "distribution"
    PROTECTIVE_DEVICE = "protective_device"


class DistributionType(StrEnum):
    MAIN = "main"
    SUB = "sub"


class ProtectiveDeviceType(StrEnum):
    FUSE = "fuse"
    RCD = "rcd"
    MCB = "mcb"
    RCBO = "rcbo"
    SPD = "spd"


class ElectricalAssetRead(BaseModel):
    id: UUID
    name: str
    jarvis_code: str
    location_id: UUID
    location_path: str
    status: str
    effective_module_width: int | None
    asset_type_name: str = "Unbekannter Asset-Typ"
    effective_breaker_characteristic: str | None = None
    effective_rated_current_a: float | None = None
    technical_short_label: str | None = None


class DistributionWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: UUID
    parent_distribution_id: UUID | None = None
    distribution_type: DistributionType
    layout_mode: DistributionLayoutMode = DistributionLayoutMode.ROWS
    designation: str | None = Field(default=None, max_length=150)
    rows: int | None = Field(default=None, ge=1, le=100)
    modules_per_row: int | None = Field(default=None, ge=1, le=1000)
    description: str | None = None
    notes: str | None = None

    @field_validator("designation", "description", "notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _optional_text(value)

    @model_validator(mode="after")
    def hierarchy_and_layout_are_valid(self) -> "DistributionWrite":
        if self.distribution_type == DistributionType.MAIN and self.parent_distribution_id:
            raise ValueError("A main distribution must not have a parent")
        if self.distribution_type == DistributionType.SUB and not self.parent_distribution_id:
            raise ValueError("A subdistribution requires a parent")
        if self.layout_mode == DistributionLayoutMode.SECTIONS and (
            self.rows is not None or self.modules_per_row is not None
        ):
            raise ValueError("A sections layout stores capacity on its individual areas")
        return self


class DistributionMoveWrite(BaseModel):
    parent_distribution_id: UUID | None = None


class DistributionBreadcrumbRead(BaseModel):
    id: UUID
    display_name: str


class DistributionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    role: ElectricalRole
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    asset: ElectricalAssetRead
    parent_distribution_id: UUID | None
    distribution_type: DistributionType
    layout_mode: DistributionLayoutMode
    designation: str | None
    display_name: str
    rows: int | None
    modules_per_row: int | None
    description: str | None
    notes: str | None
    breadcrumbs: list[DistributionBreadcrumbRead]
    direct_subdistribution_count: int
    direct_protective_device_count: int


class DistributionTreeNode(DistributionRead):
    children: list["DistributionTreeNode"] = Field(default_factory=list)


class ProtectiveDeviceWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: UUID
    distribution_id: UUID
    area_id: UUID | None = None
    device_type: ProtectiveDeviceType
    row_number: int | None = Field(default=None, ge=1, le=100)
    start_position: int | None = Field(default=None, ge=1, le=1000)
    module_width: int | None = Field(default=None, ge=1, le=100)
    rated_current_a: float | None = Field(default=None, gt=0, le=10000)
    residual_current_ma: float | None = Field(default=None, gt=0, le=100000)
    characteristic: str | None = Field(default=None, max_length=30)
    poles: int | None = Field(default=None, ge=1, le=12)
    breaking_capacity_ka: float | None = Field(default=None, gt=0, le=1000)
    rcd_type: str | None = Field(default=None, max_length=80)
    fuse_type: str | None = Field(default=None, max_length=80)
    spd_type: str | None = Field(default=None, max_length=80)
    assigned_rcd_id: UUID | None = None
    neutral_rail_id: UUID | None = None
    description: str | None = None
    notes: str | None = None

    @field_validator(
        "characteristic",
        "rcd_type",
        "fuse_type",
        "spd_type",
        "description",
        "notes",
    )
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _optional_text(value)

    @model_validator(mode="after")
    def position_is_complete(self) -> "ProtectiveDeviceWrite":
        row_and_start = (self.row_number, self.start_position)
        if any(value is not None for value in row_and_start) and any(
            value is None for value in row_and_start
        ):
            raise ValueError("row_number and start_position must be supplied together")
        if self.row_number is None and self.module_width is not None:
            raise ValueError("module_width requires row_number and start_position")
        return self


class ProtectiveDeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    role: ElectricalRole
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    asset: ElectricalAssetRead
    distribution_id: UUID
    distribution_name: str
    area_id: UUID | None = None
    area_name: str | None = None
    device_type: ProtectiveDeviceType
    row_number: int | None
    start_position: int | None
    module_width: int | None
    rated_current_a: float | None
    residual_current_ma: float | None
    characteristic: str | None
    poles: int | None
    breaking_capacity_ka: float | None
    rcd_type: str | None
    fuse_type: str | None
    spd_type: str | None
    assigned_rcd_id: UUID | None
    assigned_rcd_name: str | None = None
    neutral_rail_id: UUID | None
    neutral_rail_name: str | None = None
    effective_rcd_id: UUID | None = None
    effective_rcd_name: str | None = None
    effective_neutral_rail_id: UUID | None = None
    effective_neutral_rail_name: str | None = None
    busbar_component_id: UUID | None = None
    busbar_component_name: str | None = None
    calculated_phases: list[ElectricalPhase] = Field(default_factory=list)
    group_warnings: list[str] = Field(default_factory=list)
    description: str | None
    notes: str | None


class DistributionDetailRead(DistributionRead):
    sections: list[DistributionSectionRead] = Field(default_factory=list)
    protective_devices: list[ProtectiveDeviceRead]


class AvailableAssetRead(BaseModel):
    id: UUID
    name: str
    jarvis_code: str
    location_id: UUID
    location_path: str
    effective_module_width: int | None


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


__all__ = [
    "AvailableAssetRead",
    "DistributionAreaRead",
    "DistributionAreaType",
    "DistributionAreaWrite",
    "DistributionBreadcrumbRead",
    "DistributionDetailRead",
    "DistributionLayoutMode",
    "DistributionMoveWrite",
    "DistributionRead",
    "DistributionSectionRead",
    "DistributionSectionWrite",
    "DistributionTreeNode",
    "DistributionType",
    "DistributionWrite",
    "ElectricalAssetRead",
    "ElectricalRole",
    "ProtectiveDeviceRead",
    "ProtectiveDeviceType",
    "ProtectiveDeviceWrite",
]
