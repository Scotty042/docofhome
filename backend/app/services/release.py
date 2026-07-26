from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime
from typing import Any, TypeVar, cast
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, col, select, text

from app.core.settings import settings
from app.models.application_setting import ApplicationSetting
from app.models.asset_engine import (
    Asset,
    AssetCodeCounter,
    AssetLabelLink,
    AssetType,
    Label,
    Location,
    Product,
    Relationship,
)
from app.models.consumption import (
    ConsumptionMeter,
    ConsumptionNote,
    ConsumptionReading,
    ConsumptionSetting,
)
from app.models.document_link import DocumentLink
from app.models.electrical import (
    ElectricalComponent,
    ElectricalDistribution,
    ElectricalDistributionArea,
    ElectricalDistributionSection,
    ElectricalProtectiveDevice,
)
from app.models.electrical_circuit import ElectricalCircuit, ElectricalCircuitAssetLink
from app.models.electrical_topology import ElectricalConnection
from app.models.home_assistant import (
    HomeAssistantAssetLink,
    HomeAssistantEntitySelection,
    HomeAssistantSelectionSetting,
)
from app.models.immich import ImmichAssetLink
from app.models.knowledge import DomainNote, WikiPage
from app.models.network import (
    NetworkAddress,
    NetworkConnection,
    NetworkDevice,
    NetworkInterface,
    NetworkSegment,
)
from app.models.quality import QualityIssue, QualityRun
from app.models.release import (
    DEFAULT_DASHBOARD_LAYOUT,
    AuditEvent,
    DashboardSetting,
    GuidedSetupDraft,
    ServiceWorkload,
)
from app.models.system_setting import SystemSetting
from app.models.work import WorkItem, WorkItemEvent
from app.repositories.asset_engine import AssetRepository
from app.repositories.network import NetworkRepository
from app.schemas.asset_engine import AssetWrite
from app.schemas.consumption import ConsumptionMeterWrite
from app.schemas.release import (
    AuditEventRead,
    DashboardCardSetting,
    DashboardSettingRead,
    DashboardSettingWrite,
    GuidedSetupApplyRead,
    GuidedSetupDraftRead,
    GuidedSetupDraftWrite,
    GuidedSetupPreviewRead,
    ImportPreviewRead,
    ImportResultRead,
    NetworkPathNode,
    NetworkPathRead,
    PortGenerationPreview,
    PortGenerationResult,
    PortGenerationWrite,
    PortGroupWrite,
    PortNameScheme,
    ServiceWorkloadRead,
    ServiceWorkloadWrite,
)
from app.services.asset_engine import AssetService
from app.services.consumption import ConsumptionService

ModelT = TypeVar("ModelT", bound=SQLModel)


class ReleaseFeatureError(RuntimeError):
    pass


class ReleaseNotFoundError(ReleaseFeatureError):
    pass


class ReleaseConflictError(ReleaseFeatureError):
    pass


class ReleaseValidationError(ReleaseFeatureError):
    pass


ALLOWED_DASHBOARD_CARDS = {
    "documentation",
    "consumption_comparison",
    "maintenance",
    "quality",
    "network",
}


class DashboardService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self) -> DashboardSettingRead:
        record = self.session.get(DashboardSetting, 1)
        if record is None:
            record = DashboardSetting()
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
        parsed = [
            DashboardCardSetting.model_validate(item) for item in json.loads(record.layout_json)
        ]
        cards: list[DashboardCardSetting] = []
        seen: set[str] = set()
        for item in parsed:
            if item.id in ALLOWED_DASHBOARD_CARDS and item.id not in seen:
                cards.append(item)
                seen.add(item.id)
        for identifier in (
            "documentation",
            "consumption_comparison",
            "maintenance",
            "quality",
            "network",
        ):
            if identifier not in seen:
                cards.append(DashboardCardSetting(id=identifier, visible=True))
        if [item.model_dump() for item in parsed] != [item.model_dump() for item in cards]:
            record.layout_json = json.dumps(
                [item.model_dump(mode="json") for item in cards],
                ensure_ascii=False,
                separators=(",", ":"),
            )
            record.updated_at = datetime.now(UTC)
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
        return DashboardSettingRead(cards=cards, updated_at=self._aware(record.updated_at))

    def update(self, payload: DashboardSettingWrite) -> DashboardSettingRead:
        identifiers = {item.id for item in payload.cards}
        unknown = identifiers - ALLOWED_DASHBOARD_CARDS
        missing = ALLOWED_DASHBOARD_CARDS - identifiers
        if unknown or missing:
            raise ReleaseValidationError(
                "Dashboard-Konfiguration enthält unbekannte oder fehlende Kacheln"
            )
        record = self.session.get(DashboardSetting, 1) or DashboardSetting()
        record.layout_json = json.dumps(
            [item.model_dump(mode="json") for item in payload.cards],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self.get()

    def reset(self) -> DashboardSettingRead:
        cards = [
            DashboardCardSetting.model_validate(item)
            for item in json.loads(DEFAULT_DASHBOARD_LAYOUT)
        ]
        return self.update(DashboardSettingWrite(cards=cards))

    @staticmethod
    def _aware(value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=UTC)


class NetworkExtensionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = NetworkRepository(session)

    def preview_ports(
        self,
        device_id: UUID,
        payload: PortGenerationWrite,
    ) -> PortGenerationPreview:
        device = self._switch(device_id)
        del device
        existing = self.repository.list_interfaces(device_id=device_id)
        existing_by_name = {item.name.casefold(): item.name for item in existing}
        requested: list[str] = []
        for group in payload.groups:
            requested.extend(self._port_names(group))
        if len(requested) != len({item.casefold() for item in requested}):
            raise ReleaseValidationError("Das gewählte Portschema erzeugt doppelte Namen")
        create_names = [item for item in requested if item.casefold() not in existing_by_name]
        unchanged = [
            existing_by_name[item.casefold()]
            for item in requested
            if item.casefold() in existing_by_name
        ]
        return PortGenerationPreview(
            device_id=device_id,
            existing_names=[item.name for item in existing],
            create_names=create_names,
            unchanged_names=unchanged,
            requested_total=len(requested),
        )

    def generate_ports(
        self,
        device_id: UUID,
        payload: PortGenerationWrite,
    ) -> PortGenerationResult:
        preview = self.preview_ports(device_id, payload)
        existing = {item.casefold() for item in preview.existing_names}
        records: list[NetworkInterface] = []
        for group in payload.groups:
            interface_type = "fiber" if group.group in {"sfp", "sfp_plus"} else "ethernet"
            poe_mode = "source" if group.poe_capable else "none"
            for name in self._port_names(group):
                if name.casefold() in existing:
                    continue
                records.append(
                    NetworkInterface(
                        network_device_id=device_id,
                        name=name,
                        interface_type=interface_type,
                        speed_mbps=group.speed_mbps,
                        poe_mode=poe_mode,
                        autogenerated=True,
                        port_group=group.group,
                    )
                )
                existing.add(name.casefold())
        try:
            for record in records:
                self.session.add(record)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ReleaseConflictError(
                "Die Ports wurden parallel verändert; Vorschau bitte neu laden"
            ) from exc
        return PortGenerationResult(**preview.model_dump(), created=len(records))

    def documented_path(self, device_id: UUID) -> NetworkPathRead:
        target = self.repository.get_device(device_id)
        if target is None:
            raise ReleaseNotFoundError("Das Netzwerkgerät wurde nicht gefunden")
        devices = self.repository.list_devices()
        interfaces = self.repository.list_interfaces()
        connections = [
            item for item in self.repository.list_connections() if item.status == "active"
        ]
        device_by_id = {item.id: item for item in devices}
        interface_device = {item.id: item.network_device_id for item in interfaces}
        adjacency: dict[UUID, list[tuple[UUID, UUID]]] = {item.id: [] for item in devices}
        for connection in connections:
            source = interface_device.get(connection.source_interface_id)
            destination = interface_device.get(connection.target_interface_id)
            if source is None or destination is None or source == destination:
                continue
            adjacency.setdefault(source, []).append((destination, connection.id))
            adjacency.setdefault(destination, []).append((source, connection.id))
        roots = {
            item.id
            for item in devices
            if item.role in {"router", "firewall"} and item.deleted_at is None
        }
        queue: list[UUID] = [device_id]
        parent: dict[UUID, tuple[UUID, UUID] | None] = {device_id: None}
        selected_root: UUID | None = device_id if device_id in roots else None
        loop_detected = False
        while queue and selected_root is None:
            current = queue.pop(0)
            neighbors = sorted(
                adjacency.get(current, []),
                key=lambda item: self._device_name(device_by_id.get(item[0])).casefold(),
            )
            for neighbor, connection_id in neighbors:
                if neighbor in parent:
                    if parent[current] is None or parent[current][0] != neighbor:
                        loop_detected = True
                    continue
                parent[neighbor] = (current, connection_id)
                if neighbor in roots:
                    selected_root = neighbor
                    break
                queue.append(neighbor)
        warnings: list[str] = []
        if selected_root is None:
            selected_root = device_id
            warnings.append("Kein dokumentierter Pfad zu Router oder Firewall vorhanden")
        if loop_detected:
            warnings.append("Die dokumentierte Topologie enthält mindestens eine Schleife")
        reverse_nodes: list[UUID] = [selected_root]
        reverse_connections: list[UUID] = []
        while reverse_nodes[-1] != device_id:
            step = parent.get(reverse_nodes[-1])
            if step is None:
                break
            previous, connection_id = step
            reverse_connections.append(connection_id)
            reverse_nodes.append(previous)
        reverse_nodes.reverse()
        reverse_connections.reverse()
        return NetworkPathRead(
            target_device_id=device_id,
            nodes=[
                NetworkPathNode(
                    device_id=identifier,
                    asset_id=device_by_id[identifier].asset_id,
                    name=self._device_name(device_by_id[identifier]),
                    role=device_by_id[identifier].role,
                )
                for identifier in reverse_nodes
                if identifier in device_by_id
            ],
            connection_ids=reverse_connections,
            warnings=warnings,
        )

    def _switch(self, device_id: UUID) -> NetworkDevice:
        device = self.repository.get_device(device_id)
        if device is None:
            raise ReleaseNotFoundError("Das Netzwerkgerät wurde nicht gefunden")
        if device.role != "switch":
            raise ReleaseValidationError("Ports können nur für Switches automatisch erzeugt werden")
        return device

    @staticmethod
    def _port_names(group: PortGroupWrite) -> list[str]:
        result: list[str] = []
        for value in range(group.start, group.start + group.count):
            if group.scheme == PortNameScheme.NUMERIC:
                result.append(str(value))
            elif group.scheme == PortNameScheme.GIGABIT:
                result.append(f"Gi1/0/{value}")
            else:
                result.append(f"eth{value}")
        return result

    def _device_name(self, device: NetworkDevice | None) -> str:
        if device is None:
            return "Unbekannt"
        asset = self.session.get(Asset, device.asset_id)
        return device.hostname or (asset.name if asset else str(device.id))


class WorkloadService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self, *, host_asset_id: UUID | None = None) -> list[ServiceWorkloadRead]:
        statement = select(ServiceWorkload).where(col(ServiceWorkload.deleted_at).is_(None))
        if host_asset_id is not None:
            statement = statement.where(ServiceWorkload.host_asset_id == host_asset_id)
        records = self.session.exec(
            statement.order_by(ServiceWorkload.host_asset_id, ServiceWorkload.name)
        ).all()
        return [self._read(record) for record in records]

    def create(self, payload: ServiceWorkloadWrite) -> ServiceWorkloadRead:
        self._validate(payload)
        record = ServiceWorkload(**self._values(payload))
        return self._save(record)

    def update(self, workload_id: UUID, payload: ServiceWorkloadWrite) -> ServiceWorkloadRead:
        record = self._require(workload_id)
        self._validate(payload, exclude_id=workload_id)
        for key, value in self._values(payload).items():
            setattr(record, key, value)
        record.updated_at = datetime.now(UTC)
        return self._save(record)

    def archive(self, workload_id: UUID) -> None:
        record = self._require(workload_id)
        record.deleted_at = datetime.now(UTC)
        record.updated_at = record.deleted_at
        self.session.add(record)
        self.session.commit()

    def _validate(
        self,
        payload: ServiceWorkloadWrite,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        host = self.session.get(Asset, payload.host_asset_id)
        if host is None or host.deleted_at is not None:
            raise ReleaseValidationError("Das Host-Asset wurde nicht gefunden oder ist archiviert")
        records = self.session.exec(
            select(ServiceWorkload).where(
                ServiceWorkload.host_asset_id == payload.host_asset_id,
                col(ServiceWorkload.deleted_at).is_(None),
            )
        ).all()
        if any(
            item.name.casefold() == payload.name.casefold() and item.id != exclude_id
            for item in records
        ):
            raise ReleaseConflictError(
                "Auf diesem Host existiert bereits ein Dienst mit diesem Namen"
            )
        for dependency_id in payload.dependency_ids:
            dependency = self.session.get(ServiceWorkload, dependency_id)
            if dependency is None or dependency.deleted_at is not None:
                raise ReleaseValidationError("Eine Dienstabhängigkeit wurde nicht gefunden")
            if dependency.id == exclude_id:
                raise ReleaseValidationError("Ein Dienst kann nicht von sich selbst abhängen")

    @staticmethod
    def _values(payload: ServiceWorkloadWrite) -> dict[str, object]:
        return {
            "host_asset_id": payload.host_asset_id,
            "name": payload.name,
            "image": payload.image,
            "image_tag": payload.image_tag,
            "compose_project": payload.compose_project,
            "network_mode": payload.network_mode,
            "macvlan_address": payload.macvlan_address,
            "ports_json": json.dumps(
                [item.model_dump(mode="json") for item in payload.ports],
                separators=(",", ":"),
            ),
            "urls_json": json.dumps(payload.urls.model_dump(mode="json"), separators=(",", ":")),
            "reverse_proxy": payload.reverse_proxy,
            "dependencies_json": json.dumps(
                [str(item) for item in payload.dependency_ids],
                separators=(",", ":"),
            ),
            "status": payload.status,
            "notes": payload.notes,
        }

    def _save(self, record: ServiceWorkload) -> ServiceWorkloadRead:
        try:
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
        except IntegrityError as exc:
            self.session.rollback()
            raise ReleaseConflictError("Der Dienst verletzt eine Eindeutigkeitsregel") from exc
        return self._read(record)

    def _require(self, workload_id: UUID) -> ServiceWorkload:
        record = self.session.get(ServiceWorkload, workload_id)
        if record is None or record.deleted_at is not None:
            raise ReleaseNotFoundError("Der Dienst wurde nicht gefunden")
        return record

    def _read(self, record: ServiceWorkload) -> ServiceWorkloadRead:
        host = self.session.get(Asset, record.host_asset_id)
        return ServiceWorkloadRead.model_validate(
            {
                "id": record.id,
                "host_asset_id": record.host_asset_id,
                "host_name": host.name if host else "Unbekannter Host",
                "name": record.name,
                "image": record.image,
                "image_tag": record.image_tag,
                "compose_project": record.compose_project,
                "network_mode": record.network_mode,
                "macvlan_address": record.macvlan_address,
                "ports": json.loads(record.ports_json),
                "urls": json.loads(record.urls_json),
                "reverse_proxy": record.reverse_proxy,
                "dependency_ids": json.loads(record.dependencies_json),
                "status": record.status,
                "notes": record.notes,
                "created_at": self._aware(record.created_at),
                "updated_at": self._aware(record.updated_at),
            }
        )

    @staticmethod
    def _aware(value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=UTC)


EXPORT_MODELS: tuple[tuple[str, type[SQLModel], bool], ...] = (
    ("application_settings", ApplicationSetting, True),
    ("system_settings", SystemSetting, True),
    ("asset_types", AssetType, True),
    ("products", Product, True),
    ("locations", Location, True),
    ("labels", Label, True),
    ("asset_code_counters", AssetCodeCounter, True),
    ("assets", Asset, True),
    ("asset_label_links", AssetLabelLink, True),
    ("relationships", Relationship, True),
    ("electrical_components", ElectricalComponent, True),
    ("electrical_distributions", ElectricalDistribution, True),
    ("electrical_distribution_sections", ElectricalDistributionSection, True),
    ("electrical_distribution_areas", ElectricalDistributionArea, True),
    ("electrical_protective_devices", ElectricalProtectiveDevice, True),
    ("electrical_circuits", ElectricalCircuit, True),
    ("electrical_circuit_asset_links", ElectricalCircuitAssetLink, True),
    ("electrical_connections", ElectricalConnection, True),
    ("home_assistant_asset_links", HomeAssistantAssetLink, True),
    ("home_assistant_selection_settings", HomeAssistantSelectionSetting, True),
    ("home_assistant_entity_selections", HomeAssistantEntitySelection, True),
    ("immich_asset_links", ImmichAssetLink, True),
    ("document_links", DocumentLink, True),
    ("wiki_pages", WikiPage, True),
    ("domain_notes", DomainNote, True),
    ("work_items", WorkItem, True),
    ("work_item_events", WorkItemEvent, True),
    ("quality_runs", QualityRun, True),
    ("quality_issues", QualityIssue, True),
    ("network_devices", NetworkDevice, True),
    ("network_segments", NetworkSegment, True),
    ("network_interfaces", NetworkInterface, True),
    ("network_addresses", NetworkAddress, True),
    ("network_connections", NetworkConnection, True),
    ("consumption_settings", ConsumptionSetting, True),
    ("consumption_meters", ConsumptionMeter, True),
    ("consumption_readings", ConsumptionReading, True),
    ("consumption_notes", ConsumptionNote, True),
    ("dashboard_settings", DashboardSetting, True),
    ("service_workloads", ServiceWorkload, True),
    ("audit_events", AuditEvent, False),
)


class PortabilityService:
    export_version = "1.0"

    def __init__(self, session: Session) -> None:
        self.session = session

    def export_payload(self) -> dict[str, Any]:
        data = {name: self._dump_rows(model) for name, model, _ in EXPORT_MODELS}
        data["integration_settings"] = self._safe_integrations()
        return {
            "manifest": {
                "app_version": settings.app_version,
                "export_version": self.export_version,
                "created_at": datetime.now(UTC).isoformat(),
                "modules": list(data),
                "excluded_security_fields": [
                    "integration base URLs",
                    "integration accounts",
                    "passwords",
                    "tokens",
                    "API keys",
                ],
            },
            "data": data,
        }

    def csv_export(self, module: str) -> str:
        definition = next((item for item in EXPORT_MODELS if item[0] == module), None)
        if definition is None:
            raise ReleaseNotFoundError("Das Exportmodul wurde nicht gefunden")
        rows = self._dump_rows(definition[1])
        if not rows:
            return ""
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=["__module", *list(rows[0])])
        writer.writeheader()
        for row in rows:
            serialized: dict[str, object] = {
                key: (
                    json.dumps(value, ensure_ascii=False)
                    if isinstance(value, dict | list)
                    else value
                )
                for key, value in row.items()
            }
            serialized["__module"] = module
            writer.writerow(serialized)
        return output.getvalue()

    def preview(self, content: bytes) -> ImportPreviewRead:
        payload = self._parse(content)
        manifest = payload.get("manifest")
        data = payload.get("data")
        if not isinstance(manifest, dict) or not isinstance(data, dict):
            raise ReleaseValidationError("Der Export benötigt Manifest und Datenbereich")
        export_version = manifest.get("export_version")
        counts: dict[str, int] = {}
        conflicts: list[str] = []
        warnings: list[str] = []
        allowed = {name for name, _, importable in EXPORT_MODELS if importable}
        for module, rows in data.items():
            if module not in allowed:
                warnings.append(
                    f"{module}: wird aus Sicherheits- oder Kompatibilitätsgründen ignoriert"
                )
                continue
            if not isinstance(rows, list):
                raise ReleaseValidationError(f"{module}: Datensätze müssen als Liste vorliegen")
            counts[module] = len(rows)
            model = self._model(module)
            for row in rows:
                if isinstance(row, dict) and self._existing(model, row) is not None:
                    conflicts.append(f"{module}:{self._identity_text(model, row)}")
        return ImportPreviewRead(
            format="DocOfHome CSV" if manifest.get("format") == "csv" else "DocOfHome JSON",
            export_version=str(export_version) if export_version is not None else None,
            record_counts=counts,
            conflicts=conflicts[:500],
            warnings=warnings,
            writable=False,
        )

    def apply(self, content: bytes, *, strategy: str) -> ImportResultRead:
        if strategy not in {"fail", "skip"}:
            raise ReleaseValidationError("Konfliktstrategie muss fail oder skip sein")
        payload = self._parse(content)
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ReleaseValidationError("Der Datenbereich fehlt")
        created = 0
        skipped = 0
        conflict_count = 0
        modules: list[str] = []
        try:
            self.session.exec(text("PRAGMA defer_foreign_keys=ON"))
            for module, model, importable in EXPORT_MODELS:
                if not importable:
                    continue
                rows = data.get(module, [])
                if not isinstance(rows, list):
                    raise ReleaseValidationError(f"{module}: ungültiges Datenformat")
                if rows:
                    modules.append(module)
                for raw in rows:
                    if not isinstance(raw, dict):
                        raise ReleaseValidationError(f"{module}: ungültiger Datensatz")
                    row = cast(dict[str, object], raw)
                    if self._existing(model, row) is not None:
                        conflict_count += 1
                        if strategy == "fail":
                            raise ReleaseConflictError(
                                f"Konflikt bei {module}:{self._identity_text(model, row)}"
                            )
                        skipped += 1
                        continue
                    self.session.add(model.model_validate(row))
                    created += 1
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return ImportResultRead(
            created=created,
            skipped=skipped,
            conflicts=conflict_count,
            modules=modules,
        )

    def audit_events(
        self,
        *,
        object_type: str | None = None,
        object_id: str | None = None,
        action: str | None = None,
        limit: int = 200,
    ) -> list[AuditEventRead]:
        statement = select(AuditEvent)
        if object_type:
            statement = statement.where(AuditEvent.object_type == object_type)
        if object_id:
            statement = statement.where(AuditEvent.object_id == object_id)
        if action:
            statement = statement.where(AuditEvent.action == action)
        records = self.session.exec(
            statement.order_by(col(AuditEvent.created_at).desc()).limit(limit)
        ).all()
        result: list[AuditEventRead] = []
        for item in records:
            change = json.loads(item.change_json)
            label, route = self._audit_object_context(item.object_type, item.object_id, change)
            result.append(
                AuditEventRead(
                    id=item.id,
                    object_type=item.object_type,
                    object_id=item.object_id,
                    object_label=label,
                    object_route=route,
                    action=item.action,
                    change=change,
                    display_change=self._audit_display_change(item.object_type, change),
                    created_at=item.created_at
                    if item.created_at.tzinfo
                    else item.created_at.replace(tzinfo=UTC),
                )
            )
        return result

    def _audit_display_change(
        self,
        object_type: str,
        change: dict[str, object],
    ) -> dict[str, object]:
        result: dict[str, object] = {}
        for field, raw in change.items():
            if isinstance(raw, dict) and ("from" in raw or "to" in raw):
                result[field] = {
                    "from": self._audit_display_value(
                        object_type, field, raw.get("from"), change
                    ),
                    "to": self._audit_display_value(
                        object_type, field, raw.get("to"), change
                    ),
                }
            else:
                result[field] = self._audit_display_value(object_type, field, raw, change)
        return result

    def _audit_display_value(
        self,
        object_type: str,
        field: str,
        value: object,
        change: dict[str, object],
    ) -> object:
        if value is None or value == "[redacted]":
            return value
        if isinstance(value, list):
            return [
                self._audit_display_value(object_type, field, item, change)
                for item in value
            ]
        if not isinstance(value, str):
            return value

        reference_models: dict[str, type[SQLModel]] = {
            "asset_id": Asset,
            "source_asset_id": Asset,
            "target_asset_id": Asset,
            "host_asset_id": Asset,
            "asset_type_id": AssetType,
            "product_id": Product,
            "location_id": Location,
            "label_id": Label,
            "network_device_id": NetworkDevice,
            "interface_id": NetworkInterface,
            "source_interface_id": NetworkInterface,
            "target_interface_id": NetworkInterface,
            "segment_id": NetworkSegment,
            "meter_id": ConsumptionMeter,
            "parent_meter_id": ConsumptionMeter,
            "work_item_id": WorkItem,
            "distribution_id": ElectricalDistribution,
            "parent_distribution_id": ElectricalDistribution,
            "circuit_id": ElectricalCircuit,
            "protective_device_id": ElectricalProtectiveDevice,
        }
        model = reference_models.get(field)
        if field == "parent_id" and object_type == "locations":
            model = Location
        if field == "target_id" and object_type == "work_items":
            target_type = self._audit_change_value(change.get("target_type"))
            model = {
                "asset": Asset,
                "location": Location,
                "distribution": ElectricalDistribution,
                "protective_device": ElectricalProtectiveDevice,
                "circuit": ElectricalCircuit,
            }.get(str(target_type))
        if model is None:
            return value
        try:
            identity = UUID(value)
        except ValueError:
            return value
        try:
            record = self.session.get(model, identity)
        except (TypeError, ValueError):
            return value
        return self._audit_record_label(record) or value

    @staticmethod
    def _audit_change_value(raw: object) -> object:
        if isinstance(raw, dict):
            return raw.get("to") if raw.get("to") is not None else raw.get("from")
        return raw

    def _audit_record_label(self, record: SQLModel | None) -> str | None:
        if record is None:
            return None
        if isinstance(record, NetworkDevice):
            asset = self.session.get(Asset, record.asset_id)
            return asset.name if asset is not None else record.hostname
        if isinstance(record, NetworkInterface):
            device = self.session.get(NetworkDevice, record.network_device_id)
            device_label = self._audit_record_label(device)
            return f"{device_label} · {record.name}" if device_label else record.name
        if isinstance(record, ElectricalDistribution):
            return record.designation or f"Verteilung {str(record.id)[:8]}"
        if isinstance(record, ElectricalProtectiveDevice):
            return f"{record.device_type.upper()} {str(record.id)[:8]}"
        for attribute in (
            "name",
            "title",
            "designation",
            "hostname",
            "address",
            "cidr",
            "kind",
        ):
            candidate = getattr(record, attribute, None)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return None

    def _audit_object_context(
        self,
        object_type: str,
        object_id: str,
        change: dict[str, object],
    ) -> tuple[str | None, str | None]:
        label: str | None = None
        record: SQLModel | None = None
        definition = next((item for item in EXPORT_MODELS if item[0] == object_type), None)
        if definition is not None and object_id not in {"", "pending"}:
            model = definition[1]
            try:
                identity: object = UUID(object_id)
            except ValueError:
                identity = object_id
            try:
                record = self.session.get(model, identity)
            except (TypeError, ValueError):
                record = None

        label = self._audit_record_label(record)

        if label is None:
            for key in ("name", "title", "hostname", "address", "cidr"):
                raw = change.get(key)
                if isinstance(raw, dict):
                    candidate = raw.get("to") or raw.get("from")
                    if isinstance(candidate, str) and candidate.strip():
                        label = candidate.strip()
                        break

        routes = {
            "assets": f"/assets/{object_id}",
            "locations": f"/locations/{object_id}",
            "network_devices": f"/network/devices/{object_id}",
            "electrical_distributions": f"/electrical/distributions/{object_id}",
            "electrical_circuits": f"/electrical/circuits/{object_id}",
            "consumption_meters": "/consumption",
            "consumption_readings": "/consumption",
            "work_items": "/maintenance",
            "wiki_pages": "/wiki",
            "domain_notes": "/wiki",
            "service_workloads": "/workloads",
            "quality_runs": "/quality",
            "quality_issues": "/quality",
        }
        route = routes.get(object_type)
        if record is not None and getattr(record, "deleted_at", None) is not None:
            route = "/archive"
        return label, route

    def _dump_rows(self, model: type[ModelT]) -> list[dict[str, Any]]:
        return [
            cast(dict[str, Any], item.model_dump(mode="json"))
            for item in self.session.exec(select(model)).all()
        ]

    def _safe_integrations(self) -> list[dict[str, object]]:
        from app.models.integration_setting import IntegrationSetting

        return [
            {"kind": item.kind, "enabled": item.enabled}
            for item in self.session.exec(select(IntegrationSetting)).all()
        ]

    @staticmethod
    def _parse(content: bytes) -> dict[str, object]:
        if not content or len(content) > 100 * 1024 * 1024:
            raise ReleaseValidationError("Die Importdatei ist leer oder größer als 100 MiB")
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ReleaseValidationError("Die Importdatei ist kein gültiges UTF-8") from exc
        try:
            parsed = json.loads(decoded)
        except json.JSONDecodeError:
            return PortabilityService._parse_csv(decoded)
        if not isinstance(parsed, dict):
            raise ReleaseValidationError("Die Importdatei benötigt ein JSON-Objekt")
        return cast(dict[str, object], parsed)

    @staticmethod
    def _parse_csv(content: str) -> dict[str, object]:
        try:
            reader = csv.DictReader(io.StringIO(content))
            if not reader.fieldnames or "__module" not in reader.fieldnames:
                raise ReleaseValidationError(
                    "CSV-Import benötigt die von DocOfHome exportierte Spalte __module"
                )
            allowed = {name for name, _, importable in EXPORT_MODELS if importable}
            grouped: dict[str, list[dict[str, object]]] = {}
            for raw in reader:
                module = (raw.pop("__module", None) or "").strip()
                if not module:
                    raise ReleaseValidationError("CSV-Zeile ohne Modulzuordnung")
                if module not in allowed:
                    raise ReleaseValidationError(f"Unbekanntes CSV-Modul: {module}")
                row: dict[str, object] = {}
                for key, value in raw.items():
                    if key is None:
                        continue
                    if value is None or value == "":
                        row[key] = None
                    elif value in {"True", "False", "true", "false"}:
                        row[key] = value.casefold() == "true"
                    elif value[:1] in {"[", "{"}:
                        try:
                            row[key] = json.loads(value)
                        except json.JSONDecodeError:
                            row[key] = value
                    else:
                        row[key] = value
                grouped.setdefault(module, []).append(row)
        except csv.Error as exc:
            raise ReleaseValidationError("Die CSV-Datei ist ungültig") from exc
        return {
            "manifest": {
                "app_version": settings.app_version,
                "export_version": PortabilityService.export_version,
                "format": "csv",
            },
            "data": grouped,
        }

    @staticmethod
    def _model(module: str) -> type[SQLModel]:
        for name, model, importable in EXPORT_MODELS:
            if name == module and importable:
                return model
        raise ReleaseNotFoundError("Das Importmodul wurde nicht gefunden")

    def _existing(self, model: type[SQLModel], row: dict[str, object]) -> SQLModel | None:
        mapper = sa_inspect(model)
        names = [column.key for column in mapper.primary_key]
        if not names or any(name not in row for name in names):
            raise ReleaseValidationError(f"{model.__name__}: Primärschlüssel fehlt")
        try:
            validated = model.model_validate(row)
        except ValidationError as exc:
            raise ReleaseValidationError(
                f"{model.__name__}: ungültiger Datensatz: {exc.errors()[0]['msg']}"
            ) from exc
        identity: object = (
            getattr(validated, names[0])
            if len(names) == 1
            else tuple(getattr(validated, name) for name in names)
        )
        return self.session.get(model, identity)

    @staticmethod
    def _identity_text(model: type[SQLModel], row: dict[str, object]) -> str:
        names = [column.key for column in sa_inspect(model).primary_key]
        return "/".join(str(row.get(name, "?")) for name in names)


class GuidedSetupService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[GuidedSetupDraftRead]:
        records = self.session.exec(
            select(GuidedSetupDraft).order_by(col(GuidedSetupDraft.updated_at).desc())
        ).all()
        return [self._read(item) for item in records]

    def create(self, payload: GuidedSetupDraftWrite) -> GuidedSetupDraftRead:
        record = GuidedSetupDraft(
            name=payload.name,
            current_step=payload.current_step,
            data_json=json.dumps(payload.data, ensure_ascii=False, separators=(",", ":")),
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._read(record)

    def update(
        self,
        draft_id: UUID,
        payload: GuidedSetupDraftWrite,
    ) -> GuidedSetupDraftRead:
        record = self._require(draft_id)
        if record.status == "applied":
            raise ReleaseConflictError("Ein angewendeter Entwurf ist unveränderlich")
        record.name = payload.name
        record.current_step = payload.current_step
        record.data_json = json.dumps(payload.data, ensure_ascii=False, separators=(",", ":"))
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._read(record)

    def preview(self, draft_id: UUID) -> GuidedSetupPreviewRead:
        record = self._require(draft_id)
        data = self._data(record)
        actions: list[str] = []
        warnings: list[str] = []
        errors: list[str] = []
        duplicates: list[UUID] = []
        existing_id = self._uuid(data.get("existing_asset_id"))
        asset_payload = self._object(data, "asset")
        if existing_id is not None:
            asset = self.session.get(Asset, existing_id)
            if asset is None or asset.deleted_at is not None:
                errors.append("Das ausgewählte bestehende Asset wurde nicht gefunden")
            else:
                actions.append(f"Bestehendes Asset „{asset.name}“ wiederverwenden")
        elif asset_payload:
            try:
                asset_write = AssetWrite.model_validate(asset_payload)
                actions.append(f"Asset „{asset_write.name}“ transaktional anlegen")
                matches = [
                    item
                    for item in AssetRepository(self.session).all()
                    if item.name.casefold() == asset_write.name.casefold()
                ]
                duplicates.extend(item.id for item in matches)
                if matches:
                    errors.append(
                        "Ein Asset mit diesem Namen existiert bereits; bitte wiederverwenden"
                    )
            except ValidationError as exc:
                errors.append(f"Assetdaten unvollständig: {exc.errors()[0]['msg']}")
        else:
            errors.append("Asset auswählen oder vollständig erfassen")
        for key, label in (
            ("network", "Netzwerkprofil"),
            ("consumption", "Verbrauchszähler"),
            ("home_assistant", "Home-Assistant-Zuordnung"),
            ("documents", "Nextcloud-Dokumentverknüpfungen"),
            ("images", "Immich-Bildverknüpfungen"),
            ("maintenance", "Wartung"),
            ("note", "offene Notiz"),
            ("electrical", "Stromkreiszuordnung"),
        ):
            value = data.get(key)
            if value:
                actions.append(f"{label} anlegen oder zuordnen")
        if not data.get("network") and not data.get("consumption"):
            warnings.append("Netzwerk und Verbrauch sind für dieses Objekt nicht aktiviert")
        return GuidedSetupPreviewRead(
            draft_id=draft_id,
            actions=actions,
            warnings=warnings,
            errors=errors,
            duplicate_asset_ids=duplicates,
            can_apply=not errors and record.status == "draft",
        )

    def apply(self, draft_id: UUID) -> GuidedSetupApplyRead:
        preview = self.preview(draft_id)
        if not preview.can_apply:
            raise ReleaseValidationError("Der Entwurf enthält noch Fehler")
        record = self._require(draft_id)
        data = self._data(record)
        created_ids: list[UUID] = []
        try:
            existing_id = self._uuid(data.get("existing_asset_id"))
            if existing_id is not None:
                asset = self.session.get(Asset, existing_id)
                if asset is None:
                    raise ReleaseValidationError("Das bestehende Asset wurde nicht gefunden")
            else:
                asset_write = AssetWrite.model_validate(self._object(data, "asset"))
                asset = AssetService(self.session)._build_asset(asset_write)
                created_ids.append(asset.id)
            self._apply_network(data, asset, created_ids)
            self._apply_consumption(data, asset, created_ids)
            self._apply_links(data, asset, created_ids)
            self._apply_maintenance(data, asset, created_ids)
            self._apply_note_and_circuit(data, asset, created_ids)
            record.status = "applied"
            record.current_step = 11
            record.updated_at = datetime.now(UTC)
            self.session.add(record)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return GuidedSetupApplyRead(
            draft_id=draft_id,
            asset_id=asset.id,
            created_object_ids=created_ids,
            applied_at=datetime.now(UTC),
        )

    def _apply_network(
        self,
        data: dict[str, object],
        asset: Asset,
        created_ids: list[UUID],
    ) -> None:
        payload = self._object(data, "network")
        if not payload:
            return
        role = str(payload.get("role") or "other")
        if role not in {
            "router",
            "firewall",
            "switch",
            "access_point",
            "server",
            "nas",
            "client",
            "iot",
            "printer",
            "controller",
            "other",
        }:
            raise ReleaseValidationError("Ungültige Netzwerkrolle")
        network = NetworkDevice(
            asset_id=asset.id,
            role=role,
            hostname=self._text(payload.get("hostname")),
            management_url=self._text(payload.get("management_url")),
            notes=self._text(payload.get("notes")),
        )
        self.session.add(network)
        self.session.flush()
        created_ids.append(network.id)

    def _apply_consumption(
        self,
        data: dict[str, object],
        asset: Asset,
        created_ids: list[UUID],
    ) -> None:
        payload = self._object(data, "consumption")
        if not payload:
            return
        payload["asset_id"] = asset.id
        meter_write = ConsumptionMeterWrite.model_validate(payload)
        ConsumptionService(self.session)._validate_meter(meter_write)
        meter = ConsumptionMeter(
            name=meter_write.name,
            meter_type=meter_write.meter_type.value,
            unit=meter_write.unit,
            decimals=meter_write.decimals,
            sort_order=meter_write.sort_order,
            serial_number=meter_write.serial_number,
            asset_id=asset.id,
            location_id=meter_write.location_id,
            parent_meter_id=meter_write.parent_meter_id,
            home_assistant_entity_id=meter_write.home_assistant_entity_id,
            water_role=meter_write.water_role.value,
            primary_for_dashboard=meter_write.primary_for_dashboard,
            reading_schedule_day=meter_write.reading_schedule_day,
            reading_schedule_last_day=meter_write.reading_schedule_last_day,
            reminder_days_json=json.dumps(meter_write.reminder_days),
            notes=meter_write.notes,
        )
        self.session.add(meter)
        self.session.flush()
        created_ids.append(meter.id)

    def _apply_links(
        self,
        data: dict[str, object],
        asset: Asset,
        created_ids: list[UUID],
    ) -> None:
        home_assistant = self._object(data, "home_assistant")
        for object_type in ("device", "entity"):
            values = home_assistant.get(f"{object_type}_ids", [])
            if isinstance(values, list):
                for external_id in values:
                    link = HomeAssistantAssetLink(
                        object_type=object_type,
                        external_id=str(external_id),
                        asset_id=asset.id,
                    )
                    self.session.add(link)
                    self.session.flush()
                    created_ids.append(link.id)
        documents = data.get("documents", [])
        if isinstance(documents, list):
            for raw in documents:
                if not isinstance(raw, dict):
                    continue
                path = self._text(raw.get("path"))
                if not path:
                    continue
                link = DocumentLink(
                    target_type="asset",
                    target_id=asset.id,
                    document_path=path,
                    document_name=self._text(raw.get("name")) or path.rsplit("/", 1)[-1],
                )
                self.session.add(link)
                self.session.flush()
                created_ids.append(link.id)
        images = data.get("images", [])
        if isinstance(images, list):
            for raw in images:
                if not isinstance(raw, dict):
                    continue
                image_id = self._text(raw.get("id"))
                name = self._text(raw.get("name"))
                if not image_id or not name:
                    continue
                link = ImmichAssetLink(
                    asset_id=asset.id,
                    immich_asset_id=image_id,
                    original_file_name=name,
                )
                self.session.add(link)
                self.session.flush()
                created_ids.append(link.id)

    def _apply_maintenance(
        self,
        data: dict[str, object],
        asset: Asset,
        created_ids: list[UUID],
    ) -> None:
        payload = self._object(data, "maintenance")
        if not payload:
            return
        title = self._text(payload.get("title"))
        if not title:
            raise ReleaseValidationError("Die Wartung benötigt einen Titel")
        due_at = self._datetime(payload.get("due_at"))
        item = WorkItem(
            item_type="maintenance",
            title=title,
            description=self._text(payload.get("description")),
            target_type="asset",
            target_id=asset.id,
            due_at=due_at,
            priority=str(payload.get("priority") or "normal"),
        )
        self.session.add(item)
        self.session.flush()
        created_ids.append(item.id)

    def _apply_note_and_circuit(
        self,
        data: dict[str, object],
        asset: Asset,
        created_ids: list[UUID],
    ) -> None:
        note = self._text(data.get("note"))
        if note:
            record = DomainNote(target_type="asset", target_id=asset.id, content=note)
            self.session.add(record)
            self.session.flush()
            created_ids.append(record.id)
        electrical = self._object(data, "electrical")
        circuit_id = self._uuid(electrical.get("circuit_id"))
        if circuit_id is not None:
            circuit = self.session.get(ElectricalCircuit, circuit_id)
            if circuit is None or circuit.deleted_at is not None:
                raise ReleaseValidationError("Der ausgewählte Stromkreis wurde nicht gefunden")
            link = ElectricalCircuitAssetLink(circuit_id=circuit_id, asset_id=asset.id)
            self.session.add(link)
            self.session.flush()
            created_ids.append(link.id)

    def _require(self, draft_id: UUID) -> GuidedSetupDraft:
        record = self.session.get(GuidedSetupDraft, draft_id)
        if record is None:
            raise ReleaseNotFoundError("Der Assistentenentwurf wurde nicht gefunden")
        return record

    @staticmethod
    def _data(record: GuidedSetupDraft) -> dict[str, object]:
        parsed = json.loads(record.data_json)
        return cast(dict[str, object], parsed if isinstance(parsed, dict) else {})

    @staticmethod
    def _object(data: dict[str, object], key: str) -> dict[str, object]:
        value = data.get(key)
        return cast(dict[str, object], dict(value)) if isinstance(value, dict) else {}

    @staticmethod
    def _uuid(value: object) -> UUID | None:
        if value in (None, ""):
            return None
        try:
            return UUID(str(value))
        except ValueError:
            return None

    @staticmethod
    def _text(value: object) -> str | None:
        normalized = str(value).strip() if value is not None else ""
        return normalized or None

    @staticmethod
    def _datetime(value: object) -> datetime | None:
        if value in (None, ""):
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ReleaseValidationError("Ungültiger Zeitpunkt im Assistenten") from exc
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

    @staticmethod
    def _read(record: GuidedSetupDraft) -> GuidedSetupDraftRead:
        return GuidedSetupDraftRead(
            id=record.id,
            name=record.name,
            current_step=record.current_step,
            data=json.loads(record.data_json),
            status=record.status,
            created_at=record.created_at
            if record.created_at.tzinfo
            else record.created_at.replace(tzinfo=UTC),
            updated_at=record.updated_at
            if record.updated_at.tzinfo
            else record.updated_at.replace(tzinfo=UTC),
        )
