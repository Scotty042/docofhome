from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from pathlib import PurePosixPath
from uuid import UUID

from sqlmodel import Session, select

from app.models.asset_engine import Asset, Location
from app.models.document_link import DocumentLink
from app.models.electrical_circuit import ElectricalCircuit, ElectricalCircuitAssetLink
from app.models.knowledge import WikiPage
from app.models.network import NetworkAddress, NetworkDevice, NetworkInterface
from app.models.quality import QualityIssue, QualityRun
from app.models.work import WorkItem
from app.repositories.settings import SettingsRepository
from app.schemas.documents import DocumentEntryType
from app.schemas.quality import QualityIssueRead, QualityReportRead, QualitySeverity
from app.schemas.work import WorkStatus
from app.services.documents import DocumentError, DocumentService


class QualityError(RuntimeError):
    pass


class QualityNotFoundError(QualityError):
    pass


class QualityService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def latest(self, *, create_if_missing: bool = True) -> QualityReportRead:
        run = self.session.exec(select(QualityRun).order_by(QualityRun.started_at.desc())).first()
        if run is None:
            if not create_if_missing:
                raise QualityNotFoundError("Noch keine Qualitätsprüfung vorhanden")
            return self.run(trigger="manual")
        return self._read(run)

    def run(self, *, trigger: str) -> QualityReportRead:
        if trigger not in {"manual", "scheduled"}:
            raise ValueError("Unsupported quality-run trigger")
        run = QualityRun(trigger=trigger)
        self.session.add(run)
        self.session.flush()
        issues = [
            *self._asset_issues(run.id),
            *self._location_issues(run.id),
            *self._electrical_issues(run.id),
            *self._network_issues(run.id),
            *self._wiki_issues(run.id),
            *self._work_issues(run.id),
            *self._document_issues(run.id),
        ]
        for issue in issues:
            self.session.add(issue)
        run.issue_count = len(issues)
        run.error_count = sum(issue.severity == QualitySeverity.ERROR.value for issue in issues)
        run.warning_count = sum(issue.severity == QualitySeverity.WARNING.value for issue in issues)
        run.info_count = sum(issue.severity == QualitySeverity.INFO.value for issue in issues)
        run.score = max(
            0,
            100 - run.error_count * 10 - run.warning_count * 4 - run.info_count,
        )
        run.completed_at = datetime.now(UTC)
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        self._retain_recent_runs(30)
        return self._read(run)

    def is_due(self) -> bool:
        run = self.session.exec(select(QualityRun).order_by(QualityRun.started_at.desc())).first()
        if run is None:
            return True
        started = self._aware(run.started_at)
        return datetime.now(UTC) >= started + timedelta(hours=24)

    def _asset_issues(self, run_id: UUID) -> Iterable[QualityIssue]:
        assets = self.session.exec(select(Asset).where(Asset.deleted_at.is_(None))).all()
        for asset in assets:
            route = f"/assets/{asset.id}"
            if asset.location_id is None:
                yield self._issue(
                    run_id,
                    "assets",
                    QualitySeverity.WARNING,
                    "asset_missing_location",
                    f"{asset.name}: kein Bereich zugeordnet",
                    "Das Asset sollte einem Raum oder Bereich zugeordnet werden.",
                    "asset",
                    asset.id,
                    route,
                )
            if not asset.description or not asset.description.strip():
                yield self._issue(
                    run_id,
                    "assets",
                    QualitySeverity.INFO,
                    "asset_missing_description",
                    f"{asset.name}: Beschreibung fehlt",
                    "Eine kurze Beschreibung erleichtert spätere Suche und Wartung.",
                    "asset",
                    asset.id,
                    route,
                )
            if not asset.serial_number and not asset.inventory_number:
                yield self._issue(
                    run_id,
                    "assets",
                    QualitySeverity.INFO,
                    "asset_missing_identifier",
                    f"{asset.name}: keine reale Kennung",
                    "Serien- oder Inventarnummer ist nicht hinterlegt.",
                    "asset",
                    asset.id,
                    route,
                )

    def _location_issues(self, run_id: UUID) -> Iterable[QualityIssue]:
        locations = self.session.exec(select(Location).where(Location.deleted_at.is_(None))).all()
        for location in locations:
            if location.location_type == "building":
                continue
            if not location.description and not location.notes:
                yield self._issue(
                    run_id,
                    "locations",
                    QualitySeverity.INFO,
                    "location_missing_description",
                    f"{location.name}: keine Beschreibung oder Notiz",
                    "Besonderheiten des Bereichs sind noch nicht dokumentiert.",
                    "location",
                    location.id,
                    f"/locations/{location.id}",
                )

    def _electrical_issues(self, run_id: UUID) -> Iterable[QualityIssue]:
        circuits = self.session.exec(
            select(ElectricalCircuit).where(ElectricalCircuit.deleted_at.is_(None))
        ).all()
        linked_circuits = set(
            self.session.exec(
                select(ElectricalCircuitAssetLink.circuit_id).where(
                    ElectricalCircuitAssetLink.deleted_at.is_(None)
                )
            ).all()
        )
        for circuit in circuits:
            route = f"/electrical/circuits/{circuit.id}"
            if not circuit.description:
                yield self._issue(
                    run_id,
                    "electrical",
                    QualitySeverity.WARNING,
                    "circuit_missing_description",
                    f"{circuit.name}: Stromkreisbeschreibung fehlt",
                    "Der versorgte Zweck sollte eindeutig dokumentiert sein.",
                    "circuit",
                    circuit.id,
                    route,
                )
            if circuit.id not in linked_circuits:
                yield self._issue(
                    run_id,
                    "electrical",
                    QualitySeverity.INFO,
                    "circuit_without_assets",
                    f"{circuit.name}: keine Assets zugeordnet",
                    "Prüfe, ob die angeschlossenen Verbraucher erfasst werden können.",
                    "circuit",
                    circuit.id,
                    route,
                )
            if circuit.protective_device_id is None:
                yield self._issue(
                    run_id,
                    "electrical",
                    QualitySeverity.WARNING,
                    "circuit_without_protection",
                    f"{circuit.name}: kein Schutzgerät zugeordnet",
                    "Der Stromkreis besitzt keine dokumentierte Schutzgerätezuordnung.",
                    "circuit",
                    circuit.id,
                    route,
                )

    def _network_issues(self, run_id: UUID) -> Iterable[QualityIssue]:
        assets = {item.id: item for item in self.session.exec(select(Asset)).all()}
        interfaces = self.session.exec(
            select(NetworkInterface).where(NetworkInterface.deleted_at.is_(None))
        ).all()
        addresses = self.session.exec(
            select(NetworkAddress).where(NetworkAddress.deleted_at.is_(None))
        ).all()
        interface_ids_with_addresses = {item.interface_id for item in addresses}
        for device in self.session.exec(
            select(NetworkDevice).where(NetworkDevice.deleted_at.is_(None))
        ).all():
            asset = assets.get(device.asset_id)
            if asset is None or asset.deleted_at is not None:
                continue
            route = f"/network/devices/{device.id}"
            device_interfaces = [item for item in interfaces if item.network_device_id == device.id]
            if not device.hostname:
                yield self._issue(
                    run_id,
                    "network",
                    QualitySeverity.INFO,
                    "network_device_missing_hostname",
                    f"{asset.name}: Hostname fehlt",
                    "Für das Netzwerkgerät ist noch kein Hostname dokumentiert.",
                    "network_device",
                    device.id,
                    route,
                )
            if not device_interfaces:
                yield self._issue(
                    run_id,
                    "network",
                    QualitySeverity.WARNING,
                    "network_device_without_interfaces",
                    f"{asset.name}: keine Schnittstelle",
                    "Mindestens eine physische oder virtuelle Netzwerkschnittstelle "
                    "sollte erfasst werden.",
                    "network_device",
                    device.id,
                    route,
                )
            elif not any(item.id in interface_ids_with_addresses for item in device_interfaces):
                yield self._issue(
                    run_id,
                    "network",
                    QualitySeverity.INFO,
                    "network_device_without_addresses",
                    f"{asset.name}: keine IP-Adresse",
                    "Für keine Schnittstelle ist eine IP-Adresse dokumentiert.",
                    "network_device",
                    device.id,
                    route,
                )

    def _wiki_issues(self, run_id: UUID) -> Iterable[QualityIssue]:
        pages = self.session.exec(select(WikiPage).where(WikiPage.deleted_at.is_(None))).all()
        for page in pages:
            if not page.content.strip():
                yield self._issue(
                    run_id,
                    "knowledge",
                    QualitySeverity.WARNING,
                    "wiki_page_empty",
                    f"Wiki-Seite „{page.title}“ ist leer",
                    "Die Seite enthält noch keinen Wissensinhalt.",
                    "wiki_page",
                    page.id,
                    f"/wiki?page={page.id}",
                )

    def _work_issues(self, run_id: UUID) -> Iterable[QualityIssue]:
        now = datetime.now(UTC)
        items = self.session.exec(
            select(WorkItem)
            .where(WorkItem.deleted_at.is_(None))
            .where(WorkItem.status == WorkStatus.OPEN.value)
        ).all()
        for item in items:
            if item.due_at is None or self._aware(item.due_at) >= now:
                continue
            yield self._issue(
                run_id,
                "maintenance",
                QualitySeverity.ERROR,
                "work_item_overdue",
                f"Überfällig: {item.title}",
                f"Fällig seit {self._aware(item.due_at).strftime('%d.%m.%Y %H:%M')}.",
                "work_item",
                item.id,
                "/maintenance",
            )

    def _document_issues(self, run_id: UUID) -> Iterable[QualityIssue]:
        integration = SettingsRepository(self.session).get_integration("nextcloud")
        if integration is None or not integration.enabled:
            return []
        links = self.session.exec(
            select(DocumentLink).where(DocumentLink.deleted_at.is_(None))
        ).all()
        document_service = DocumentService(self.session)
        folder_cache: dict[str, set[str] | None] = {}
        issues: list[QualityIssue] = []
        for link in links:
            pure = PurePosixPath(link.document_path)
            folder = "/".join(pure.parts[:-1])
            if folder not in folder_cache:
                try:
                    listing = document_service.list_entries(folder)
                    folder_cache[folder] = {
                        entry.path
                        for entry in listing.items
                        if entry.entry_type == DocumentEntryType.FILE
                    }
                except DocumentError:
                    folder_cache[folder] = None
            available = folder_cache[folder]
            if available is None:
                continue
            if link.document_path in available:
                continue
            issues.append(
                self._issue(
                    run_id,
                    "documents",
                    QualitySeverity.WARNING,
                    "document_link_unavailable",
                    f"Dokument nicht verfügbar: {link.document_name}",
                    f"Die verknüpfte Datei wurde unter {link.document_path} nicht gefunden.",
                    link.target_type,
                    link.target_id,
                    self._target_route(link.target_type, link.target_id),
                )
            )
        return issues

    def _target_route(self, target_type: str, target_id: UUID) -> str | None:
        routes = {
            "asset": f"/assets/{target_id}",
            "location": f"/locations/{target_id}",
            "distribution": f"/electrical/distributions/{target_id}",
            "protective_device": f"/electrical/protective-devices/{target_id}/edit",
            "circuit": f"/electrical/circuits/{target_id}",
        }
        return routes.get(target_type)

    def _read(self, run: QualityRun) -> QualityReportRead:
        if run.completed_at is None:
            raise QualityError("Qualitätsprüfung ist noch nicht abgeschlossen")
        issues = self.session.exec(
            select(QualityIssue)
            .where(QualityIssue.run_id == run.id)
            .order_by(QualityIssue.severity, QualityIssue.category, QualityIssue.title)
        ).all()
        return QualityReportRead(
            id=run.id,
            trigger=run.trigger,
            score=run.score,
            issue_count=run.issue_count,
            error_count=run.error_count,
            warning_count=run.warning_count,
            info_count=run.info_count,
            started_at=self._aware(run.started_at),
            completed_at=self._aware(run.completed_at),
            issues=[
                QualityIssueRead(
                    id=issue.id,
                    category=issue.category,
                    severity=QualitySeverity(issue.severity),
                    code=issue.code,
                    title=issue.title,
                    description=issue.description,
                    target_type=issue.target_type,
                    target_id=issue.target_id,
                    route=issue.route,
                    created_at=self._aware(issue.created_at),
                )
                for issue in issues
            ],
        )

    def _retain_recent_runs(self, count: int) -> None:
        runs = list(
            self.session.exec(select(QualityRun).order_by(QualityRun.started_at.desc())).all()
        )
        for run in runs[count:]:
            issues = self.session.exec(
                select(QualityIssue).where(QualityIssue.run_id == run.id)
            ).all()
            for issue in issues:
                self.session.delete(issue)
            self.session.delete(run)
        self.session.commit()

    @staticmethod
    def _issue(
        run_id: UUID,
        category: str,
        severity: QualitySeverity,
        code: str,
        title: str,
        description: str,
        target_type: str | None,
        target_id: UUID | None,
        route: str | None,
    ) -> QualityIssue:
        return QualityIssue(
            run_id=run_id,
            category=category,
            severity=severity.value,
            code=code,
            title=title,
            description=description,
            target_type=target_type,
            target_id=target_id,
            route=route,
        )

    @staticmethod
    def _aware(value: datetime) -> datetime:
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
