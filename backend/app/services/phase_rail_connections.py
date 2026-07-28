import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlmodel import Session, col, delete, select

from app.electrical_phase_rail import (
    phase_rail_device_phases,
    phase_rail_din_asset_phases,
    rail_fully_covers_device,
)
from app.models.asset_engine import Asset
from app.models.electrical import (
    ElectricalAssetPlacement,
    ElectricalCabinetComponent,
    ElectricalComponent,
    ElectricalProtectiveDevice,
)
from app.models.electrical_topology import ElectricalConnection
from app.models.smart_meter import (
    SmartMeterMeasurementEntity,
    SmartMeterMeasurementPoint,
)
from app.repositories.electrical import ElectricalProtectiveDeviceRepository
from app.schemas.electrical_topology import ElectricalPhase
from app.services.din_width import effective_asset_module_width


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PhaseRailContact:
    """One physical DIN contact target below/above a phase rail."""

    target_kind: str
    target_id: UUID
    distribution_id: UUID
    area_id: UUID | None
    row_number: int
    start_position: int
    module_width: int
    device_type: str
    poles: int | None
    display_name: str

    @property
    def key(self) -> tuple[str, UUID]:
        return (self.target_kind, self.target_id)


class PhaseRailConnectionService:
    """Synchronize physical phase-rail contacts for every DIN device.

    A phase/comb rail is a physical contact strip. Every completely covered DIN
    device is therefore represented by one authoritative, read-only connection:

    * current DIN placements use the underlying ``asset`` endpoint;
    * legacy protective-device placements remain supported through the
      ``protective_device`` endpoint for existing installations.

    The line phases follow the rail pattern and the occupied TE positions. For a
    four-pole RCD/RCBO/SPD only the three line poles are connected; the fourth
    pole remains available for N.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def sync_distribution(self, distribution_id: UUID, *, verify: bool = True) -> int:
        self.session.flush()
        rails = list(
            self.session.exec(
                select(ElectricalCabinetComponent).where(
                    ElectricalCabinetComponent.distribution_id == distribution_id,
                    ElectricalCabinetComponent.component_type == "phase_rail",
                    col(ElectricalCabinetComponent.deleted_at).is_(None),
                )
            ).all()
        )
        contacts = self._contacts_for_distribution(distribution_id)
        desired_by_rail: dict[UUID, list[PhaseRailContact]] = {
            rail.id: [] for rail in rails
        }
        for contact in contacts:
            candidates = [
                rail
                for rail in rails
                if self._same_context(rail, contact)
                and rail_fully_covers_device(
                    rail_start=rail.start_position,
                    rail_width=rail.module_width,
                    device_start=contact.start_position,
                    device_width=contact.module_width,
                )
                and self._contact_phases(rail, contact)
            ]
            candidates.sort(
                key=lambda rail: (
                    rail.module_width,
                    rail.start_position,
                    rail.name.casefold(),
                    str(rail.id),
                )
            )
            if candidates:
                desired_by_rail[candidates[0].id].append(contact)

        synchronized = 0
        for rail in rails:
            synchronized += self._sync_rail_contacts(rail, desired_by_rail[rail.id])

        active_rail_ids = {rail.id for rail in rails}
        stale_sources = list(
            self.session.exec(
                select(ElectricalConnection).where(
                    ElectricalConnection.source_kind == "cabinet_component",
                    ElectricalConnection.connection_type == "busbar",
                    (
                        (ElectricalConnection.target_kind == "protective_device")
                        | (ElectricalConnection.target_kind == "asset")
                    ),
                    col(ElectricalConnection.deleted_at).is_(None),
                )
            ).all()
        )
        now = datetime.now(UTC)
        for connection in stale_sources:
            source = self.session.get(ElectricalCabinetComponent, connection.source_id)
            if source is None:
                self._archive_connection(connection, now)
                continue
            if (
                source.component_type == "phase_rail"
                and source.distribution_id == distribution_id
                and connection.source_id not in active_rail_ids
            ):
                self._archive_connection(connection, now)
        self.session.flush()
        if verify:
            self._verify_distribution_connections(distribution_id, desired_by_rail)
        return synchronized

    def sync_component(
        self,
        component: ElectricalCabinetComponent,
        *,
        previous_component_type: str | None = None,
        verify: bool = True,
    ) -> None:
        was_phase_rail = previous_component_type == "phase_rail"
        converted_from_phase_rail = was_phase_rail and component.component_type != "phase_rail"
        archived_phase_rail = (
            component.component_type == "phase_rail" and component.deleted_at is not None
        )
        if converted_from_phase_rail or archived_phase_rail:
            self._archive_outgoing(component.id)
        self.sync_distribution(component.distribution_id, verify=verify)

    def sync_rail(self, rail: ElectricalCabinetComponent, *, verify: bool = True) -> None:
        self.sync_distribution(rail.distribution_id, verify=verify)

    def sync_rail_with_visible_devices(
        self,
        rail: ElectricalCabinetComponent,
        visible_protective_device_ids: list[UUID],
        visible_asset_ids: list[UUID] | None = None,
        *,
        verify: bool = True,
    ) -> int:
        """Synchronize explicit UI candidates plus server-side discovery."""
        self.session.flush()
        if rail.component_type != "phase_rail" or rail.deleted_at is not None:
            return 0

        candidates: dict[tuple[str, UUID], PhaseRailContact] = {}
        rejections: list[str] = []
        explicit_protective_ids = list(dict.fromkeys(visible_protective_device_ids))
        explicit_asset_ids = list(dict.fromkeys(visible_asset_ids or []))

        for device_id in explicit_protective_ids:
            contact, reason = self._explicit_protective_candidate(rail, device_id)
            if contact is None:
                rejections.append(f"Schutzgerät {device_id}: {reason or 'nicht geeignet'}")
            else:
                candidates[contact.key] = contact

        for asset_id in explicit_asset_ids:
            contact, reason = self._explicit_asset_candidate(rail, asset_id)
            if contact is None:
                rejections.append(f"DIN-Asset {asset_id}: {reason or 'nicht geeignet'}")
            else:
                candidates[contact.key] = contact

        for contact in self._contacts_for_distribution(rail.distribution_id):
            if (
                self._same_context(rail, contact)
                and rail_fully_covers_device(
                    rail_start=rail.start_position,
                    rail_width=rail.module_width,
                    device_start=contact.start_position,
                    device_width=contact.module_width,
                )
                and self._contact_phases(rail, contact)
            ):
                candidates[contact.key] = contact

        covered = sorted(
            candidates.values(),
            key=lambda contact: (
                contact.start_position,
                contact.module_width,
                contact.target_kind,
                str(contact.target_id),
            ),
        )
        logger.warning(
            "Phase-rail synchronization: rail=%s distribution=%s explicit_protective=%d "
            "explicit_assets=%d covered=%d targets=%s rejected=%s",
            rail.id,
            rail.distribution_id,
            len(explicit_protective_ids),
            len(explicit_asset_ids),
            len(covered),
            ", ".join(
                f"{item.target_kind}:{item.display_name}@TE{item.start_position}"
                for item in covered[:20]
            ) or "-",
            " | ".join(rejections[:12]) if rejections else "-",
        )
        synchronized = self._sync_rail_contacts(rail, covered)
        self.session.flush()
        if verify:
            self._verify_distribution_connections(rail.distribution_id, {rail.id: covered})

        explicit_count = len(explicit_protective_ids) + len(explicit_asset_ids)
        if explicit_count and not covered:
            details = "; ".join(rejections[:16]) or "keine Kandidatendetails verfügbar"
            raise RuntimeError(
                "Keines der von der Verteilerschrankansicht gemeldeten DIN-Geräte "
                "konnte der Phasen-/Kammschiene zugeordnet werden. "
                f"Schiene: Bereich={rail.area_id}, Reihe={rail.row_number}, "
                f"TE={rail.start_position}–{rail.start_position + rail.module_width - 1}. "
                f"Prüfung: {details}"
            )
        return synchronized

    def _explicit_protective_candidate(
        self,
        rail: ElectricalCabinetComponent,
        device_id: UUID,
    ) -> tuple[PhaseRailContact | None, str | None]:
        device = self._active_device_by_id(device_id)
        if device is None:
            return None, "kein aktives Schutzgerät"
        contact = self._protective_contact(device)
        if contact is None:
            return None, "Platzierung oder DIN-Breite fehlt"
        return self._validate_explicit_contact(rail, contact)

    def _explicit_asset_candidate(
        self,
        rail: ElectricalCabinetComponent,
        asset_id: UUID,
    ) -> tuple[PhaseRailContact | None, str | None]:
        placement = self.session.exec(
            select(ElectricalAssetPlacement).where(
                ElectricalAssetPlacement.distribution_id == rail.distribution_id,
                ElectricalAssetPlacement.asset_id == asset_id,
                col(ElectricalAssetPlacement.deleted_at).is_(None),
            )
        ).first()
        if placement is None:
            return None, "keine aktive DIN-Platzierung"
        asset = self.session.get(Asset, placement.asset_id)
        if asset is None or asset.deleted_at is not None or asset.status == "retired":
            return None, "Asset ist archiviert oder außer Betrieb"
        electrical_component = self.session.exec(
            select(ElectricalComponent).where(
                ElectricalComponent.asset_id == asset.id,
                col(ElectricalComponent.deleted_at).is_(None),
            )
        ).first()
        if electrical_component is not None:
            return None, (
                "Asset besitzt bereits eine elektrische Komponentenrolle "
                f"({electrical_component.role}) und muss über diesen Endpunkt angebunden werden"
            )
        contact = self._asset_contact(placement, asset)
        return self._validate_explicit_contact(rail, contact)

    def _validate_explicit_contact(
        self,
        rail: ElectricalCabinetComponent,
        contact: PhaseRailContact,
    ) -> tuple[PhaseRailContact | None, str | None]:
        if contact.distribution_id != rail.distribution_id:
            return None, f"andere Verteilung ({contact.distribution_id})"
        if contact.area_id != rail.area_id:
            return None, f"anderer Bereich ({contact.area_id})"
        if contact.row_number != rail.row_number:
            return None, f"andere Reihe ({contact.row_number})"
        if not rail_fully_covers_device(
            rail_start=rail.start_position,
            rail_width=rail.module_width,
            device_start=contact.start_position,
            device_width=contact.module_width,
        ):
            end = contact.start_position + contact.module_width - 1
            return None, f"TE {contact.start_position}–{end} nicht vollständig überdeckt"
        if not self._contact_phases(rail, contact):
            return None, "keine wirksame Außenleiterphase berechenbar"
        return contact, None

    def _active_device_by_id(
        self, device_id: UUID
    ) -> ElectricalProtectiveDevice | None:
        try:
            projection = ElectricalProtectiveDeviceRepository(self.session).get(
                device_id,
                include_deleted=False,
            )
        except ValueError:
            projection = None
        if projection is not None:
            return projection.record
        device = self.session.get(ElectricalProtectiveDevice, device_id)
        if device is None:
            return None
        component = self.session.get(ElectricalComponent, device.id)
        if component is None or component.deleted_at is not None:
            return None
        asset = self.session.get(Asset, component.asset_id)
        if asset is None or asset.deleted_at is not None or asset.status == "retired":
            return None
        return device

    def archive_component_connections(self, component_id: UUID) -> None:
        now = datetime.now(UTC)
        records = list(
            self.session.exec(
                select(ElectricalConnection).where(
                    col(ElectricalConnection.deleted_at).is_(None),
                    (
                        (ElectricalConnection.source_kind == "cabinet_component")
                        & (ElectricalConnection.source_id == component_id)
                    )
                    | (
                        (ElectricalConnection.target_kind == "cabinet_component")
                        & (ElectricalConnection.target_id == component_id)
                    ),
                )
            ).all()
        )
        for connection in records:
            self._archive_connection(connection, now)
        self.session.flush()

    def _sync_rail_contacts(
        self,
        rail: ElectricalCabinetComponent,
        covered: list[PhaseRailContact],
    ) -> int:
        covered_keys = {contact.key for contact in covered}
        all_connections = list(
            self.session.exec(
                select(ElectricalConnection).where(
                    ElectricalConnection.source_kind == "cabinet_component",
                    ElectricalConnection.source_id == rail.id,
                    (
                        (ElectricalConnection.target_kind == "protective_device")
                        | (ElectricalConnection.target_kind == "asset")
                    ),
                )
            ).all()
        )
        all_connections.sort(
            key=lambda connection: (
                connection.deleted_at is not None,
                connection.created_at,
                str(connection.id),
            )
        )
        by_target: dict[tuple[str, UUID], ElectricalConnection] = {}
        duplicates: list[ElectricalConnection] = []
        for connection in all_connections:
            key = (connection.target_kind, connection.target_id)
            if key in by_target:
                duplicates.append(connection)
            else:
                by_target[key] = connection
        active_connections = [
            connection for connection in all_connections if connection.deleted_at is None
        ]
        now = datetime.now(UTC)
        synchronized = 0

        for contact in covered:
            phases = self._contact_phases(rail, contact)
            if not phases:
                continue
            connection = by_target.get(contact.key)
            created = connection is None
            if connection is None:
                connection = ElectricalConnection(
                    source_kind="cabinet_component",
                    source_id=rail.id,
                    target_kind=contact.target_kind,
                    target_id=contact.target_id,
                    connection_type="busbar",
                    label=None,
                    created_at=now,
                    updated_at=now,
                    deleted_at=now,
                )
            needs_activation = connection.deleted_at is not None
            changed = created
            if connection.connection_type != "busbar":
                connection.connection_type = "busbar"
                changed = True
            changed = self._set_phases(connection, phases) or changed
            for attribute, expected in (
                ("neutral", False),
                ("protective_earth", False),
                ("cable_type", None),
                ("cores", None),
                ("cross_section_mm2", None),
                ("length_m", None),
                ("route", None),
                ("notes", None),
                ("label", None),
            ):
                if getattr(connection, attribute) != expected:
                    setattr(connection, attribute, expected)
                    changed = True
            if changed:
                connection.updated_at = now
            self.session.add(connection)
            self.session.flush()
            self._archive_competing_incoming(
                contact.target_kind,
                contact.target_id,
                connection,
                now,
            )
            self.session.flush()
            if needs_activation:
                connection.deleted_at = None
                connection.updated_at = now
                self.session.add(connection)
                self.session.flush()

            synchronized += 1
            self._synchronize_measurement_phase(connection, phases, now)
            self._synchronize_endpoint_outputs(
                contact.target_kind,
                contact.target_id,
                phases,
                now,
            )

        for duplicate in duplicates:
            if duplicate.deleted_at is None:
                authoritative = by_target.get((duplicate.target_kind, duplicate.target_id))
                self._archive_connection(
                    duplicate,
                    now,
                    replacement_id=authoritative.id if authoritative is not None else None,
                )

        for connection in active_connections:
            if (connection.target_kind, connection.target_id) not in covered_keys:
                self._archive_connection(connection, now)

        reverse_connections = list(
            self.session.exec(
                select(ElectricalConnection).where(
                    (
                        (ElectricalConnection.source_kind == "protective_device")
                        | (ElectricalConnection.source_kind == "asset")
                    ),
                    ElectricalConnection.target_kind == "cabinet_component",
                    ElectricalConnection.target_id == rail.id,
                    ElectricalConnection.connection_type == "busbar",
                    col(ElectricalConnection.deleted_at).is_(None),
                )
            ).all()
        )
        for connection in reverse_connections:
            if (connection.source_kind, connection.source_id) in covered_keys:
                self._archive_connection(connection, now)
        return synchronized

    def _synchronize_endpoint_outputs(
        self,
        source_kind: str,
        source_id: UUID,
        phases: tuple[ElectricalPhase, ...],
        now: datetime,
    ) -> None:
        records = self.session.exec(
            select(ElectricalConnection).where(
                ElectricalConnection.source_kind == source_kind,
                ElectricalConnection.source_id == source_id,
                col(ElectricalConnection.deleted_at).is_(None),
            )
        ).all()
        for record in records:
            target_component = (
                self.session.get(ElectricalCabinetComponent, record.target_id)
                if record.target_kind == "cabinet_component"
                else None
            )
            if target_component is not None and target_component.component_type == "phase_rail":
                continue
            if self._set_phases(record, phases):
                record.updated_at = now
                self.session.add(record)
            self._synchronize_measurement_phase(record, phases, now)

    def _synchronize_measurement_phase(
        self,
        connection: ElectricalConnection,
        phases: tuple[ElectricalPhase, ...],
        now: datetime,
    ) -> None:
        line_phases = [
            phase
            for phase in phases
            if phase in {ElectricalPhase.L1, ElectricalPhase.L2, ElectricalPhase.L3}
        ]
        if len(line_phases) != 1:
            return
        points = self.session.exec(
            select(SmartMeterMeasurementPoint).where(
                SmartMeterMeasurementPoint.connection_id == connection.id,
                col(SmartMeterMeasurementPoint.deleted_at).is_(None),
            )
        ).all()
        for point in points:
            if (
                (point.phase is None or point.phase in {"L1", "L2", "L3"})
                and point.phase != line_phases[0].value
            ):
                point.phase = line_phases[0].value
                point.updated_at = now
                self.session.add(point)

    def _archive_competing_incoming(
        self,
        target_kind: str,
        target_id: UUID,
        authoritative: ElectricalConnection,
        now: datetime,
    ) -> None:
        competing = list(
            self.session.exec(
                select(ElectricalConnection).where(
                    ElectricalConnection.target_kind == target_kind,
                    ElectricalConnection.target_id == target_id,
                    ElectricalConnection.id != authoritative.id,
                    col(ElectricalConnection.deleted_at).is_(None),
                )
            ).all()
        )
        for obsolete in competing:
            self._archive_connection(obsolete, now, replacement_id=authoritative.id)

    def _archive_connection(
        self,
        connection: ElectricalConnection,
        now: datetime,
        *,
        replacement_id: UUID | None = None,
    ) -> None:
        measurement_points = self.session.exec(
            select(SmartMeterMeasurementPoint).where(
                SmartMeterMeasurementPoint.connection_id == connection.id,
                col(SmartMeterMeasurementPoint.deleted_at).is_(None),
            )
        ).all()
        for point in measurement_points:
            if replacement_id is not None:
                point.connection_id = replacement_id
            else:
                point.deleted_at = now
                self.session.exec(
                    delete(SmartMeterMeasurementEntity).where(
                        SmartMeterMeasurementEntity.measurement_point_id == point.id
                    )
                )
            point.updated_at = now
            self.session.add(point)
        connection.deleted_at = now
        connection.updated_at = now
        self.session.add(connection)

    def _archive_outgoing(self, component_id: UUID) -> None:
        now = datetime.now(UTC)
        records = self.session.exec(
            select(ElectricalConnection).where(
                ElectricalConnection.source_kind == "cabinet_component",
                ElectricalConnection.source_id == component_id,
                (
                    (ElectricalConnection.target_kind == "protective_device")
                    | (ElectricalConnection.target_kind == "asset")
                ),
                ElectricalConnection.connection_type == "busbar",
                col(ElectricalConnection.deleted_at).is_(None),
            )
        ).all()
        for connection in records:
            self._archive_connection(connection, now)

    def _contacts_for_distribution(self, distribution_id: UUID) -> list[PhaseRailContact]:
        contacts: dict[tuple[str, UUID], PhaseRailContact] = {}
        component_asset_ids = {
            component.asset_id
            for component in self.session.exec(
                select(ElectricalComponent).where(
                    col(ElectricalComponent.deleted_at).is_(None)
                )
            ).all()
        }
        for device in self._devices_for_distribution(distribution_id):
            contact = self._protective_contact(device)
            if contact is None:
                continue
            contacts[contact.key] = contact

        placements = self.session.exec(
            select(ElectricalAssetPlacement).where(
                ElectricalAssetPlacement.distribution_id == distribution_id,
                col(ElectricalAssetPlacement.deleted_at).is_(None),
            )
        ).all()
        for placement in placements:
            if placement.asset_id in component_asset_ids:
                continue
            asset = self.session.get(Asset, placement.asset_id)
            if asset is None or asset.deleted_at is not None or asset.status == "retired":
                continue
            contact = self._asset_contact(placement, asset)
            contacts[contact.key] = contact

        return sorted(
            contacts.values(),
            key=lambda contact: (
                contact.area_id is None,
                str(contact.area_id or ""),
                contact.row_number,
                contact.start_position,
                contact.target_kind,
                str(contact.target_id),
            ),
        )

    def _devices_for_distribution(
        self, distribution_id: UUID
    ) -> list[ElectricalProtectiveDevice]:
        try:
            projections = ElectricalProtectiveDeviceRepository(
                self.session
            ).for_distribution(distribution_id, include_deleted=False)
        except ValueError:
            projections = []
        records: dict[UUID, ElectricalProtectiveDevice] = {
            projection.record.id: projection.record for projection in projections
        }
        direct = self.session.exec(
            select(ElectricalProtectiveDevice).where(
                ElectricalProtectiveDevice.distribution_id == distribution_id,
            )
        ).all()
        for device in direct:
            if device.id in records:
                continue
            component = self.session.get(ElectricalComponent, device.id)
            if component is None or component.deleted_at is not None:
                continue
            asset = self.session.get(Asset, component.asset_id)
            if asset is None or asset.deleted_at is not None or asset.status == "retired":
                continue
            records[device.id] = device
        return sorted(
            (
                device
                for device in records.values()
                if device.row_number is not None
                and device.start_position is not None
                and self._device_module_width(device) is not None
            ),
            key=lambda device: (
                device.area_id is None,
                str(device.area_id or ""),
                device.row_number or 0,
                device.start_position or 0,
                str(device.id),
            ),
        )

    def _protective_contact(
        self,
        device: ElectricalProtectiveDevice,
    ) -> PhaseRailContact | None:
        if device.row_number is None or device.start_position is None:
            return None
        width = self._device_module_width(device)
        if width is None:
            return None
        component = self.session.get(ElectricalComponent, device.id)
        asset = self.session.get(Asset, component.asset_id) if component is not None else None
        return PhaseRailContact(
            target_kind="protective_device",
            target_id=device.id,
            distribution_id=device.distribution_id,
            area_id=device.area_id,
            row_number=device.row_number,
            start_position=device.start_position,
            module_width=width,
            device_type=device.device_type,
            poles=device.poles,
            display_name=asset.name if asset is not None else str(device.id),
        )

    @staticmethod
    def _asset_contact(
        placement: ElectricalAssetPlacement,
        asset: Asset,
    ) -> PhaseRailContact:
        return PhaseRailContact(
            target_kind="asset",
            target_id=placement.asset_id,
            distribution_id=placement.distribution_id,
            area_id=placement.area_id,
            row_number=placement.row_number,
            start_position=placement.start_position,
            module_width=placement.module_width,
            device_type="din_asset",
            poles=placement.module_width,
            display_name=asset.name,
        )

    def _verify_distribution_connections(
        self,
        distribution_id: UUID,
        desired_by_rail: dict[UUID, list[PhaseRailContact]],
    ) -> None:
        expected: dict[tuple[UUID, str, UUID], tuple[bool, bool, bool]] = {}
        for rail_id, contacts in desired_by_rail.items():
            rail = self.session.get(ElectricalCabinetComponent, rail_id)
            if rail is None or rail.deleted_at is not None:
                continue
            for contact in contacts:
                phases = self._contact_phases(rail, contact)
                selected = set(phases)
                expected[(rail_id, contact.target_kind, contact.target_id)] = (
                    ElectricalPhase.L1 in selected,
                    ElectricalPhase.L2 in selected,
                    ElectricalPhase.L3 in selected,
                )
        if not expected:
            return

        records = self.session.exec(
            select(ElectricalConnection).where(
                ElectricalConnection.source_kind == "cabinet_component",
                (
                    (ElectricalConnection.target_kind == "protective_device")
                    | (ElectricalConnection.target_kind == "asset")
                ),
                ElectricalConnection.connection_type == "busbar",
                col(ElectricalConnection.deleted_at).is_(None),
            )
        ).all()
        actual = {
            (record.source_id, record.target_kind, record.target_id): (
                bool(record.phase_l1),
                bool(record.phase_l2),
                bool(record.phase_l3),
            )
            for record in records
        }
        missing = set(expected) - set(actual)
        mismatched = {
            pair
            for pair, phases in expected.items()
            if pair in actual and actual[pair] != phases
        }
        if missing or mismatched:
            parts: list[str] = []
            if missing:
                parts.append(
                    "fehlend: "
                    + ", ".join(
                        f"{rail_id}->{kind}:{target_id}"
                        for rail_id, kind, target_id in sorted(
                            missing,
                            key=lambda pair: (str(pair[0]), pair[1], str(pair[2])),
                        )
                    )
                )
            if mismatched:
                parts.append(
                    "falsche Phase: "
                    + ", ".join(
                        f"{rail_id}->{kind}:{target_id}"
                        for rail_id, kind, target_id in sorted(
                            mismatched,
                            key=lambda pair: (str(pair[0]), pair[1], str(pair[2])),
                        )
                    )
                )
            raise RuntimeError(
                "Automatische Phasenschienen-Verbindungen sind nach dem Abgleich "
                f"in Verteilung {distribution_id} unvollständig ({'; '.join(parts)})"
            )

    @staticmethod
    def _same_context(
        rail: ElectricalCabinetComponent,
        contact: PhaseRailContact,
    ) -> bool:
        return (
            rail.distribution_id == contact.distribution_id
            and rail.area_id == contact.area_id
            and rail.row_number == contact.row_number
        )

    def _device_module_width(
        self,
        device: ElectricalProtectiveDevice,
    ) -> int | None:
        if device.module_width is not None:
            return device.module_width
        component = self.session.get(ElectricalComponent, device.id)
        if component is None or component.deleted_at is not None:
            return None
        asset = self.session.get(Asset, component.asset_id)
        if asset is None or asset.deleted_at is not None or asset.status == "retired":
            return None
        return effective_asset_module_width(self.session, asset)

    def _contact_phases(
        self,
        rail: ElectricalCabinetComponent,
        contact: PhaseRailContact,
    ) -> tuple[ElectricalPhase, ...]:
        if contact.target_kind == "protective_device":
            return phase_rail_device_phases(
                rail_start=rail.start_position,
                rail_width=rail.module_width,
                phase_l1=rail.phase_l1,
                phase_l2=rail.phase_l2,
                phase_l3=rail.phase_l3,
                start_phase=rail.start_phase,
                device_start=contact.start_position,
                device_width=contact.module_width,
                device_type=contact.device_type,
                poles=contact.poles,
            )
        return phase_rail_din_asset_phases(
            rail_start=rail.start_position,
            rail_width=rail.module_width,
            phase_l1=rail.phase_l1,
            phase_l2=rail.phase_l2,
            phase_l3=rail.phase_l3,
            start_phase=rail.start_phase,
            asset_start=contact.start_position,
            asset_width=contact.module_width,
        )

    @staticmethod
    def _set_phases(
        connection: ElectricalConnection,
        phases: tuple[ElectricalPhase, ...],
    ) -> bool:
        selected = set(phases)
        expected = (
            ElectricalPhase.L1 in selected,
            ElectricalPhase.L2 in selected,
            ElectricalPhase.L3 in selected,
        )
        current = (
            connection.phase_l1,
            connection.phase_l2,
            connection.phase_l3,
        )
        if current == expected:
            return False
        connection.phase_l1, connection.phase_l2, connection.phase_l3 = expected
        return True
