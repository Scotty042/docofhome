from datetime import datetime
from enum import StrEnum
from math import ceil
from uuid import UUID

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    field_validator,
    model_validator,
)


class AssetStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class ProductImageSource(StrEnum):
    URL = "url"
    UPLOAD = "upload"
    IMMICH = "immich"
    ONLINE = "online"


class SwitchPortLayout(StrEnum):
    ODD_EVEN = "odd_even"
    SEQUENTIAL_HALVES = "sequential_halves"


class BreakerCharacteristic(StrEnum):
    B = "B"
    C = "C"
    D = "D"
    K = "K"
    Z = "Z"


class CoilVoltageType(StrEnum):
    AC = "AC"
    DC = "DC"


class ContactType(StrEnum):
    NORMALLY_OPEN = "normally_open"
    NORMALLY_CLOSED = "normally_closed"
    CHANGEOVER = "changeover"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class LocationType(StrEnum):
    BUILDING = "building"
    FLOOR = "floor"
    ROOM = "room"
    AREA = "area"
    CABINET = "cabinet"
    INSTALLATION_POINT = "installation_point"
    OUTDOOR = "outdoor"


class RecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class ReferenceRead(BaseModel):
    id: UUID
    name: str




def _normalize_image_url(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    normalized = value.strip()
    if normalized.startswith("/") and not normalized.startswith("//"):
        return normalized
    return str(TypeAdapter(AnyHttpUrl).validate_python(normalized))


def _normalize_image_reference(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return value.strip()


class AssetTypeWrite(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    icon: str | None = Field(default=None, max_length=100)
    image_url: str | None = Field(default=None, max_length=1000)
    image_source: ProductImageSource = ProductImageSource.URL
    image_reference: str | None = Field(default=None, max_length=1000)
    is_meter: bool = False
    switch_port_layout: SwitchPortLayout = SwitchPortLayout.ODD_EVEN
    module_width: int | None = Field(default=None, ge=1, le=100)
    breaker_characteristic: BreakerCharacteristic | None = None
    rated_current_a: float | None = Field(default=None, gt=0, le=10000)
    coil_voltage_v: float | None = Field(default=None, gt=0, le=10000)
    coil_voltage_type: CoilVoltageType | None = None
    contact_count: int | None = Field(default=None, ge=1, le=100)
    contact_type: ContactType | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return _required_text(value, "Asset type name")

    _normalize_image_url = field_validator("image_url")(_normalize_image_url)
    _normalize_image_reference = field_validator("image_reference")(_normalize_image_reference)


class AssetTypeRead(RecordRead):
    name: str
    code_prefix: str
    description: str | None
    icon: str | None
    image_url: str | None = None
    image_source: ProductImageSource = ProductImageSource.URL
    image_reference: str | None = None
    is_meter: bool = False
    switch_port_layout: SwitchPortLayout = SwitchPortLayout.ODD_EVEN
    module_width: int | None
    breaker_characteristic: BreakerCharacteristic | None
    rated_current_a: float | None
    coil_voltage_v: float | None
    coil_voltage_type: CoilVoltageType | None
    contact_count: int | None
    contact_type: ContactType | None


class ProductWrite(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    manufacturer: str | None = Field(default=None, max_length=150)
    model_number: str | None = Field(default=None, max_length=150)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=1000)
    image_source: ProductImageSource = ProductImageSource.URL
    image_reference: str | None = Field(default=None, max_length=1000)
    din_rail_mount: bool = False
    module_width: int | None = Field(default=None, ge=1, le=100)
    asset_type_id: UUID | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return _required_text(value, "Product name")

    @field_validator("image_url")
    @classmethod
    def normalize_image_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip()
        if normalized.startswith("/") and not normalized.startswith("//"):
            return normalized
        validated = TypeAdapter(AnyHttpUrl).validate_python(normalized)
        return str(validated)

    @field_validator("image_reference")
    @classmethod
    def normalize_image_reference(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()

    @model_validator(mode="after")
    def validate_din_dimensions(self) -> "ProductWrite":
        if not self.din_rail_mount and self.module_width is not None:
            raise ValueError("TE-Breite ist nur bei DIN-Hutschienenprodukten zulässig")
        return self


class ProductRead(RecordRead):
    name: str
    manufacturer: str | None
    model_number: str | None
    description: str | None
    image_url: str | None = None
    image_source: ProductImageSource = ProductImageSource.URL
    image_reference: str | None = None
    din_rail_mount: bool = False
    module_width: int | None = None
    asset_type_id: UUID | None


class LocationWrite(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    location_type: LocationType | None = None
    description: str | None = None
    parent_id: UUID | None = None
    short_name: str | None = Field(default=None, max_length=80)
    sort_order: int | None = Field(default=None, ge=0, le=1_000_000)
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return _required_text(value, "Location name")

    @field_validator("short_name")
    @classmethod
    def normalize_short_name(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()


class LocationMoveWrite(BaseModel):
    parent_id: UUID


class LocationBreadcrumb(BaseModel):
    id: UUID
    name: str
    location_type: LocationType


class LocationRead(RecordRead):
    name: str
    location_type: LocationType
    description: str | None
    parent_id: UUID | None
    short_name: str | None
    sort_order: int | None
    notes: str | None
    path: str
    breadcrumbs: list[LocationBreadcrumb]
    direct_asset_count: int
    descendant_asset_count: int


class LocationTreeNode(LocationRead):
    children: list["LocationTreeNode"] = Field(default_factory=list)


class LabelWrite(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(default="#26c6da", pattern=r"^#[0-9a-fA-F]{6}$")

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return _required_text(value, "Label name")

    @field_validator("color")
    @classmethod
    def normalize_color(cls, value: str) -> str:
        return value.lower()


class LabelRead(RecordRead):
    name: str
    color: str


class AssetWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    asset_type_id: UUID
    product_id: UUID | None = None
    location_id: UUID | None = None
    serial_number: str | None = Field(default=None, max_length=200)
    inventory_number: str | None = Field(default=None, max_length=200)
    image_url: str | None = Field(default=None, max_length=1000)
    image_source: ProductImageSource = ProductImageSource.URL
    image_reference: str | None = Field(default=None, max_length=1000)
    module_width: int | None = Field(default=None, ge=1, le=100)
    breaker_characteristic: BreakerCharacteristic | None = None
    rated_current_a: float | None = Field(default=None, gt=0, le=10000)
    coil_voltage_v: float | None = Field(default=None, gt=0, le=10000)
    coil_voltage_type: CoilVoltageType | None = None
    contact_count: int | None = Field(default=None, ge=1, le=100)
    contact_type: ContactType | None = None
    status: AssetStatus = AssetStatus.ACTIVE
    label_ids: list[UUID] = Field(default_factory=list, max_length=100)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return _required_text(value, "Asset name")

    _normalize_asset_image_url = field_validator("image_url")(_normalize_image_url)
    _normalize_asset_image_reference = field_validator("image_reference")(_normalize_image_reference)

    @field_validator("serial_number", "inventory_number")
    @classmethod
    def normalize_optional_identifier(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()

    @field_validator("label_ids")
    @classmethod
    def labels_are_unique(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("Each label may only be assigned once")
        return value


class AssetRead(RecordRead):
    name: str
    jarvis_code: str
    description: str | None
    asset_type_id: UUID
    product_id: UUID | None
    location_id: UUID | None
    serial_number: str | None
    inventory_number: str | None
    image_url: str | None = None
    image_source: ProductImageSource = ProductImageSource.URL
    image_reference: str | None = None
    asset_type_image_url: str | None = None
    effective_image_url: str | None = None
    module_width: int | None
    effective_module_width: int | None
    breaker_characteristic: BreakerCharacteristic | None
    effective_breaker_characteristic: BreakerCharacteristic | None
    rated_current_a: float | None
    effective_rated_current_a: float | None
    coil_voltage_v: float | None
    effective_coil_voltage_v: float | None
    coil_voltage_type: CoilVoltageType | None
    effective_coil_voltage_type: CoilVoltageType | None
    contact_count: int | None
    effective_contact_count: int | None
    contact_type: ContactType | None
    effective_contact_type: ContactType | None
    status: AssetStatus
    asset_type: ReferenceRead
    asset_type_is_meter: bool = False
    product: ReferenceRead | None
    product_image_url: str | None = None
    location: ReferenceRead | None
    labels: list[LabelRead]


class AssetDuplicateWrite(BaseModel):
    name: str | None = Field(default=None, max_length=150)
    copy_location: bool = True
    copy_labels: bool = True
    copy_electrical_role: bool = True

    @field_validator("name")
    @classmethod
    def normalize_duplicate_name(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()


class AssetSeriesWrite(BaseModel):
    count: int = Field(ge=1, le=100)
    start_number: int = Field(default=1, ge=0, le=1_000_000)
    name_template: str = Field(default="{name} {n:02}", min_length=1, max_length=150)
    copy_location: bool = True
    copy_labels: bool = True
    copy_electrical_role: bool = True
    place_sequentially: bool = False
    distribution_id: UUID | None = None
    area_id: UUID | None = None
    row_number: int | None = Field(default=None, ge=1, le=100)
    start_position: int | None = Field(default=None, ge=1, le=1000)

    @field_validator("name_template")
    @classmethod
    def validate_name_template(cls, value: str) -> str:
        normalized = value.strip()
        try:
            sample = normalized.format(name="Asset", n=1)
        except (KeyError, ValueError, IndexError) as exc:
            raise ValueError("Namensschema darf nur {name} und {n} verwenden") from exc
        if not sample.strip() or len(sample) > 150:
            raise ValueError("Namensschema erzeugt keinen gültigen Asset-Namen")
        return normalized

    @model_validator(mode="after")
    def validate_placement(self) -> "AssetSeriesWrite":
        required = (self.distribution_id, self.row_number, self.start_position)
        if self.place_sequentially and any(value is None for value in required):
            raise ValueError(
                "Für fortlaufende Platzierung sind Verteilung, Reihe und "
                "Startposition nötig"
            )
        if not self.place_sequentially and any(
            value is not None
            for value in (
                self.distribution_id,
                self.area_id,
                self.row_number,
                self.start_position,
            )
        ):
            raise ValueError("Platzierungsfelder erfordern 'fortlaufend platzieren'")
        return self


class AssetSeriesRead(BaseModel):
    items: list[AssetRead]
    created_count: int = Field(ge=0)


class ProductImageUploadRead(BaseModel):
    image_url: str
    image_source: ProductImageSource = ProductImageSource.UPLOAD
    image_reference: str


class ProductImageSearchItemRead(BaseModel):
    title: str
    thumbnail_url: str
    source_url: str
    image_url: str
    license_name: str | None = None
    author: str | None = None
    provider: str | None = None


class ProductImageSearchRead(BaseModel):
    items: list[ProductImageSearchItemRead]
    enabled: bool


class ProductImageImportWrite(BaseModel):
    image_url: str = Field(min_length=1, max_length=2000)
    source_url: str | None = Field(default=None, max_length=2000)


class RelationshipWrite(BaseModel):
    source_asset_id: UUID
    target_asset_id: UUID
    relationship_type: str = Field(min_length=1, max_length=100)
    description: str | None = None

    @field_validator("relationship_type")
    @classmethod
    def normalize_type(cls, value: str) -> str:
        return _required_text(value, "Relationship type")

    @model_validator(mode="after")
    def endpoints_are_distinct(self) -> "RelationshipWrite":
        if self.source_asset_id == self.target_asset_id:
            raise ValueError("A relationship requires two different assets")
        return self


class RelationshipRead(RecordRead):
    source_asset_id: UUID
    target_asset_id: UUID
    relationship_type: str
    description: str | None


class AssetReplacementWrite(BaseModel):
    replacement: AssetWrite
    reason: str | None = Field(default=None, max_length=1000)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()


class AssetReplacementRead(BaseModel):
    archived: AssetRead
    replacement: AssetRead
    relationship: RelationshipRead


class Page[ItemT](BaseModel):
    items: list[ItemT]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(
        cls,
        items: list[ItemT],
        total: int,
        page: int,
        page_size: int,
    ) -> "Page[ItemT]":
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=ceil(total / page_size) if total else 0,
        )


def _required_text(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty")
    return normalized
