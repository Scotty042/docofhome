import re
from datetime import datetime
from enum import StrEnum
from ipaddress import ip_address, ip_network
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


class NetworkRole(StrEnum):
    ROUTER = "router"
    FIREWALL = "firewall"
    SWITCH = "switch"
    ACCESS_POINT = "access_point"
    SERVER = "server"
    NAS = "nas"
    CLIENT = "client"
    IOT = "iot"
    PRINTER = "printer"
    CONTROLLER = "controller"
    OTHER = "other"


class NetworkInterfaceType(StrEnum):
    ETHERNET = "ethernet"
    WIFI = "wifi"
    FIBER = "fiber"
    VIRTUAL = "virtual"
    CELLULAR = "cellular"
    OTHER = "other"


class NetworkPoeMode(StrEnum):
    NONE = "none"
    SOURCE = "source"
    SINK = "sink"
    PASSIVE = "passive"
    UNKNOWN = "unknown"


class NetworkAssignmentType(StrEnum):
    STATIC = "static"
    DHCP = "dhcp"
    RESERVATION = "reservation"
    LINK_LOCAL = "link_local"
    UNKNOWN = "unknown"


class NetworkConnectionType(StrEnum):
    PHYSICAL = "physical"
    LOGICAL = "logical"
    WIRELESS = "wireless"


class NetworkConnectionStatus(StrEnum):
    ACTIVE = "active"
    PLANNED = "planned"
    INACTIVE = "inactive"


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _hostname(value: str | None) -> str | None:
    normalized = _optional_text(value)
    if normalized is None:
        return None
    if "_" in normalized:
        raise ValueError(
            "Unterstriche sind in Hostnamen nicht erlaubt. "
            "Verwenden Sie stattdessen einen Bindestrich."
        )
    if len(normalized) > 253 or not re.fullmatch(
        r"(?=.{1,253}\.?$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
        r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.??",
        normalized,
    ):
        raise ValueError(
            "Der Hostname darf nur Buchstaben, Ziffern, Punkte und Bindestriche "
            "enthalten; jedes Segment muss mit Buchstabe oder Ziffer beginnen und enden."
        )
    return normalized.rstrip(".").lower()


def _mac(value: str | None) -> str | None:
    normalized = _optional_text(value)
    if normalized is None:
        return None
    compact = re.sub(r"[^0-9A-Fa-f]", "", normalized)
    if len(compact) != 12:
        raise ValueError("Invalid MAC address")
    return ":".join(compact[index : index + 2] for index in range(0, 12, 2)).upper()


class NetworkDeviceWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: UUID
    role: NetworkRole = NetworkRole.OTHER
    hostname: str | None = Field(default=None, max_length=253)
    management_url: str | None = Field(default=None, max_length=1000)
    notes: str | None = None

    _normalize_hostname = field_validator("hostname")(_hostname)
    _normalize_notes = field_validator("notes")(_optional_text)

    @field_validator("management_url")
    @classmethod
    def validate_management_url(cls, value: str | None) -> str | None:
        normalized = _optional_text(value)
        if normalized is None:
            return None
        parsed = TypeAdapter(AnyHttpUrl).validate_python(normalized)
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("Management URL must not contain credentials")
        return str(parsed)


class NetworkDeviceRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    asset_id: UUID
    asset_name: str
    asset_code: str
    asset_type: str
    switch_port_layout: str = "odd_even"
    product_name: str | None
    location_name: str | None
    role: NetworkRole
    hostname: str | None
    management_url: str | None
    notes: str | None
    primary_address: str | None
    interface_count: int = Field(ge=0)
    address_count: int = Field(ge=0)
    connection_count: int = Field(ge=0)
    archived: bool
    created_at: datetime
    updated_at: datetime


class NetworkDeviceCandidateRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: UUID
    name: str
    jarvis_code: str
    asset_type: str
    product_name: str | None
    location_name: str | None


class NetworkSegmentWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=150)
    cidr: str = Field(min_length=3, max_length=64)
    vlan_id: int | None = Field(default=None, ge=1, le=4094)
    gateway: str | None = Field(default=None, max_length=64)
    dns_servers: list[str] = Field(default_factory=list, max_length=10)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name must not be empty")
        return normalized

    @field_validator("cidr")
    @classmethod
    def normalize_cidr(cls, value: str) -> str:
        return str(ip_network(value.strip(), strict=False))

    @field_validator("gateway")
    @classmethod
    def normalize_gateway(cls, value: str | None) -> str | None:
        normalized = _optional_text(value)
        return str(ip_address(normalized)) if normalized else None

    @field_validator("dns_servers")
    @classmethod
    def normalize_dns(cls, values: list[str]) -> list[str]:
        result: list[str] = []
        for value in values:
            parsed = str(ip_address(value.strip()))
            if parsed not in result:
                result.append(parsed)
        return result

    _normalize_description = field_validator("description")(_optional_text)

    @model_validator(mode="after")
    def gateway_belongs_to_network(self) -> "NetworkSegmentWrite":
        if self.gateway is not None and ip_address(self.gateway) not in ip_network(self.cidr):
            raise ValueError("Gateway must belong to the configured network")
        return self


class NetworkSegmentRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    cidr: str
    vlan_id: int | None
    gateway: str | None
    dns_servers: list[str]
    description: str | None
    address_count: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime


class NetworkInterfaceWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    network_device_id: UUID
    name: str = Field(min_length=1, max_length=100)
    interface_type: NetworkInterfaceType = NetworkInterfaceType.ETHERNET
    mac_address: str | None = Field(default=None, max_length=32)
    speed_mbps: int | None = Field(default=None)

    @field_validator("speed_mbps")
    @classmethod
    def validate_speed(cls, value: int | None) -> int | None:
        if value is not None and value not in {100, 1000, 2500}:
            raise ValueError("Geschwindigkeit muss 100, 1000 oder 2500 Mbit/s sein")
        return value

    poe_mode: NetworkPoeMode = NetworkPoeMode.NONE
    enabled: bool = True
    is_primary: bool = False
    logical_interface_id: UUID | None = None
    description: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Interface name must not be empty")
        return normalized

    _normalize_mac = field_validator("mac_address")(_mac)
    _normalize_description = field_validator("description")(_optional_text)


class NetworkInterfaceRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    network_device_id: UUID
    device_name: str
    name: str
    interface_type: NetworkInterfaceType
    mac_address: str | None
    speed_mbps: int | None
    poe_mode: NetworkPoeMode
    enabled: bool
    is_primary: bool
    logical_interface_id: UUID | None
    logical_interface_name: str | None
    member_count: int = Field(ge=0)
    description: str | None
    address_count: int = Field(ge=0)
    connection_count: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime


class NetworkAddressWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interface_id: UUID
    segment_id: UUID | None = None
    address: str = Field(min_length=2, max_length=64)
    assignment_type: NetworkAssignmentType = NetworkAssignmentType.UNKNOWN
    hostname: str | None = Field(default=None, max_length=253)
    is_primary: bool = False
    notes: str | None = None

    @field_validator("address")
    @classmethod
    def normalize_address(cls, value: str) -> str:
        return str(ip_address(value.strip()))

    _normalize_hostname = field_validator("hostname")(_hostname)
    _normalize_notes = field_validator("notes")(_optional_text)


class NetworkAddressRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    interface_id: UUID
    interface_name: str
    network_device_id: UUID
    device_name: str
    segment_id: UUID | None
    segment_name: str | None
    address: str
    assignment_type: NetworkAssignmentType
    hostname: str | None
    is_primary: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class NetworkConnectionWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_interface_id: UUID
    target_interface_id: UUID
    connection_type: NetworkConnectionType = NetworkConnectionType.PHYSICAL
    status: NetworkConnectionStatus = NetworkConnectionStatus.ACTIVE
    cable_type: str | None = Field(default=None, max_length=100)
    cable_label: str | None = Field(default=None, max_length=100)
    description: str | None = None

    _normalize_cable_type = field_validator("cable_type")(_optional_text)
    _normalize_cable_label = field_validator("cable_label")(_optional_text)
    _normalize_description = field_validator("description")(_optional_text)

    @model_validator(mode="after")
    def distinct_interfaces(self) -> "NetworkConnectionWrite":
        if self.source_interface_id == self.target_interface_id:
            raise ValueError("A connection requires two different interfaces")
        return self


class NetworkConnectionRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    source_interface_id: UUID
    source_interface_name: str
    source_device_id: UUID
    source_device_name: str
    target_interface_id: UUID
    target_interface_name: str
    target_device_id: UUID
    target_device_name: str
    connection_type: NetworkConnectionType
    status: NetworkConnectionStatus
    cable_type: str | None
    cable_label: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime


class NetworkSummaryRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_count: int = Field(ge=0)
    segment_count: int = Field(ge=0)
    interface_count: int = Field(ge=0)
    address_count: int = Field(ge=0)
    connection_count: int = Field(ge=0)
    free_interface_count: int = Field(ge=0)
    device_without_connection_count: int = Field(ge=0)
    unconnected_interface_count: int = Field(ge=0)


class NetworkTopologyNodeRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    asset_id: UUID
    name: str
    role: NetworkRole
    hostname: str | None
    location_name: str | None
    interface_count: int


class NetworkTopologyEdgeRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    source_device_id: UUID
    target_device_id: UUID
    source_label: str
    target_label: str
    connection_type: NetworkConnectionType
    status: NetworkConnectionStatus
    cable_label: str | None


class NetworkTopologyRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[NetworkTopologyNodeRead]
    edges: list[NetworkTopologyEdgeRead]


class NetworkIpStatus(StrEnum):
    MATCH = "match"
    MISMATCH = "mismatch"
    NOT_DETECTED = "not_detected"
    OBSERVED_ONLY = "observed_only"
    CONFLICT = "conflict"
    NO_INTEGRATION = "no_integration"


class NetworkIpOverviewRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    status: NetworkIpStatus
    device_id: UUID | None
    device_name: str
    interface_id: UUID | None
    interface_name: str | None
    documented_address_id: UUID | None
    documented_address: str | None
    mac_address: str | None
    assignment_type: NetworkAssignmentType
    observed_address_id: UUID | None
    observed_address: str | None
    source: str | None
    last_seen_at: datetime | None
    ignored: bool = False


class NetworkIpActionRead(BaseModel):
    documented_address_id: UUID | None
    status: str
