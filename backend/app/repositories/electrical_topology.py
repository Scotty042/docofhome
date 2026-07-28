from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlmodel import Session, col, select

from app.electrical_phase_rail import (
    phase_rail_device_phases,
    phase_rail_din_asset_phases,
    rail_fully_covers_device,
)
from app.models.asset_engine import Asset, AssetType, Location
from app.models.electrical import (
    ElectricalAssetPlacement,
    ElectricalCabinetComponent,
    ElectricalComponent,
    ElectricalDistribution,
    ElectricalProtectiveDevice,
)
from app.models.electrical_circuit import ElectricalCircuit
from app.models.electrical_topology import ElectricalConnection
from app.models.energy import EnergyConfiguration
from app.schemas.electrical_topology import ElectricalEndpointKind, ElectricalPhase
from app.services.din_width import effective_asset_module_width


GRID_CONNECTION_ENDPOINT_ID = UUID("00000000-0000-0000-0000-000000000001")


@dataclass(frozen=True)
class ElectricalEndpointProjection:
    kind: ElectricalEndpointKind
    id: UUID
    name: str
    code: str | None
    type_name: str
    location_name: str | None
    device_type: str | None
    deleted_at: datetime | None
    effective_phases: tuple[ElectricalPhase, ...] | None = None

    @property
    def key(self) -> str:
        return f"{self.kind.value}:{self.id}"


class ElectricalConnectionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(
        self,
        connection_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> ElectricalConnection | None:
        record = self.session.get(ElectricalConnection, connection_id)
        if record is None or (record.deleted_at is not None and not include_deleted):
            return None
        return record

    def list(self, *, include_deleted: bool = False) -> list[ElectricalConnection]:
        statement = select(ElectricalConnection)
        if not include_deleted:
            statement = statement.where(col(ElectricalConnection.deleted_at).is_(None))
        return list(
            self.session.exec(
                statement.order_by(
                    col(ElectricalConnection.created_at),
                    col(ElectricalConnection.id),
                )
            ).all()
        )

    def active_for_target(
        self,
        target_kind: ElectricalEndpointKind,
        target_id: UUID,
        *,
        exclude_id: UUID | None = None,
    ) -> ElectricalConnection | None:
        statement = select(ElectricalConnection).where(
            ElectricalConnection.target_kind == target_kind.value,
            ElectricalConnection.target_id == target_id,
            col(ElectricalConnection.deleted_at).is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(ElectricalConnection.id != exclude_id)
        return self.session.exec(statement).first()

    def add(self, connection: ElectricalConnection) -> None:
        self.session.add(connection)


class ElectricalEndpointRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def resolve(
        self,
        kind: ElectricalEndpointKind,
        endpoint_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> ElectricalEndpointProjection | None:
        projection = self._all_projections().get(f"{kind.value}:{endpoint_id}")
        if projection is None and kind == ElectricalEndpointKind.ASSET:
            asset = self.session.get(Asset, endpoint_id)
            if asset is not None:
                asset_type = self.session.get(AssetType, asset.asset_type_id)
                location = (
                    self.session.get(Location, asset.location_id) if asset.location_id else None
                )
                projection = ElectricalEndpointProjection(
                    kind=kind,
                    id=asset.id,
                    name=asset.name,
                    code=asset.jarvis_code,
                    type_name=asset_type.name if asset_type else "Asset",
                    location_name=location.name if location else None,
                    device_type=None,
                    deleted_at=asset.deleted_at,
                )
        if projection is None:
            return None
        if projection.deleted_at is not None and not include_deleted:
            return None
        return projection

    def list(self, *, include_deleted: bool = False) -> list[ElectricalEndpointProjection]:
        projections = list(self._all_projections().values())
        if not include_deleted:
            projections = [item for item in projections if item.deleted_at is None]
        return sorted(
            projections,
            key=lambda item: (item.name.casefold(), item.type_name.casefold(), item.key),
        )

    def _all_projections(self) -> dict[str, ElectricalEndpointProjection]:
        assets = {item.id: item for item in self.session.exec(select(Asset)).all()}
        asset_types = {item.id: item for item in self.session.exec(select(AssetType)).all()}
        locations = {item.id: item for item in self.session.exec(select(Location)).all()}
        components = {
            item.id: item for item in self.session.exec(select(ElectricalComponent)).all()
        }
        cabinet_components = list(
            self.session.exec(select(ElectricalCabinetComponent)).all()
        )
        protective_devices = list(
            self.session.exec(select(ElectricalProtectiveDevice)).all()
        )
        asset_placements = {
            item.asset_id: item
            for item in self.session.exec(
                select(ElectricalAssetPlacement).where(
                    col(ElectricalAssetPlacement.deleted_at).is_(None)
                )
            ).all()
        }
        protective_devices_by_id = {item.id: item for item in protective_devices}
        distributions = {
            item.id: item
            for item in self.session.exec(select(ElectricalDistribution)).all()
        }
        component_asset_ids = {item.asset_id for item in components.values()}
        projections: dict[str, ElectricalEndpointProjection] = {}
        energy = self.session.get(EnergyConfiguration, 1)
        grid = ElectricalEndpointProjection(
            kind=ElectricalEndpointKind.GRID_CONNECTION,
            id=GRID_CONNECTION_ENDPOINT_ID,
            name=(
                energy.grid_connection_name
                if energy and energy.grid_connection_name
                else "Netzanschluss"
            ),
            code=(energy.metering_point_id if energy else None),
            type_name="Öffentliches Stromnetz / Hauseinspeisung",
            location_name=(energy.grid_operator if energy else None),
            device_type=None,
            deleted_at=None,
            effective_phases=(
                ElectricalPhase.L1,
                ElectricalPhase.L2,
                ElectricalPhase.L3,
                ElectricalPhase.N,
                ElectricalPhase.PE,
            ),
        )
        projections[grid.key] = grid

        def asset_values(
            asset: Asset,
        ) -> tuple[str, str | None, str | None, datetime | None]:
            asset_type = asset_types.get(asset.asset_type_id)
            location = locations.get(asset.location_id) if asset.location_id else None
            return (
                asset_type.name if asset_type else "Asset",
                location.name if location else None,
                asset.jarvis_code,
                asset.deleted_at,
            )

        def protective_device_phases(
            device: ElectricalProtectiveDevice,
        ) -> tuple[ElectricalPhase, ...] | None:
            component = components.get(device.id)
            device_asset = assets.get(component.asset_id) if component is not None else None
            device_width = device.module_width
            if device_width is None and device_asset is not None:
                device_width = effective_asset_module_width(self.session, device_asset)
            if (
                device.row_number is None
                or device.start_position is None
                or device_width is None
            ):
                return None
            candidates = [
                cabinet_component
                for cabinet_component in cabinet_components
                if cabinet_component.deleted_at is None
                and cabinet_component.distribution_id == device.distribution_id
                and cabinet_component.area_id == device.area_id
                and cabinet_component.row_number == device.row_number
                and cabinet_component.component_type == "phase_rail"
                and rail_fully_covers_device(
                    rail_start=cabinet_component.start_position,
                    rail_width=cabinet_component.module_width,
                    device_start=device.start_position,
                    device_width=device_width,
                )
            ]
            candidates.sort(
                key=lambda item: (
                    item.module_width,
                    item.start_position,
                    item.name.casefold(),
                    str(item.id),
                )
            )
            if not candidates:
                return None
            rail = candidates[0]
            phases = phase_rail_device_phases(
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
            return phases or None

        def din_asset_phases(asset: Asset) -> tuple[ElectricalPhase, ...] | None:
            placement = asset_placements.get(asset.id)
            if placement is None:
                return None
            candidates = [
                cabinet_component
                for cabinet_component in cabinet_components
                if cabinet_component.deleted_at is None
                and cabinet_component.distribution_id == placement.distribution_id
                and cabinet_component.area_id == placement.area_id
                and cabinet_component.row_number == placement.row_number
                and cabinet_component.component_type == "phase_rail"
                and rail_fully_covers_device(
                    rail_start=cabinet_component.start_position,
                    rail_width=cabinet_component.module_width,
                    device_start=placement.start_position,
                    device_width=placement.module_width,
                )
            ]
            candidates.sort(
                key=lambda item: (
                    item.module_width,
                    item.start_position,
                    item.name.casefold(),
                    str(item.id),
                )
            )
            if not candidates:
                return None
            rail = candidates[0]
            phases = phase_rail_din_asset_phases(
                rail_start=rail.start_position,
                rail_width=rail.module_width,
                phase_l1=rail.phase_l1,
                phase_l2=rail.phase_l2,
                phase_l3=rail.phase_l3,
                start_phase=rail.start_phase,
                asset_start=placement.start_position,
                asset_width=placement.module_width,
            )
            return phases or None

        for asset in assets.values():
            if asset.id in component_asset_ids:
                continue
            type_name, location_name, code, deleted_at = asset_values(asset)
            item = ElectricalEndpointProjection(
                kind=ElectricalEndpointKind.ASSET,
                id=asset.id,
                name=asset.name,
                code=code,
                type_name=type_name,
                location_name=location_name,
                device_type=None,
                deleted_at=deleted_at,
                effective_phases=din_asset_phases(asset),
            )
            projections[item.key] = item

        for distribution in distributions.values():
            component = components.get(distribution.id)
            distribution_asset = assets.get(component.asset_id) if component else None
            if component is None or distribution_asset is None:
                continue
            _, location_name, code, asset_deleted_at = asset_values(distribution_asset)
            item = ElectricalEndpointProjection(
                kind=ElectricalEndpointKind.DISTRIBUTION,
                id=distribution.id,
                name=distribution.designation or distribution_asset.name,
                code=code,
                type_name=(
                    "Hauptverteilung"
                    if distribution.distribution_type == "main"
                    else "Unterverteilung"
                ),
                location_name=location_name,
                device_type=None,
                deleted_at=component.deleted_at or asset_deleted_at,
            )
            projections[item.key] = item

        for device in protective_devices:
            component = components.get(device.id)
            device_asset = assets.get(component.asset_id) if component else None
            if component is None or device_asset is None:
                continue
            _, location_name, code, asset_deleted_at = asset_values(device_asset)
            item = ElectricalEndpointProjection(
                kind=ElectricalEndpointKind.PROTECTIVE_DEVICE,
                id=device.id,
                name=device_asset.name,
                code=code,
                type_name="Schutzgerät",
                location_name=location_name,
                device_type=device.device_type,
                deleted_at=component.deleted_at or asset_deleted_at,
                effective_phases=protective_device_phases(device),
            )
            projections[item.key] = item

        for cabinet_component in cabinet_components:
            distribution = distributions.get(cabinet_component.distribution_id)
            distribution_role = (
                components.get(distribution.id) if distribution is not None else None
            )
            distribution_asset = (
                assets.get(distribution_role.asset_id)
                if distribution_role is not None
                else None
            )
            location_name = None
            if distribution_asset is not None:
                _, location_name, _, _ = asset_values(distribution_asset)
            type_names = {
                "phase_distribution_block": "Phasenverteilerblock",
                "busbar": "Sammelschiene",
                "phase_rail": "Phasenschiene",
                "neutral_rail": "N-Schiene",
                "protective_earth_rail": "PE-Schiene",
                "terminal_block": "Reihenklemme",
                "connection_block": "Anschlussblock",
                "potential_distribution": "Potentialverteiler",
                "other": "Schrankkomponente",
            }
            item = ElectricalEndpointProjection(
                kind=ElectricalEndpointKind.CABINET_COMPONENT,
                id=cabinet_component.id,
                name=cabinet_component.name,
                code=None,
                type_name=type_names.get(
                    cabinet_component.component_type, "Schrankkomponente"
                ),
                location_name=location_name,
                device_type=cabinet_component.component_type,
                deleted_at=(
                    cabinet_component.deleted_at
                    or (distribution_role.deleted_at if distribution_role else None)
                    or (distribution_asset.deleted_at if distribution_asset else None)
                ),
                effective_phases=tuple(
                    phase
                    for phase, selected in (
                        (ElectricalPhase.L1, cabinet_component.phase_l1),
                        (ElectricalPhase.L2, cabinet_component.phase_l2),
                        (ElectricalPhase.L3, cabinet_component.phase_l3),
                        (ElectricalPhase.N, cabinet_component.neutral),
                        (ElectricalPhase.PE, cabinet_component.protective_earth),
                    )
                    if selected
                ),
            )
            projections[item.key] = item

        for circuit in self.session.exec(select(ElectricalCircuit)).all():
            circuit_device = (
                protective_devices_by_id.get(circuit.protective_device_id)
                if circuit.protective_device_id is not None
                else None
            )
            circuit_device_component = (
                components.get(circuit_device.id) if circuit_device is not None else None
            )
            circuit_phases = (
                protective_device_phases(circuit_device)
                if circuit_device is not None
                and circuit_device_component is not None
                and circuit_device_component.deleted_at is None
                else None
            )
            item = ElectricalEndpointProjection(
                kind=ElectricalEndpointKind.CIRCUIT,
                id=circuit.id,
                name=circuit.name,
                code=circuit.circuit_number,
                type_name="Stromkreis",
                location_name=None,
                device_type=None,
                deleted_at=circuit.deleted_at,
                effective_phases=circuit_phases,
            )
            projections[item.key] = item
        return projections
