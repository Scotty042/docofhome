from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class HomeAssistantObjectType(StrEnum):
    DEVICE = "device"
    ENTITY = "entity"


class HomeAssistantEntityRole(StrEnum):
    PRIMARY_LIVE = "primary_live"
    TOTAL_POWER = "total_power"
    VOLTAGE = "voltage"
    CURRENT = "current"
    ENERGY = "energy"
    POWER_L1 = "power_l1"
    POWER_L2 = "power_l2"
    POWER_L3 = "power_l3"
    VOLTAGE_L1 = "voltage_l1"
    VOLTAGE_L2 = "voltage_l2"
    VOLTAGE_L3 = "voltage_l3"
    SWITCH_OUTPUT = "switch_output"
    INPUT = "input"
    AVAILABILITY = "availability"
    DIAGNOSTIC = "diagnostic"
    ADDITIONAL = "additional"


class HomeAssistantSelectionMode(StrEnum):
    ALL = "all"
    SELECTED = "selected"


class HomeAssistantSelectionScope(StrEnum):
    VISIBLE = "visible"
    ALL = "all"


class HomeAssistantAreaRead(BaseModel):
    area_id: str
    name: str
    floor_id: str | None = None


class HomeAssistantDeviceRead(BaseModel):
    device_id: str
    name: str
    manufacturer: str | None = None
    model: str | None = None
    model_id: str | None = None
    sw_version: str | None = None
    hw_version: str | None = None
    serial_number: str | None = None
    area_id: str | None = None
    area_name: str | None = None
    entity_count: int = Field(ge=0)
    disabled: bool = False


class HomeAssistantEntityRead(BaseModel):
    entity_id: str
    name: str
    domain: str
    state: str
    unit: str | None = None
    device_class: str | None = None
    icon: str | None = None
    device_id: str | None = None
    device_name: str | None = None
    area_id: str | None = None
    area_name: str | None = None
    platform: str | None = None
    entity_category: str | None = None
    last_changed: datetime | None = None
    last_updated: datetime | None = None
    available: bool = True
    disabled: bool = False


class HomeAssistantSummaryRead(BaseModel):
    location_name: str | None = None
    version: str | None = None
    time_zone: str | None = None
    device_count: int = Field(ge=0)
    entity_count: int = Field(ge=0)
    area_count: int = Field(ge=0)
    unavailable_entity_count: int = Field(ge=0)
    selection_mode: HomeAssistantSelectionMode
    selected_entity_count: int = Field(ge=0)
    visible_device_count: int = Field(ge=0)
    visible_entity_count: int = Field(ge=0)
    registry_available: bool
    warning: str | None = None
    refreshed_at: datetime


class HomeAssistantDeviceListRead(BaseModel):
    items: list[HomeAssistantDeviceRead]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1)


class HomeAssistantEntityListRead(BaseModel):
    items: list[HomeAssistantEntityRead]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1)


class HomeAssistantOverviewRead(BaseModel):
    summary: HomeAssistantSummaryRead
    areas: list[HomeAssistantAreaRead]
    domains: list[str]
    device_classes: list[str] = Field(default_factory=list)
    units: list[str] = Field(default_factory=list)


class HomeAssistantSelectionWrite(BaseModel):
    mode: HomeAssistantSelectionMode
    entity_ids: list[str] = Field(default_factory=list, max_length=10_000)


class HomeAssistantSelectionRead(BaseModel):
    mode: HomeAssistantSelectionMode
    entity_ids: list[str]
    selected_count: int = Field(ge=0)
    updated_at: datetime | None = None


class HomeAssistantAssetLinkWrite(BaseModel):
    asset_id: UUID
    role: HomeAssistantEntityRole = HomeAssistantEntityRole.ADDITIONAL


class HomeAssistantAssetLinkRead(BaseModel):
    id: UUID
    object_type: HomeAssistantObjectType
    external_id: str
    asset_id: UUID
    role: HomeAssistantEntityRole
    asset_name: str
    asset_code: str
    asset_archived: bool
    created_at: datetime
    updated_at: datetime


class HomeAssistantAssetLinkListRead(BaseModel):
    items: list[HomeAssistantAssetLinkRead]


class HomeAssistantEntityBindingWrite(BaseModel):
    external_id: str = Field(min_length=3, max_length=255)
    role: HomeAssistantEntityRole = HomeAssistantEntityRole.ADDITIONAL

    @field_validator("external_id")
    @classmethod
    def normalize_external_id(cls, value: str) -> str:
        normalized = value.strip()
        if "." not in normalized:
            raise ValueError("Eine Home-Assistant-Entität benötigt eine gültige entity_id")
        return normalized


class HomeAssistantAssetBindingsWrite(BaseModel):
    device_ids: list[str] = Field(default_factory=list, max_length=100)
    entities: list[HomeAssistantEntityBindingWrite] = Field(default_factory=list, max_length=1000)

    @field_validator("device_ids")
    @classmethod
    def normalize_device_ids(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values if value.strip()]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Jedes Home-Assistant-Gerät darf nur einmal ausgewählt werden")
        return normalized

    @model_validator(mode="after")
    def unique_entities_and_primary_role(self) -> "HomeAssistantAssetBindingsWrite":
        external_ids = [entity.external_id for entity in self.entities]
        if len(external_ids) != len(set(external_ids)):
            raise ValueError("Jede Home-Assistant-Entität darf nur einmal ausgewählt werden")
        primary = [
            entity
            for entity in self.entities
            if entity.role == HomeAssistantEntityRole.PRIMARY_LIVE
        ]
        if len(primary) > 1:
            raise ValueError("Pro Asset ist nur eine primäre Live-Anzeige zulässig")
        return self


class HomeAssistantAssetBindingsRead(BaseModel):
    asset_id: UUID
    device_links: list[HomeAssistantAssetLinkRead]
    entity_links: list[HomeAssistantAssetLinkRead]
    devices: list[HomeAssistantDeviceRead]
    entities: list[HomeAssistantEntityRead]
    missing_device_ids: list[str]
    missing_entity_ids: list[str]
    warning: str | None = None
    refreshed_at: datetime | None = None


class HomeAssistantExternalId(BaseModel):
    value: str = Field(min_length=1, max_length=255)

    @field_validator("value")
    @classmethod
    def normalize_value(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Home Assistant object ID must not be empty")
        return normalized
