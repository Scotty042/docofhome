from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

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
from app.repositories.electrical_topology import (
    ElectricalConnectionRepository,
    ElectricalEndpointProjection,
    ElectricalEndpointRepository,
)
from app.schemas.asset_engine import Page
from app.schemas.electrical_topology import (
    ElectricalConnectionRead,
    ElectricalConnectionType,
    ElectricalConnectionWrite,
    ElectricalEndpointKind,
    ElectricalEndpointRead,
    ElectricalPhase,
    ElectricalPhaseSource,
    ElectricalTopologyNodeRead,
    ElectricalTopologyRead,
)
from app.services.din_width import effective_asset_module_width
from app.services.electrical import (
    ElectricalConflictError,
    ElectricalNotFoundError,
    ElectricalValidationError,
)
from app.services.phase_rail_connections import PhaseRailConnectionService


class ElectricalTopologyService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.connections = ElectricalConnectionRepository(session)
        self.endpoints = ElectricalEndpointRepository(session)

    def _reconcile_phase_rail_connections(self) -> None:
        """Self-heal derived phase-rail contacts before topology reads.

        Runtime writes already synchronize the affected distribution. This additional
        reconciliation makes upgrades and interrupted legacy transactions robust: as
        soon as the topology is opened, every active phase rail is matched against its
        physically covered DIN devices and missing contacts are recreated.
        """
        distribution_ids = list(
            self.session.exec(
                select(ElectricalCabinetComponent.distribution_id)
                .where(
                    ElectricalCabinetComponent.component_type == "phase_rail",
                    col(ElectricalCabinetComponent.deleted_at).is_(None),
                )
                .distinct()
            ).all()
        )
        if not distribution_ids:
            return
        try:
            synchronizer = PhaseRailConnectionService(self.session)
            for distribution_id in distribution_ids:
                synchronizer.sync_distribution(distribution_id)
            self.session.commit()
        except IntegrityError:
            # A second topology request may have created the same derived pair
            # concurrently. Retry once after rollback; the synchronizer then reuses
            # the already active connection instead of inserting a duplicate.
            self.session.rollback()
            try:
                synchronizer = PhaseRailConnectionService(self.session)
                for distribution_id in distribution_ids:
                    synchronizer.sync_distribution(distribution_id)
                self.session.commit()
            except IntegrityError as exc:
                self.session.rollback()
                raise ElectricalValidationError(
                    "Automatische Phasenschienen-Verbindungen konnten nicht abgeglichen werden"
                ) from exc

    def endpoint_page(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
    ) -> Page[ElectricalEndpointRead]:
        candidates = [
            item for item in self.endpoints.list()
            if item.kind != ElectricalEndpointKind.DISTRIBUTION
        ]
        normalized = search.strip().casefold() if search else ""
        if normalized:
            candidates = [
                item
                for item in candidates
                if any(
                    normalized in value.casefold()
                    for value in (
                        item.name,
                        item.code or "",
                        item.type_name,
                        item.location_name or "",
                    )
                )
            ]
        total = len(candidates)
        offset = (page - 1) * page_size
        reads: list[ElectricalEndpointRead] = []
        for item in candidates[offset : offset + page_size]:
            read = self._endpoint_read(item)
            if item.kind == ElectricalEndpointKind.CIRCUIT and not read.effective_phases:
                phase_sets = self._circuit_incoming_phase_sets(item.id)
                if len(phase_sets) == 1:
                    read.effective_phases = list(phase_sets[0])
            reads.append(read)
        return Page.create(reads, total, page, page_size)

    def list_connections(self) -> list[ElectricalConnectionRead]:
        self._reconcile_phase_rail_connections()
        return [self._connection_read(item) for item in self.connections.list()]

    def create(self, payload: ElectricalConnectionWrite) -> ElectricalConnectionRead:
        self._validate(payload)
        record = ElectricalConnection(**self._record_values(payload))
        self._apply_phase_source(record)
        self.connections.add(record)
        self._commit()
        return self._connection_read(record)

    def update(
        self,
        connection_id: UUID,
        payload: ElectricalConnectionWrite,
    ) -> ElectricalConnectionRead:
        record = self.connections.get(connection_id)
        if record is None:
            raise ElectricalNotFoundError
        existing_source = self.endpoints.resolve(
            ElectricalEndpointKind(record.source_kind), record.source_id
        )
        existing_target = self.endpoints.resolve(
            ElectricalEndpointKind(record.target_kind), record.target_id
        )
        if (
            existing_source is not None
            and existing_target is not None
            and self._is_direct_phase_rail_connection(existing_source, existing_target)
        ):
            raise ElectricalConflictError(
                "Diese Verbindung wird vollständig durch die Phasen-/Kammschiene "
                "verwaltet und kann nicht manuell bearbeitet werden. Ändere stattdessen "
                "die Schiene oder die Geräteplatzierung."
            )
        self._validate(payload, exclude_id=connection_id)
        record.sqlmodel_update(self._record_values(payload))
        self._apply_phase_source(record)
        record.updated_at = datetime.now(UTC)
        self._commit()
        return self._connection_read(record)

    def delete(self, connection_id: UUID) -> None:
        record = self.connections.get(connection_id)
        if record is None:
            raise ElectricalNotFoundError
        source = self.endpoints.resolve(
            ElectricalEndpointKind(record.source_kind), record.source_id
        )
        target = self.endpoints.resolve(
            ElectricalEndpointKind(record.target_kind), record.target_id
        )
        if (
            source is not None
            and target is not None
            and self._is_direct_phase_rail_connection(source, target)
        ):
            raise ElectricalConflictError(
                "Die Verbindung wird automatisch durch die Phasen-/Kammschiene verwaltet. "
                "Verschiebe das DIN-Gerät oder ändere den Schienenbereich."
            )
        from app.services.smart_meter import SmartMeterMeasurementService

        if SmartMeterMeasurementService(self.session).active_for_connection(connection_id):
            raise ElectricalConflictError(
                "Die Verkabelung wird von mindestens einem Smart-Meter-Messpunkt verwendet"
            )
        self._validate_cabinet_phase_flow(None, exclude_id=connection_id)
        now = datetime.now(UTC)
        record.deleted_at = now
        record.updated_at = now
        self._commit()

    def topology(self) -> ElectricalTopologyRead:
        self._reconcile_phase_rail_connections()
        connection_records = self.connections.list()
        connection_reads = [self._connection_read(item) for item in connection_records]
        self._append_cabinet_supply_warnings(connection_reads)
        endpoints: dict[str, ElectricalEndpointRead] = {}
        incoming: dict[str, list[ElectricalConnectionRead]] = {}
        outgoing: dict[str, list[ElectricalConnectionRead]] = {}
        for connection in connection_reads:
            endpoints[connection.source.key] = connection.source
            endpoints[connection.target.key] = connection.target
            incoming.setdefault(connection.target.key, []).append(connection)
            outgoing.setdefault(connection.source.key, []).append(connection)

        def descendant_keys(start_key: str) -> set[str]:
            result: set[str] = set()
            pending = [start_key]
            while pending:
                current = pending.pop()
                for connection in outgoing.get(current, []):
                    target_key = connection.target.key
                    if target_key not in result:
                        result.add(target_key)
                        pending.append(target_key)
            result.discard(start_key)
            return result

        def source_endpoints(endpoint_key: str, visited: set[str] | None = None) -> set[str]:
            visited = set() if visited is None else set(visited)
            if endpoint_key in visited:
                raise ElectricalValidationError("Stored electrical topology contains a cycle")
            visited.add(endpoint_key)
            parent_connections = incoming.get(endpoint_key, [])
            if not parent_connections:
                return {endpoint_key}
            result: set[str] = set()
            for parent_connection in parent_connections:
                result.update(source_endpoints(parent_connection.source.key, visited))
            return result

        nodes: list[ElectricalTopologyNodeRead] = []
        for key, endpoint in endpoints.items():
            descendants = [endpoints[item] for item in descendant_keys(key)]
            incoming_connections = incoming.get(key, [])
            source_names = sorted(
                {endpoints[source_key].name for source_key in source_endpoints(key)},
                key=str.casefold,
            )
            incoming_phases = sorted(
                {
                    phase
                    for connection in incoming_connections
                    for phase in connection.effective_phases
                },
                key=list(ElectricalPhase).index,
            )
            nodes.append(
                ElectricalTopologyNodeRead(
                    endpoint=endpoint,
                    source_names=source_names,
                    incoming_phases=incoming_phases,
                    downstream_protective_device_count=sum(
                        item.kind == ElectricalEndpointKind.PROTECTIVE_DEVICE
                        and item.device_type in {"fuse", "mcb", "rcbo"}
                        for item in descendants
                    ),
                    downstream_circuit_count=sum(
                        item.kind == ElectricalEndpointKind.CIRCUIT for item in descendants
                    ),
                    downstream_asset_count=sum(
                        item.kind == ElectricalEndpointKind.ASSET for item in descendants
                    ),
                )
            )
        nodes.sort(
            key=lambda item: (
                item.source_names[0].casefold(),
                item.endpoint.name.casefold(),
                item.endpoint.key,
            )
        )
        from app.services.smart_meter import SmartMeterMeasurementService

        return ElectricalTopologyRead(
            nodes=nodes,
            connections=connection_reads,
            measurement_points=SmartMeterMeasurementService(self.session).list_all_active(),
        )

    @staticmethod
    def _append_cabinet_supply_warnings(
        connections: list[ElectricalConnectionRead],
    ) -> None:
        incoming: dict[str, list[ElectricalConnectionRead]] = {}
        for connection in connections:
            incoming.setdefault(connection.target.key, []).append(connection)
        for connection in connections:
            source = connection.source
            if source.kind != ElectricalEndpointKind.CABINET_COMPONENT:
                continue
            supply_connections = incoming.get(source.key, [])
            if not supply_connections:
                if source.device_type == "phase_rail":
                    connection.phase_warnings.append(
                        "Für diese Phasen-/Kammschiene ist noch keine vorgelagerte "
                        "Einspeisung dokumentiert."
                    )
                continue
            supplied = {
                phase
                for supply in supply_connections
                for phase in supply.effective_phases
            }
            missing = [
                phase for phase in connection.effective_phases if phase not in supplied
            ]
            if missing:
                connection.phase_warnings.append(
                    f"{source.name} gibt {', '.join(item.value for item in missing)} aus, "
                    "obwohl diese Leiter in der dokumentierten Einspeisung fehlen."
                )

    def _validate(
        self,
        payload: ElectricalConnectionWrite,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        if ElectricalEndpointKind.DISTRIBUTION in {
            payload.source_kind,
            payload.target_kind,
        }:
            raise ElectricalValidationError(
                "Verteilungen sind strukturelle Behälter. Verkabelungen werden an ihren "
                "Einbaugeräten und Klemmen dokumentiert."
            )
        if payload.target_kind == ElectricalEndpointKind.GRID_CONNECTION:
            raise ElectricalValidationError(
                "Der Netzanschluss kann nur als Quelle verwendet werden"
            )
        source = self.endpoints.resolve(payload.source_kind, payload.source_id)
        target = self.endpoints.resolve(payload.target_kind, payload.target_id)
        if source is None:
            raise ElectricalValidationError("Source does not exist or is archived")
        if target is None:
            raise ElectricalValidationError("Target does not exist or is archived")
        if (
            source.kind == ElectricalEndpointKind.CABINET_COMPONENT
            and source.device_type == "phase_rail"
        ):
            raise ElectricalValidationError(
                "Ausgänge einer Phasen-/Kammschiene zu DIN-Geräten werden aus der "
                "Schienen- und Geräteplatzierung automatisch erzeugt."
            )
        restricted_phases = self._restricted_conductor_phases(source, target)
        if restricted_phases is not None:
            if not restricted_phases:
                raise ElectricalValidationError(
                    "N- und PE-Schienen können nicht direkt miteinander verbunden werden."
                )
            order = {phase: index for index, phase in enumerate(ElectricalPhase)}
            payload.phases = sorted(restricted_phases, key=order.__getitem__)
        target_phase_source = self._active_physical_phase_source(
            target, exclude_connection_id=exclude_id
        )
        if (
            restricted_phases is None
            and target_phase_source
            and target_phase_source[1] == ElectricalPhaseSource.BUSBAR
        ):
            raise ElectricalValidationError(
                f"{target.name} wird bereits physisch durch eine Phasen-/Kammschiene "
                "versorgt. Eine zusätzliche manuelle Einspeisung ist nicht zulässig."
            )
        self._enforce_protective_device_line_phases(
            payload, source, target, exclude_connection_id=exclude_id
        )
        self._validate_endpoint_phases(payload, source, target, exclude_connection_id=exclude_id)
        source_key = source.key
        target_key = target.key
        outgoing: dict[str, list[str]] = {}
        for connection in self.connections.list():
            if connection.id == exclude_id:
                continue
            existing_source = f"{connection.source_kind}:{connection.source_id}"
            existing_target = f"{connection.target_kind}:{connection.target_id}"
            outgoing.setdefault(existing_source, []).append(existing_target)
        pending = [target_key]
        visited: set[str] = set()
        while pending:
            current = pending.pop()
            if current == source_key:
                raise ElectricalConflictError(
                    "Connection would create a cycle in the supply topology"
                )
            if current in visited:
                continue
            visited.add(current)
            pending.extend(outgoing.get(current, []))
        self._validate_cabinet_phase_flow(payload, exclude_id=exclude_id)

    @staticmethod
    def _endpoint_restricted_conductors(
        endpoint: ElectricalEndpointProjection,
    ) -> set[ElectricalPhase] | None:
        if endpoint.kind != ElectricalEndpointKind.CABINET_COMPONENT:
            return None
        if endpoint.device_type == "neutral_rail":
            return {ElectricalPhase.N}
        if endpoint.device_type == "protective_earth_rail":
            return {ElectricalPhase.PE}
        return None

    @classmethod
    def _restricted_conductor_phases(
        cls,
        source: ElectricalEndpointProjection,
        target: ElectricalEndpointProjection,
    ) -> set[ElectricalPhase] | None:
        restrictions = [
            restriction
            for endpoint in (source, target)
            if (restriction := cls._endpoint_restricted_conductors(endpoint)) is not None
        ]
        if not restrictions:
            return None
        allowed = set(restrictions[0])
        for restriction in restrictions[1:]:
            allowed.intersection_update(restriction)
        return allowed

    def _phase_rail_phases_for_device(
        self,
        device_id: UUID,
    ) -> tuple[ElectricalPhase, ...]:
        device = self.session.get(ElectricalProtectiveDevice, device_id)
        if device is None:
            return ()
        device_component = self.session.get(ElectricalComponent, device.id)
        if device_component is None or device_component.deleted_at is not None:
            return ()
        if device.row_number is None or device.start_position is None:
            return ()
        device_width = device.module_width
        if device_width is None:
            asset = self.session.get(Asset, device_component.asset_id)
            if asset is None or asset.deleted_at is not None or asset.status == "retired":
                return ()
            device_width = effective_asset_module_width(self.session, asset)
        if device_width is None:
            return ()

        rails = list(
            self.session.exec(
                select(ElectricalCabinetComponent).where(
                    ElectricalCabinetComponent.distribution_id == device.distribution_id,
                    ElectricalCabinetComponent.area_id == device.area_id,
                    ElectricalCabinetComponent.row_number == device.row_number,
                    ElectricalCabinetComponent.component_type == "phase_rail",
                    col(ElectricalCabinetComponent.deleted_at).is_(None),
                )
            ).all()
        )
        rails = [
            rail
            for rail in rails
            if rail_fully_covers_device(
                rail_start=rail.start_position,
                rail_width=rail.module_width,
                device_start=device.start_position,
                device_width=device_width,
            )
        ]
        rails.sort(
            key=lambda rail: (
                rail.module_width,
                rail.start_position,
                rail.name.casefold(),
                str(rail.id),
            )
        )
        if not rails:
            return ()
        rail = rails[0]
        return phase_rail_device_phases(
            rail_start=rail.start_position,
            rail_width=rail.module_width,
            phase_l1=rail.phase_l1,
            phase_l2=rail.phase_l2,
            phase_l3=rail.phase_l3,
            start_phase=rail.start_phase,
            device_start=device.start_position,
            device_width=device_width,
            device_type=device.device_type,
            poles=device.poles,
        )

    def _phase_rail_phases_for_asset(
        self,
        asset_id: UUID,
    ) -> tuple[ElectricalPhase, ...]:
        placement = self.session.exec(
            select(ElectricalAssetPlacement).where(
                ElectricalAssetPlacement.asset_id == asset_id,
                col(ElectricalAssetPlacement.deleted_at).is_(None),
            )
        ).first()
        if placement is None:
            return ()
        asset = self.session.get(Asset, asset_id)
        if asset is None or asset.deleted_at is not None or asset.status == "retired":
            return ()
        rails = list(
            self.session.exec(
                select(ElectricalCabinetComponent).where(
                    ElectricalCabinetComponent.distribution_id == placement.distribution_id,
                    ElectricalCabinetComponent.area_id == placement.area_id,
                    ElectricalCabinetComponent.row_number == placement.row_number,
                    ElectricalCabinetComponent.component_type == "phase_rail",
                    col(ElectricalCabinetComponent.deleted_at).is_(None),
                )
            ).all()
        )
        rails = [
            rail
            for rail in rails
            if rail_fully_covers_device(
                rail_start=rail.start_position,
                rail_width=rail.module_width,
                device_start=placement.start_position,
                device_width=placement.module_width,
            )
        ]
        rails.sort(
            key=lambda rail: (
                rail.module_width,
                rail.start_position,
                rail.name.casefold(),
                str(rail.id),
            )
        )
        if not rails:
            return ()
        rail = rails[0]
        return phase_rail_din_asset_phases(
            rail_start=rail.start_position,
            rail_width=rail.module_width,
            phase_l1=rail.phase_l1,
            phase_l2=rail.phase_l2,
            phase_l3=rail.phase_l3,
            start_phase=rail.start_phase,
            asset_start=placement.start_position,
            asset_width=placement.module_width,
        )

    def _active_physical_phase_source(
        self,
        endpoint: ElectricalEndpointProjection,
        *,
        exclude_connection_id: UUID | None = None,
    ) -> tuple[tuple[ElectricalPhase, ...], ElectricalPhaseSource, UUID] | None:
        if endpoint.kind not in {
            ElectricalEndpointKind.PROTECTIVE_DEVICE,
            ElectricalEndpointKind.ASSET,
        }:
            return None
        records = list(
            self.session.exec(
                select(ElectricalConnection).where(
                    ElectricalConnection.target_kind == endpoint.kind.value,
                    ElectricalConnection.target_id == endpoint.id,
                    col(ElectricalConnection.deleted_at).is_(None),
                )
            ).all()
        )
        line_order = [ElectricalPhase.L1, ElectricalPhase.L2, ElectricalPhase.L3]
        candidates: list[tuple[int, tuple[ElectricalPhase, ...], ElectricalPhaseSource, UUID]] = []
        for record in records:
            if record.id == exclude_connection_id:
                continue
            phases = tuple(phase for phase in line_order if phase in self._phases(record))
            if not phases:
                continue
            if record.connection_type == ElectricalConnectionType.BUSBAR.value:
                rail = (
                    self.session.get(ElectricalCabinetComponent, record.source_id)
                    if record.source_kind == ElectricalEndpointKind.CABINET_COMPONENT.value
                    else None
                )
                if rail is not None and rail.deleted_at is None and rail.component_type == "phase_rail":
                    candidates.append((0, phases, ElectricalPhaseSource.BUSBAR, record.id))
            elif record.connection_type in {
                ElectricalConnectionType.WIRE.value,
                ElectricalConnectionType.CABLE.value,
            }:
                candidates.append((1, phases, ElectricalPhaseSource.WIRE, record.id))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], str(item[3])))
        _, phases, source, connection_id = candidates[0]
        return phases, source, connection_id

    def _phase_source_for_record(
        self,
        record: ElectricalConnection,
        source: ElectricalEndpointProjection,
        target: ElectricalEndpointProjection,
    ) -> tuple[ElectricalPhaseSource, UUID | None]:
        if self._is_auxiliary_conductor_only(self._phases(record)):
            # N and PE are independent conductors. A separate neutral/protective-earth
            # wire must not inherit the L1/L2/L3 source of another incoming connection.
            return ElectricalPhaseSource.MANUAL, None
        if self._restricted_conductor_phases(source, target) is not None:
            return ElectricalPhaseSource.MANUAL, None
        # A real phase rail always has priority. This also repairs the displayed
        # source for older inconsistent records that still contain a parallel wire.
        if self._is_direct_phase_rail_connection(source, target):
            return ElectricalPhaseSource.BUSBAR, record.id
        target_physical = self._active_physical_phase_source(target)
        if target_physical is not None:
            return target_physical[1], target_physical[2]
        if (
            target.kind in {ElectricalEndpointKind.PROTECTIVE_DEVICE, ElectricalEndpointKind.ASSET}
            and record.connection_type in {
                ElectricalConnectionType.WIRE.value,
                ElectricalConnectionType.CABLE.value,
            }
        ):
            return ElectricalPhaseSource.WIRE, record.id
        source_physical = self._active_physical_phase_source(
            source, exclude_connection_id=record.id
        )
        if source_physical is not None:
            return source_physical[1], source_physical[2]
        return ElectricalPhaseSource.MANUAL, None

    def _apply_phase_source(self, record: ElectricalConnection) -> None:
        source = self.endpoints.resolve(
            ElectricalEndpointKind(record.source_kind), record.source_id
        )
        target = self.endpoints.resolve(
            ElectricalEndpointKind(record.target_kind), record.target_id
        )
        if source is None or target is None:
            record.phase_source = ElectricalPhaseSource.MANUAL.value
            record.source_connection_id = None
            return
        phase_source, source_connection_id = self._phase_source_for_record(record, source, target)
        record.phase_source = phase_source.value
        record.source_connection_id = source_connection_id

    def _direct_phase_rail_requirement(
        self,
        source: ElectricalEndpointProjection,
        target: ElectricalEndpointProjection,
    ) -> tuple[ElectricalPhase, ...]:
        if (
            source.kind != ElectricalEndpointKind.CABINET_COMPONENT
            or source.device_type != "phase_rail"
        ):
            return ()
        if target.kind == ElectricalEndpointKind.PROTECTIVE_DEVICE:
            return self._phase_rail_phases_for_device(target.id)
        if target.kind == ElectricalEndpointKind.ASSET:
            return self._phase_rail_phases_for_asset(target.id)
        return ()

    def _circuit_incoming_phase_sets(
        self,
        circuit_id: UUID,
        *,
        exclude_connection_id: UUID | None = None,
    ) -> list[tuple[ElectricalPhase, ...]]:
        line_order = [ElectricalPhase.L1, ElectricalPhase.L2, ElectricalPhase.L3]
        records = self.session.exec(
            select(ElectricalConnection).where(
                ElectricalConnection.target_kind == "circuit",
                ElectricalConnection.target_id == circuit_id,
                col(ElectricalConnection.deleted_at).is_(None),
            )
        ).all()
        phase_sets: list[tuple[ElectricalPhase, ...]] = []
        for record in records:
            if record.id == exclude_connection_id:
                continue
            phases = tuple(phase for phase in line_order if phase in self._phases(record))
            if phases and phases not in phase_sets:
                phase_sets.append(phases)
        return phase_sets

    def _connection_phase_requirements(
        self,
        source: ElectricalEndpointProjection,
        target: ElectricalEndpointProjection,
        *,
        exclude_connection_id: UUID | None = None,
    ) -> list[tuple[ElectricalPhase, ...]]:
        requirements: list[tuple[ElectricalPhase, ...]] = []
        line_phases = {ElectricalPhase.L1, ElectricalPhase.L2, ElectricalPhase.L3}
        direct_requirement = self._direct_phase_rail_requirement(source, target)
        if direct_requirement:
            requirements.append(direct_requirement)
        for endpoint in (source, target):
            if endpoint.kind not in {
                ElectricalEndpointKind.PROTECTIVE_DEVICE,
                ElectricalEndpointKind.ASSET,
                ElectricalEndpointKind.CIRCUIT,
            }:
                continue
            physical = self._active_physical_phase_source(
                endpoint, exclude_connection_id=exclude_connection_id
            )
            required = physical[0] if physical is not None else ()
            if (
                not required
                and endpoint.kind not in {
                    ElectricalEndpointKind.PROTECTIVE_DEVICE,
                    ElectricalEndpointKind.ASSET,
                }
                and endpoint.effective_phases is not None
            ):
                required = tuple(
                    phase
                    for phase in endpoint.effective_phases
                    if phase in line_phases
                )
            if required and required not in requirements:
                requirements.append(required)
            if endpoint.kind == ElectricalEndpointKind.CIRCUIT and not required:
                for circuit_requirement in self._circuit_incoming_phase_sets(
                    endpoint.id, exclude_connection_id=exclude_connection_id
                ):
                    if circuit_requirement not in requirements:
                        requirements.append(circuit_requirement)
        return requirements

    @staticmethod
    def _is_auxiliary_conductor_only(phases: list[ElectricalPhase]) -> bool:
        """Return true for an explicit N/PE-only connection.

        Such a connection is one physical conductor path and must not be expanded with
        line phases merely because the same target receives L1/L2/L3 through another
        wire, cable, distribution block or phase rail.
        """
        line_phases = {ElectricalPhase.L1, ElectricalPhase.L2, ElectricalPhase.L3}
        return bool(phases) and not any(phase in line_phases for phase in phases)

    @staticmethod
    def _is_direct_phase_rail_connection(
        source: ElectricalEndpointProjection,
        target: ElectricalEndpointProjection,
    ) -> bool:
        return (
            source.kind == ElectricalEndpointKind.CABINET_COMPONENT
            and source.device_type == "phase_rail"
            and target.kind in {
                ElectricalEndpointKind.PROTECTIVE_DEVICE,
                ElectricalEndpointKind.ASSET,
            }
        )

    def _enforce_protective_device_line_phases(
        self,
        payload: ElectricalConnectionWrite,
        source: ElectricalEndpointProjection,
        target: ElectricalEndpointProjection,
        *,
        exclude_connection_id: UUID | None = None,
    ) -> None:
        """Force the line phase derived from a rail onto line-carrying wiring.

        Explicit N/PE-only paths remain independent. Existing contradictory line-phase
        records are still normalized on save instead of accepting a manual override.
        """
        if self._restricted_conductor_phases(source, target) is not None:
            return
        if self._is_auxiliary_conductor_only(payload.phases):
            return
        line_phases = {ElectricalPhase.L1, ElectricalPhase.L2, ElectricalPhase.L3}
        requirements = self._connection_phase_requirements(
            source, target, exclude_connection_id=exclude_connection_id
        )
        if not requirements:
            return
        required = requirements[0]
        if any(candidate != required for candidate in requirements[1:]):
            details = " / ".join(
                ", ".join(phase.value for phase in candidate)
                for candidate in requirements
            )
            raise ElectricalValidationError(
                "Die beteiligten Schutzgeräte haben widersprüchliche wirksame Phasen: "
                f"{details}"
            )
        preserved = (
            []
            if self._is_direct_phase_rail_connection(source, target)
            else [phase for phase in payload.phases if phase not in line_phases]
        )
        order = {phase: index for index, phase in enumerate(ElectricalPhase)}
        payload.phases = sorted(set(required).union(preserved), key=order.__getitem__)

    def _validate_endpoint_phases(
        self,
        payload: ElectricalConnectionWrite,
        source: ElectricalEndpointProjection,
        target: ElectricalEndpointProjection,
        *,
        exclude_connection_id: UUID | None = None,
    ) -> None:
        if self._restricted_conductor_phases(source, target) is not None:
            return
        if self._is_auxiliary_conductor_only(payload.phases):
            return
        line_phases = {ElectricalPhase.L1, ElectricalPhase.L2, ElectricalPhase.L3}
        selected = set(payload.phases) & line_phases
        for endpoint, role in ((source, "Quelle"), (target, "Ziel")):
            physical = self._active_physical_phase_source(
                endpoint, exclude_connection_id=exclude_connection_id
            )
            endpoint_phases = (
                list(physical[0])
                if physical is not None
                else endpoint.effective_phases
                if endpoint.kind not in {
                    ElectricalEndpointKind.PROTECTIVE_DEVICE,
                    ElectricalEndpointKind.ASSET,
                }
                else None
            )
            if endpoint_phases is None:
                continue
            allowed = set(endpoint_phases) & line_phases
            if not allowed:
                continue
            invalid = selected - allowed
            if invalid:
                names = ", ".join(sorted(item.value for item in invalid))
                expected = ", ".join(
                    item.value for item in endpoint_phases if item in line_phases
                )
                raise ElectricalValidationError(
                    f"{role} {endpoint.name} akzeptiert nicht {names}; "
                    f"wirksame Phase: {expected}"
                )
            if endpoint.kind in {
                ElectricalEndpointKind.PROTECTIVE_DEVICE,
                ElectricalEndpointKind.CIRCUIT,
            } and selected != allowed:
                expected = ", ".join(
                    item.value for item in endpoint_phases if item in line_phases
                )
                role_name = (
                    "Schutzgerät" if endpoint.kind == ElectricalEndpointKind.PROTECTIVE_DEVICE
                    else "Stromkreis"
                )
                raise ElectricalValidationError(
                    f"Die Verbindung am {role_name} {endpoint.name} muss exakt "
                    f"{expected} verwenden"
                )

    def _validate_cabinet_phase_flow(
        self,
        payload: ElectricalConnectionWrite | None,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        affected: set[UUID] = set()
        if payload is not None:
            if payload.source_kind == ElectricalEndpointKind.CABINET_COMPONENT:
                affected.add(payload.source_id)
            if payload.target_kind == ElectricalEndpointKind.CABINET_COMPONENT:
                affected.add(payload.target_id)
            if affected and not payload.phases:
                raise ElectricalValidationError(
                    "Für Verbindungen an Schrankkomponenten müssen die Leiter angegeben werden"
                )
        if exclude_id is not None:
            previous = self.connections.get(exclude_id)
            if previous is not None:
                if previous.source_kind == ElectricalEndpointKind.CABINET_COMPONENT.value:
                    affected.add(previous.source_id)
                if previous.target_kind == ElectricalEndpointKind.CABINET_COMPONENT.value:
                    affected.add(previous.target_id)
        if not affected:
            return

        edges: list[tuple[str, UUID, str, UUID, set[ElectricalPhase]]] = []
        for record in self.connections.list():
            if record.id == exclude_id:
                continue
            edges.append(
                (
                    record.source_kind,
                    record.source_id,
                    record.target_kind,
                    record.target_id,
                    self._effective_record_phases(record),
                )
            )
        if payload is not None:
            edges.append(
                (
                    payload.source_kind.value,
                    payload.source_id,
                    payload.target_kind.value,
                    payload.target_id,
                    set(payload.phases),
                )
            )

        phase_order = {phase: index for index, phase in enumerate(ElectricalPhase)}
        for component_id in affected:
            component = self.session.get(ElectricalCabinetComponent, component_id)
            if component is None or component.deleted_at is not None:
                raise ElectricalValidationError(
                    "Die Schrankkomponente ist nicht mehr verfügbar"
                )
            configured = {
                phase
                for phase, enabled in (
                    (ElectricalPhase.L1, component.phase_l1),
                    (ElectricalPhase.L2, component.phase_l2),
                    (ElectricalPhase.L3, component.phase_l3),
                    (ElectricalPhase.N, component.neutral),
                    (ElectricalPhase.PE, component.protective_earth),
                )
                if enabled
            }
            incoming: set[ElectricalPhase] = set()
            outgoing: set[ElectricalPhase] = set()
            for source_kind, source_id, target_kind, target_id, phases in edges:
                if (
                    target_kind == ElectricalEndpointKind.CABINET_COMPONENT.value
                    and target_id == component_id
                ):
                    incoming.update(phases)
                    if configured and not phases.issubset(configured):
                        invalid = sorted(phases - configured, key=phase_order.__getitem__)
                        invalid_names = ", ".join(item.value for item in invalid)
                        raise ElectricalValidationError(
                            f"{component.name} unterstützt die Leiter "
                            f"{invalid_names} nicht"
                        )
                if (
                    source_kind == ElectricalEndpointKind.CABINET_COMPONENT.value
                    and source_id == component_id
                ):
                    outgoing.update(phases)
                    if configured and not phases.issubset(configured):
                        invalid = sorted(phases - configured, key=phase_order.__getitem__)
                        invalid_names = ", ".join(item.value for item in invalid)
                        raise ElectricalValidationError(
                            f"{component.name} unterstützt die Leiter "
                            f"{invalid_names} nicht"
                        )
            missing = outgoing - incoming
            if missing:
                ordered = sorted(missing, key=phase_order.__getitem__)
                missing_names = ", ".join(item.value for item in ordered)
                raise ElectricalValidationError(
                    f"{component.name} kann {missing_names} nicht ausgeben, "
                    "weil diese Leiter nicht eingespeist werden"
                )

    def _effective_record_phases(
        self,
        record: ElectricalConnection,
    ) -> set[ElectricalPhase]:
        source = self.endpoints.resolve(
            ElectricalEndpointKind(record.source_kind),
            record.source_id,
            include_deleted=True,
        )
        target = self.endpoints.resolve(
            ElectricalEndpointKind(record.target_kind),
            record.target_id,
            include_deleted=True,
        )
        stored = self._phases(record)
        if source is None or target is None:
            return set(stored)
        effective, _ = self._effective_connection_phases(source, target, stored)
        return set(effective)

    def _connection_read(
        self,
        record: ElectricalConnection,
    ) -> ElectricalConnectionRead:
        source = self.endpoints.resolve(
            ElectricalEndpointKind(record.source_kind),
            record.source_id,
            include_deleted=True,
        )
        target = self.endpoints.resolve(
            ElectricalEndpointKind(record.target_kind),
            record.target_id,
            include_deleted=True,
        )
        if source is None or target is None:
            raise ElectricalValidationError(
                "Stored electrical connection references a missing endpoint"
            )
        stored_phases = self._phases(record)
        effective_phases, warnings = self._effective_connection_phases(
            source, target, stored_phases, exclude_connection_id=record.id
        )
        restricted_phases = self._restricted_conductor_phases(source, target)
        line_phase_relevant = not self._is_auxiliary_conductor_only(stored_phases)
        requirements = (
            self._connection_phase_requirements(
                source, target, exclude_connection_id=record.id
            )
            if line_phase_relevant
            else []
        )
        locked_line_phases = [] if restricted_phases is not None else (
            list(requirements[0])
            if requirements and all(item == requirements[0] for item in requirements)
            else []
        )
        phase_source, source_connection_id = self._phase_source_for_record(
            record, source, target
        )
        return ElectricalConnectionRead(
            id=record.id,
            source=self._endpoint_read(source),
            target=self._endpoint_read(target),
            connection_type=ElectricalConnectionType(record.connection_type),
            label=record.label,
            phases=stored_phases,
            effective_phases=effective_phases,
            phase_locked=bool(locked_line_phases),
            phase_source=phase_source,
            source_connection_id=source_connection_id,
            locked_line_phases=locked_line_phases,
            phase_warnings=warnings,
            cable_type=record.cable_type,
            cores=record.cores,
            cross_section_mm2=record.cross_section_mm2,
            length_m=record.length_m,
            route=record.route,
            notes=record.notes,
            created_at=record.created_at,
            updated_at=record.updated_at,
            deleted_at=record.deleted_at,
        )

    @staticmethod
    def _endpoint_read(
        endpoint: ElectricalEndpointProjection,
    ) -> ElectricalEndpointRead:
        return ElectricalEndpointRead(
            key=endpoint.key,
            kind=endpoint.kind,
            id=endpoint.id,
            name=endpoint.name,
            code=endpoint.code,
            type_name=endpoint.type_name,
            location_name=endpoint.location_name,
            device_type=endpoint.device_type,
            effective_phases=(
                list(endpoint.effective_phases)
                if endpoint.effective_phases is not None
                else None
            ),
            deleted_at=endpoint.deleted_at,
        )

    def _effective_connection_phases(
        self,
        source: ElectricalEndpointProjection,
        target: ElectricalEndpointProjection,
        stored: list[ElectricalPhase],
        *,
        exclude_connection_id: UUID | None = None,
    ) -> tuple[list[ElectricalPhase], list[str]]:
        line_phases = {
            ElectricalPhase.L1,
            ElectricalPhase.L2,
            ElectricalPhase.L3,
        }
        restricted_phases = self._restricted_conductor_phases(source, target)
        if restricted_phases is not None:
            order = {phase: index for index, phase in enumerate(ElectricalPhase)}
            effective = sorted(restricted_phases, key=order.__getitem__)
            warnings: list[str] = []
            if effective != stored:
                stored_names = ", ".join(item.value for item in stored) or "keine"
                effective_names = ", ".join(item.value for item in effective) or "keine"
                warnings.append(
                    "Gespeicherte Verbindung enthält für die ausgewählte N-/PE-Schiene "
                    f"abweichende Leiter: {stored_names}. Wirksam: {effective_names}."
                )
            return effective, warnings
        if self._is_auxiliary_conductor_only(stored):
            # The effective conductors of one connection are exactly the conductors on
            # that connection. L1/L2/L3 supplied to the same target on parallel paths
            # belong to the target's aggregate supply, not to this N/PE-only path.
            order = {phase: index for index, phase in enumerate(ElectricalPhase)}
            return sorted(set(stored), key=order.__getitem__), []
        requirements = self._connection_phase_requirements(
            source, target, exclude_connection_id=exclude_connection_id
        )

        if requirements and all(item == requirements[0] for item in requirements):
            preserved = (
                []
                if self._is_direct_phase_rail_connection(source, target)
                else [phase for phase in stored if phase not in line_phases]
            )
            effective_set = set(requirements[0]).union(preserved)
        else:
            effective_set = set(stored)
            for endpoint in (source, target):
                if endpoint.effective_phases is None:
                    continue
                allowed_lines = set(endpoint.effective_phases) & line_phases
                if allowed_lines:
                    effective_set -= line_phases - allowed_lines

        order = {phase: index for index, phase in enumerate(ElectricalPhase)}
        effective = sorted(effective_set, key=order.__getitem__)
        warnings: list[str] = []
        if effective != stored:
            stored_names = ", ".join(item.value for item in stored) or "keine"
            effective_names = ", ".join(item.value for item in effective) or "keine"
            warnings.append(
                "Gespeicherte Verbindung enthält abweichende Phasen: "
                f"{stored_names}. Wirksam: {effective_names}."
            )
        return effective, warnings

    @staticmethod
    def _record_values(payload: ElectricalConnectionWrite) -> dict[str, object]:
        phases = set(payload.phases)
        return {
            "source_kind": payload.source_kind.value,
            "source_id": payload.source_id,
            "target_kind": payload.target_kind.value,
            "target_id": payload.target_id,
            "connection_type": payload.connection_type.value,
            "label": payload.label,
            "phase_l1": ElectricalPhase.L1 in phases,
            "phase_l2": ElectricalPhase.L2 in phases,
            "phase_l3": ElectricalPhase.L3 in phases,
            "neutral": ElectricalPhase.N in phases,
            "protective_earth": ElectricalPhase.PE in phases,
            "cable_type": payload.cable_type,
            "cores": payload.cores,
            "cross_section_mm2": payload.cross_section_mm2,
            "length_m": payload.length_m,
            "route": payload.route,
            "notes": payload.notes,
        }

    @staticmethod
    def _phases(record: ElectricalConnection) -> list[ElectricalPhase]:
        return [
            phase
            for phase, selected in (
                (ElectricalPhase.L1, record.phase_l1),
                (ElectricalPhase.L2, record.phase_l2),
                (ElectricalPhase.L3, record.phase_l3),
                (ElectricalPhase.N, record.neutral),
                (ElectricalPhase.PE, record.protective_earth),
            )
            if selected
        ]

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            database_message = str(getattr(exc, "orig", exc))
            if (
                "uq_electrical_connections_active_pair" in database_message
                or (
                    "electrical_connections.source_kind" in database_message
                    and "electrical_connections.source_id" in database_message
                    and "electrical_connections.target_kind" in database_message
                    and "electrical_connections.target_id" in database_message
                )
            ):
                message = "Diese Versorgungsverbindung ist bereits vorhanden"
            elif (
                "uq_electrical_connections_active_target" in database_message
                or (
                    "electrical_connections.target_kind" in database_message
                    and "electrical_connections.target_id" in database_message
                )
            ):
                message = (
                    "Die Datenbank enthält noch die alte Beschränkung auf eine "
                    "Einspeisung je Ziel. Bitte Migration 0033 ausführen."
                )
            else:
                message = "Versorgungsverbindung kollidiert mit vorhandenen Daten"
            raise ElectricalConflictError(message) from exc
