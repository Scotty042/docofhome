from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.models.electrical import ElectricalCabinetComponent
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
    ElectricalTopologyNodeRead,
    ElectricalTopologyRead,
)
from app.services.electrical import (
    ElectricalConflictError,
    ElectricalNotFoundError,
    ElectricalValidationError,
)


class ElectricalTopologyService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.connections = ElectricalConnectionRepository(session)
        self.endpoints = ElectricalEndpointRepository(session)

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
        return Page.create(
            [self._endpoint_read(item) for item in candidates[offset : offset + page_size]],
            total,
            page,
            page_size,
        )

    def list_connections(self) -> list[ElectricalConnectionRead]:
        return [self._connection_read(item) for item in self.connections.list()]

    def create(self, payload: ElectricalConnectionWrite) -> ElectricalConnectionRead:
        self._validate(payload)
        record = ElectricalConnection(**self._record_values(payload))
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
        self._validate(payload, exclude_id=connection_id)
        record.sqlmodel_update(self._record_values(payload))
        record.updated_at = datetime.now(UTC)
        self._commit()
        return self._connection_read(record)

    def delete(self, connection_id: UUID) -> None:
        record = self.connections.get(connection_id)
        if record is None:
            raise ElectricalNotFoundError
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
        connection_records = self.connections.list()
        connection_reads = [self._connection_read(item) for item in connection_records]
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
        self._enforce_protective_device_line_phases(payload, source, target)
        self._validate_endpoint_phases(payload, source, target)
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
    def _enforce_protective_device_line_phases(
        payload: ElectricalConnectionWrite,
        source: ElectricalEndpointProjection,
        target: ElectricalEndpointProjection,
    ) -> None:
        """Force the line phase derived from a rail onto new or edited wiring.

        N and PE remain user-selectable. Existing contradictory records are still shown
        with warnings until they are edited; every subsequent save stores the calculated
        line phase instead of accepting a manual L1/L2/L3 override.
        """
        line_phases = {ElectricalPhase.L1, ElectricalPhase.L2, ElectricalPhase.L3}
        requirements: list[tuple[ElectricalPhase, ...]] = []
        for endpoint in (source, target):
            if (
                endpoint.kind != ElectricalEndpointKind.PROTECTIVE_DEVICE
                or endpoint.effective_phases is None
            ):
                continue
            required = tuple(
                phase for phase in endpoint.effective_phases if phase in line_phases
            )
            if required:
                requirements.append(required)
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
        preserved = [phase for phase in payload.phases if phase not in line_phases]
        order = {phase: index for index, phase in enumerate(ElectricalPhase)}
        payload.phases = sorted(set(required).union(preserved), key=order.__getitem__)

    @staticmethod
    def _validate_endpoint_phases(
        payload: ElectricalConnectionWrite,
        source: ElectricalEndpointProjection,
        target: ElectricalEndpointProjection,
    ) -> None:
        line_phases = {ElectricalPhase.L1, ElectricalPhase.L2, ElectricalPhase.L3}
        selected = set(payload.phases) & line_phases
        for endpoint, role in ((source, "Quelle"), (target, "Ziel")):
            if endpoint.effective_phases is None:
                continue
            allowed = set(endpoint.effective_phases) & line_phases
            if not allowed:
                continue
            invalid = selected - allowed
            if invalid:
                names = ", ".join(sorted(item.value for item in invalid))
                expected = ", ".join(
                    item.value for item in endpoint.effective_phases if item in line_phases
                )
                raise ElectricalValidationError(
                    f"{role} {endpoint.name} akzeptiert nicht {names}; "
                    f"wirksame Phase: {expected}"
                )
            if endpoint.kind == ElectricalEndpointKind.PROTECTIVE_DEVICE and selected != allowed:
                expected = ", ".join(
                    item.value for item in endpoint.effective_phases if item in line_phases
                )
                raise ElectricalValidationError(
                    f"Die Verbindung am Schutzgerät {endpoint.name} muss exakt "
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
                    set(self._phases(record)),
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
            source, target, stored_phases
        )
        return ElectricalConnectionRead(
            id=record.id,
            source=self._endpoint_read(source),
            target=self._endpoint_read(target),
            connection_type=ElectricalConnectionType(record.connection_type),
            label=record.label,
            phases=stored_phases,
            effective_phases=effective_phases,
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

    @staticmethod
    def _effective_connection_phases(
        source: ElectricalEndpointProjection,
        target: ElectricalEndpointProjection,
        stored: list[ElectricalPhase],
    ) -> tuple[list[ElectricalPhase], list[str]]:
        allowed = set(stored)
        for endpoint in (source, target):
            if endpoint.effective_phases is None:
                continue
            line_allowed = set(endpoint.effective_phases) & {
                ElectricalPhase.L1,
                ElectricalPhase.L2,
                ElectricalPhase.L3,
            }
            if line_allowed:
                allowed -= {
                    ElectricalPhase.L1,
                    ElectricalPhase.L2,
                    ElectricalPhase.L3,
                } - line_allowed
        order = {phase: index for index, phase in enumerate(ElectricalPhase)}
        effective = sorted(allowed, key=order.__getitem__)
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
