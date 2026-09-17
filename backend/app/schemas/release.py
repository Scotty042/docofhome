import re
from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    field_validator,
    model_validator,
)


class DashboardCardSetting(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=50)
    visible: bool = True


class DashboardSettingWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cards: list[DashboardCardSetting] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def unique_cards(self) -> "DashboardSettingWrite":
        identifiers = [item.id for item in self.cards]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Dashboard-Kacheln dürfen nicht doppelt vorkommen")
        return self


class DashboardSettingRead(DashboardSettingWrite):
    updated_at: datetime


class PortNameScheme(StrEnum):
    NUMERIC = "numeric"
    GIGABIT = "gigabit"
    ETHERNET = "ethernet"


class PortGroupWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group: str = Field(pattern="^(copper|sfp|sfp_plus|uplink)$")
    count: int = Field(ge=0, le=256)
    scheme: PortNameScheme = PortNameScheme.NUMERIC
    start: int = Field(default=1, ge=1, le=4096)
    speed_mbps: int | None = Field(default=None, ge=1, le=1_000_000)
    poe_capable: bool = False


class PortGenerationWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    groups: list[PortGroupWrite] = Field(min_length=1, max_length=4)


class PortGenerationPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_id: UUID
    existing_names: list[str]
    create_names: list[str]
    unchanged_names: list[str]
    requested_total: int


class PortGenerationResult(PortGenerationPreview):
    created: int


class NetworkPathNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_id: UUID
    asset_id: UUID
    name: str
    role: str


class NetworkPathRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_device_id: UUID
    nodes: list[NetworkPathNode]
    connection_ids: list[UUID]
    warnings: list[str]
    documented_path: bool = True


class WorkloadPort(BaseModel):
    model_config = ConfigDict(extra="forbid")

    container_port: int = Field(ge=1, le=65535)
    host_port: int | None = Field(default=None, ge=1, le=65535)
    protocol: str = Field(default="tcp", pattern="^(tcp|udp)$")


class WorkloadUrls(BaseModel):
    model_config = ConfigDict(extra="forbid")

    internal: AnyHttpUrl | None = None
    external: AnyHttpUrl | None = None
    administrative: AnyHttpUrl | None = None
    api: AnyHttpUrl | None = None


class ServiceWorkloadWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host_asset_id: UUID
    name: str = Field(min_length=1, max_length=200)
    image: str | None = Field(default=None, max_length=500)
    image_tag: str | None = Field(default=None, max_length=200)
    compose_project: str | None = Field(default=None, max_length=200)
    network_mode: str = Field(
        default="bridge",
        pattern="^(bridge|host|macvlan|docker_network)$",
    )
    macvlan_address: str | None = Field(default=None, max_length=64)
    ports: list[WorkloadPort] = Field(default_factory=list, max_length=100)
    urls: WorkloadUrls = Field(default_factory=WorkloadUrls)
    reverse_proxy: str | None = Field(default=None, max_length=500)
    dependency_ids: list[UUID] = Field(default_factory=list, max_length=100)
    status: str = Field(default="unknown", pattern="^(running|stopped|planned|unknown)$")
    notes: str | None = Field(default=None, max_length=20_000)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_network_mode(self) -> "ServiceWorkloadWrite":
        if self.network_mode != "macvlan" and self.macvlan_address is not None:
            raise ValueError("Eine eigene IP ist nur im Macvlan-Modus zulässig")
        if len(self.dependency_ids) != len(set(self.dependency_ids)):
            raise ValueError("Dienstabhängigkeiten dürfen nicht doppelt vorkommen")
        return self


class ServiceWorkloadRead(ServiceWorkloadWrite):
    id: UUID
    host_name: str
    docker_container_id: str | None = None
    docker_status_text: str | None = None
    docker_networks: list[str] = Field(default_factory=list)
    docker_mounts: list[str] = Field(default_factory=list)
    docker_last_seen_at: datetime | None = None
    docker_managed: bool = False
    created_at: datetime
    updated_at: datetime


class DockerSyncSettingWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    socket_path: str = Field(default="/var/run/docker.sock", min_length=1, max_length=500)
    host_asset_id: UUID | None = None
    refresh_interval_seconds: int = Field(default=300)

    @field_validator("socket_path")
    @classmethod
    def normalize_socket_path(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized.startswith("/"):
            raise ValueError("Der Docker-Socket muss als absoluter Pfad angegeben werden")
        return normalized

    @field_validator("refresh_interval_seconds")
    @classmethod
    def validate_interval(cls, value: int) -> int:
        if value not in {0, 30, 60, 300, 900, 1800}:
            raise ValueError("Ungültiges Docker-Aktualisierungsintervall")
        return value


class DockerSyncSettingRead(DockerSyncSettingWrite):
    host_name: str | None = None
    last_attempt_at: datetime | None = None
    last_success_at: datetime | None = None
    last_error: str | None = None


class DockerSyncResultRead(BaseModel):
    imported: int = Field(ge=0)
    updated: int = Field(ge=0)
    missing: int = Field(ge=0)
    total: int = Field(ge=0)
    docker_version: str | None = None
    synchronized_at: datetime


class DockerConnectionTestRead(BaseModel):
    success: bool
    message: str
    docker_version: str | None = None


class DockerHostWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    enabled: bool = False
    connection_type: Literal["socket", "ssh"] = "ssh"
    host_asset_id: UUID
    socket_path: str | None = Field(default=None, max_length=500)
    ssh_host: str | None = Field(default=None, max_length=255)
    ssh_port: int = Field(default=22, ge=1, le=65535)
    ssh_user: str | None = Field(default=None, max_length=100)
    ssh_host_key: str | None = None
    refresh_interval_seconds: int = Field(default=300)

    @model_validator(mode="after")
    def validate_connection(self) -> "DockerHostWrite":
        self.name = self.name.strip()
        if self.connection_type == "socket":
            if not self.socket_path or not self.socket_path.strip().startswith("/"):
                raise ValueError(
                    "Für einen lokalen Host ist ein absoluter Docker-Socket erforderlich"
                )
            self.socket_path = self.socket_path.strip()
            self.ssh_host = self.ssh_user = self.ssh_host_key = None
        else:
            self.socket_path = None
            self.ssh_host = self.ssh_host.strip() if self.ssh_host else None
            self.ssh_user = self.ssh_user.strip() if self.ssh_user else None
            self.ssh_host_key = self.ssh_host_key.strip() if self.ssh_host_key else None
            if not self.ssh_host or not self.ssh_user:
                raise ValueError("Für SSH sind Hostname und Benutzer erforderlich")
            if self.ssh_host.startswith("-") or not re.fullmatch(
                r"[A-Za-z0-9_.:-]+", self.ssh_host
            ):
                raise ValueError("Der SSH-Hostname enthält unzulässige Zeichen")
            if not re.fullmatch(r"[A-Za-z0-9._-]+", self.ssh_user):
                raise ValueError("Der SSH-Benutzer enthält unzulässige Zeichen")
            if self.ssh_host_key:
                parts = self.ssh_host_key.split()
                if len(parts) < 3 or parts[1] not in {
                    "ssh-ed25519",
                    "ecdsa-sha2-nistp256",
                    "rsa-sha2-512",
                    "ssh-rsa",
                }:
                    raise ValueError("Der SSH-Host-Schlüssel ist ungültig")
        if self.refresh_interval_seconds not in {0, 30, 60, 300, 900, 1800}:
            raise ValueError("Ungültiges Docker-Aktualisierungsintervall")
        return self


class DockerHostRead(DockerHostWrite):
    id: UUID
    host_name: str
    public_key: str | None = None
    key_configured: bool = False
    host_key_fingerprint: str | None = None
    last_attempt_at: datetime | None = None
    last_success_at: datetime | None = None
    last_error: str | None = None


class DockerHostKeyScanRead(BaseModel):
    host_key: str
    fingerprint: str


class ExportManifestRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app_version: str
    export_version: str
    created_at: datetime
    modules: list[str]
    excluded_security_fields: list[str]


class ImportPreviewRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: str
    export_version: str | None
    record_counts: dict[str, int]
    conflicts: list[str]
    warnings: list[str]
    writable: bool = False


class ImportResultRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    created: int
    skipped: int
    conflicts: int
    modules: list[str]
    rolled_back: bool = False


class AuditEventRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    object_type: str
    object_id: str
    object_label: str | None = None
    object_route: str | None = None
    action: str
    change: dict[str, JsonValue]
    display_change: dict[str, JsonValue] | None = None
    created_at: datetime


class GuidedSetupDraftWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    current_step: int = Field(default=1, ge=1, le=11)
    data: dict[str, JsonValue] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def normalize_draft_name(cls, value: str) -> str:
        return value.strip()


class GuidedSetupDraftRead(GuidedSetupDraftWrite):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime


class GuidedSetupPreviewRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_id: UUID
    actions: list[str]
    warnings: list[str]
    errors: list[str]
    duplicate_asset_ids: list[UUID]
    can_apply: bool


class GuidedSetupApplyRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_id: UUID
    asset_id: UUID
    created_object_ids: list[UUID]
    applied_at: datetime


class FritzBoxDeviceRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    mac_address: str | None
    ipv4: str | None
    ipv6: str | None
    active: bool
    interface_type: str | None
    connection_rate_mbps: int | None
    connected_via: str | None
    last_seen: datetime | None
    dhcp_reservation: bool | None
