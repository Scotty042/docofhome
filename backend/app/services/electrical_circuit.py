from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.electrical_device_classification import protective_asset_device_type
from app.models.asset_engine import Asset, AssetType
from app.models.electrical import ElectricalAssetPlacement
from app.models.electrical_circuit import ElectricalCircuit, ElectricalCircuitAssetLink
from app.models.electrical_topology import ElectricalConnection
from app.repositories.asset_engine import AssetRepository
from app.repositories.electrical import (
    ElectricalDistributionRepository,
    ElectricalProtectiveDeviceRepository,
)
from app.repositories.electrical_circuit import (
    ElectricalCircuitAssetProjection,
    ElectricalCircuitProjection,
    ElectricalCircuitRepository,
)
from app.schemas.asset_engine import Page, SortOrder
from app.schemas.electrical_circuit import (
    ElectricalCircuitAssetRead,
    ElectricalCircuitAssetWrite,
    ElectricalCircuitRead,
    ElectricalCircuitWrite,
    ElectricalProtectiveDeviceOptionRead,
)
from app.services.electrical import (
    ElectricalConflictError,
    ElectricalDistributionService,
    ElectricalNotFoundError,
    ElectricalSortError,
    ElectricalValidationError,
)


class ElectricalCircuitService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = ElectricalCircuitRepository(session)
        self.distributions = ElectricalDistributionRepository(session)
        self.devices = ElectricalProtectiveDeviceRepository(session)
        self.assets = AssetRepository(session)

    def get_read(
        self,
        circuit_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> ElectricalCircuitRead:
        projection = self.repository.get(
            circuit_id,
            include_deleted=include_deleted,
        )
        if projection is None:
            raise ElectricalNotFoundError
        return self._to_read(projection)

    def list_read(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        sort_by: str,
        sort_order: SortOrder,
        include_deleted: bool,
        distribution_id: UUID | None,
        protective_device_id: UUID | None,
        protective_device_asset_id: UUID | None = None,
    ) -> Page[ElectricalCircuitRead]:
        try:
            result = self.repository.list_page(
                page=page,
                page_size=page_size,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
                include_deleted=include_deleted,
                distribution_id=distribution_id,
                protective_device_id=protective_device_id,
                protective_device_asset_id=protective_device_asset_id,
            )
        except ValueError as exc:
            raise ElectricalSortError(str(exc)) from exc
        return Page.create(
            [self._to_read(item) for item in result.items],
            result.total,
            page,
            page_size,
        )

    def protective_device_options(
        self,
        distribution_id: UUID,
        *,
        circuit_id: UUID | None = None,
    ) -> list[ElectricalProtectiveDeviceOptionRead]:
        detail = ElectricalDistributionService(self.session).get_read(distribution_id)
        active_circuits = list(
            self.session.exec(
                select(ElectricalCircuit).where(
                    ElectricalCircuit.distribution_id == distribution_id,
                    col(ElectricalCircuit.deleted_at).is_(None),
                )
            ).all()
        )
        by_device = {
            item.protective_device_id: item
            for item in active_circuits
            if item.protective_device_id is not None and item.id != circuit_id
        }
        by_asset = {
            item.protective_device_asset_id: item
            for item in active_circuits
            if item.protective_device_asset_id is not None and item.id != circuit_id
        }
        result: list[ElectricalProtectiveDeviceOptionRead] = []
        type_labels = {"fuse": "Sicherung", "mcb": "LS", "rcbo": "FI/LS"}
        for device in detail.protective_devices:
            if device.device_type.value not in {"fuse", "mcb", "rcbo"}:
                continue
            if device.row_number is None or device.start_position is None:
                continue
            occupied_by = by_device.get(device.id)
            phase_text = [phase.value for phase in device.calculated_phases]
            position = f"Reihe {device.row_number}, Position {device.start_position}"
            rating = (
                f"{device.characteristic or ''}{device.rated_current_a:g} A"
                if device.rated_current_a is not None
                else "ohne Nennwert"
            )
            label = (
                f"{device.asset.jarvis_code} – {type_labels[device.device_type.value]} "
                f"{rating} – {position}"
                + (f" – {', '.join(phase_text)}" if phase_text else "")
            )
            result.append(
                ElectricalProtectiveDeviceOptionRead(
                    id=device.id,
                    reference_type="legacy_device",
                    label=label,
                    device_type=device.device_type.value,
                    rated_current_a=device.rated_current_a,
                    characteristic=device.characteristic,
                    position=position,
                    phases=phase_text,
                    occupied=occupied_by is not None,
                    occupied_by_circuit_id=occupied_by.id if occupied_by else None,
                    occupied_by_circuit_name=occupied_by.name if occupied_by else None,
                )
            )

        placements = list(
            self.session.exec(
                select(ElectricalAssetPlacement).where(
                    ElectricalAssetPlacement.distribution_id == distribution_id,
                    col(ElectricalAssetPlacement.deleted_at).is_(None),
                )
            ).all()
        )
        for placement in placements:
            asset = self.session.get(Asset, placement.asset_id)
            if asset is None or asset.deleted_at is not None or asset.status != "active":
                continue
            asset_type = self.session.get(AssetType, asset.asset_type_id)
            if asset_type is None or asset_type.deleted_at is not None:
                continue
            device_type = protective_asset_device_type(asset_type.name)
            if device_type is None:
                continue
            occupied_by = by_asset.get(asset.id)
            characteristic = asset.breaker_characteristic or asset_type.breaker_characteristic
            rated_current = asset.rated_current_a or asset_type.rated_current_a
            phases = self._asset_phases(asset.id)
            position = f"Reihe {placement.row_number}, Position {placement.start_position}"
            rating = (
                f"{characteristic or ''}{rated_current:g} A"
                if rated_current is not None
                else "ohne Nennwert"
            )
            label = (
                f"{asset.jarvis_code} – {asset.name} – {type_labels[device_type]} "
                f"{rating} – {position}"
                + (f" – {', '.join(phases)}" if phases else "")
            )
            result.append(
                ElectricalProtectiveDeviceOptionRead(
                    id=asset.id,
                    reference_type="asset",
                    label=label,
                    device_type=device_type,
                    rated_current_a=rated_current,
                    characteristic=characteristic,
                    position=position,
                    phases=phases,
                    occupied=occupied_by is not None,
                    occupied_by_circuit_id=occupied_by.id if occupied_by else None,
                    occupied_by_circuit_name=occupied_by.name if occupied_by else None,
                )
            )
        return sorted(result, key=lambda item: item.label.casefold())

    def create(self, payload: ElectricalCircuitWrite) -> ElectricalCircuitRead:
        self._validate_references(payload, exclude_circuit_id=None)
        self._validate_number(payload, exclude_id=None)
        circuit = ElectricalCircuit(**payload.model_dump(mode="python"))
        self.repository.add(circuit)
        self._commit()
        return self.get_read(circuit.id)

    def update(
        self,
        circuit_id: UUID,
        payload: ElectricalCircuitWrite,
    ) -> ElectricalCircuitRead:
        projection = self.repository.get(circuit_id)
        if projection is None:
            raise ElectricalNotFoundError
        self._validate_references(payload, exclude_circuit_id=circuit_id)
        self._validate_number(payload, exclude_id=circuit_id)
        projection.record.sqlmodel_update(payload.model_dump(mode="python"))
        projection.record.updated_at = datetime.now(UTC)
        self._commit()
        return self.get_read(circuit_id)

    def delete(self, circuit_id: UUID) -> None:
        projection = self.repository.get(circuit_id)
        if projection is None:
            raise ElectricalNotFoundError
        active_connection = self.session.exec(
            select(ElectricalConnection).where(
                col(ElectricalConnection.deleted_at).is_(None),
                (
                    (ElectricalConnection.source_kind == "circuit")
                    & (ElectricalConnection.source_id == circuit_id)
                )
                | (
                    (ElectricalConnection.target_kind == "circuit")
                    & (ElectricalConnection.target_id == circuit_id)
                ),
            )
        ).first()
        if active_connection is not None:
            raise ElectricalConflictError(
                "Der Stromkreis ist noch in der Versorgungstopologie verkabelt. "
                "Entferne zuerst diese Verbindungen."
            )
        now = datetime.now(UTC)
        projection.record.deleted_at = now
        projection.record.updated_at = now
        self._commit()

    def list_assets(
        self,
        circuit_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> list[ElectricalCircuitAssetRead]:
        if self.repository.get(circuit_id, include_deleted=True) is None:
            raise ElectricalNotFoundError
        return [
            self._to_asset_read(item)
            for item in self.repository.list_asset_links(
                circuit_id,
                include_deleted=include_deleted,
            )
        ]

    def assign_asset(
        self,
        circuit_id: UUID,
        payload: ElectricalCircuitAssetWrite,
    ) -> ElectricalCircuitAssetRead:
        if self.repository.get(circuit_id) is None:
            raise ElectricalNotFoundError
        if self.assets.get(payload.asset_id) is None:
            raise ElectricalValidationError("Asset does not exist or is archived")
        if self.repository.get_active_asset_link(circuit_id, payload.asset_id):
            raise ElectricalConflictError("Asset is already assigned to this circuit")
        link = ElectricalCircuitAssetLink(
            circuit_id=circuit_id,
            asset_id=payload.asset_id,
        )
        self.repository.add_asset_link(link)
        self._commit()
        projection = next(
            item for item in self.repository.list_asset_links(circuit_id) if item.link.id == link.id
        )
        return self._to_asset_read(projection)

    def remove_asset(self, circuit_id: UUID, asset_id: UUID) -> None:
        if self.repository.get(circuit_id) is None:
            raise ElectricalNotFoundError
        link = self.repository.get_active_asset_link(circuit_id, asset_id)
        if link is None:
            raise ElectricalNotFoundError
        now = datetime.now(UTC)
        link.deleted_at = now
        link.updated_at = now
        self._commit()

    def _validate_references(
        self, payload: ElectricalCircuitWrite, *, exclude_circuit_id: UUID | None
    ) -> None:
        if self.distributions.get(payload.distribution_id) is None:
            raise ElectricalValidationError("Target distribution does not exist or is archived")
        if payload.protective_device_id is not None:
            self._validate_legacy_protective_device(payload, exclude_circuit_id)
        elif payload.protective_device_asset_id is not None:
            self._validate_asset_protective_device(payload, exclude_circuit_id)

    def _validate_number(
        self,
        payload: ElectricalCircuitWrite,
        *,
        exclude_id: UUID | None,
    ) -> None:
        if payload.circuit_number is None:
            return
        if self.repository.number_exists(
            distribution_id=payload.distribution_id,
            circuit_number=payload.circuit_number,
            exclude_id=exclude_id,
        ):
            raise ElectricalConflictError("Circuit number already exists in this distribution")

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ElectricalConflictError(
                "Circuit conflicts with an existing electrical record"
            ) from exc

    def _to_read(self, projection: ElectricalCircuitProjection) -> ElectricalCircuitRead:
        device_type = None
        device_rating = None
        device_position = None
        device_phases: list[str] = []
        if projection.record.protective_device_id is not None:
            options = self.protective_device_options(
                projection.record.distribution_id,
                circuit_id=projection.record.id,
            )
            option = next(
                (
                    item
                    for item in options
                    if item.reference_type == "legacy_device"
                    and item.id == projection.record.protective_device_id
                ),
                None,
            )
        elif projection.record.protective_device_asset_id is not None:
            options = self.protective_device_options(
                projection.record.distribution_id,
                circuit_id=projection.record.id,
            )
            option = next(
                (
                    item
                    for item in options
                    if item.reference_type == "asset"
                    and item.id == projection.record.protective_device_asset_id
                ),
                None,
            )
        else:
            option = None
        if option is not None:
            device_type = option.device_type
            device_position = option.position
            device_phases = option.phases
            if option.rated_current_a is not None:
                device_rating = f"{option.characteristic or ''}{option.rated_current_a:g} A"
        return ElectricalCircuitRead.model_validate(
            {
                **projection.record.model_dump(),
                "distribution_name": projection.distribution_name,
                "protective_device_name": projection.protective_device_name,
                "protective_device_code": projection.protective_device_code,
                "protective_device_type": device_type,
                "protective_device_rating": device_rating,
                "protective_device_position": device_position,
                "protective_device_phases": device_phases,
                "protective_device_assignment_missing": (
                    projection.record.protective_device_id is None
                    and projection.record.protective_device_asset_id is None
                ),
            }
        )

    def _validate_legacy_protective_device(
        self,
        payload: ElectricalCircuitWrite,
        exclude_circuit_id: UUID | None,
    ) -> None:
        assert payload.protective_device_id is not None
        device = self.devices.get(payload.protective_device_id)
        if device is None:
            raise ElectricalValidationError("Protective device does not exist or is archived")
        if device.record.distribution_id != payload.distribution_id:
            raise ElectricalConflictError(
                "Protective device and circuit must belong to the same distribution"
            )
        if device.record.device_type not in {"fuse", "mcb", "rcbo"}:
            raise ElectricalValidationError(
                "Ein Stromkreis kann nur einer Sicherung, einem Leitungsschutzschalter "
                "oder einem FI/LS zugeordnet werden. FI/RCD und Überspannungsschutz "
                "schützen Gruppen und sind kein einzelnes Stromkreis-Schutzgerät."
            )
        if device.record.row_number is None or device.record.start_position is None:
            raise ElectricalValidationError(
                "Das ausgewählte Schutzgerät muss aktiv und in der Verteilung platziert sein."
            )
        occupied = self.session.exec(
            select(ElectricalCircuit).where(
                ElectricalCircuit.protective_device_id == payload.protective_device_id,
                col(ElectricalCircuit.deleted_at).is_(None),
            )
        ).first()
        if occupied is not None and occupied.id != exclude_circuit_id:
            raise ElectricalConflictError(
                f"Das Schutzgerät ist bereits dem Stromkreis „{occupied.name}“ zugeordnet."
            )

    def _validate_asset_protective_device(
        self,
        payload: ElectricalCircuitWrite,
        exclude_circuit_id: UUID | None,
    ) -> None:
        assert payload.protective_device_asset_id is not None
        asset = self.session.get(Asset, payload.protective_device_asset_id)
        asset_type = (
            self.session.get(AssetType, asset.asset_type_id) if asset is not None else None
        )
        placement = self.session.exec(
            select(ElectricalAssetPlacement).where(
                ElectricalAssetPlacement.distribution_id == payload.distribution_id,
                ElectricalAssetPlacement.asset_id == payload.protective_device_asset_id,
                col(ElectricalAssetPlacement.deleted_at).is_(None),
            )
        ).first()
        if (
            asset is None
            or asset.deleted_at is not None
            or asset.status != "active"
            or asset_type is None
            or asset_type.deleted_at is not None
            or protective_asset_device_type(asset_type.name) is None
        ):
            raise ElectricalValidationError(
                "Das ausgewählte DIN-Gerät ist keine aktive Sicherung, kein LS oder FI/LS."
            )
        if placement is None:
            raise ElectricalValidationError(
                "Das ausgewählte Schutzgerät muss aktiv und in der Verteilung platziert sein."
            )
        occupied = self.session.exec(
            select(ElectricalCircuit).where(
                ElectricalCircuit.protective_device_asset_id
                == payload.protective_device_asset_id,
                col(ElectricalCircuit.deleted_at).is_(None),
            )
        ).first()
        if occupied is not None and occupied.id != exclude_circuit_id:
            raise ElectricalConflictError(
                f"Das Schutzgerät ist bereits dem Stromkreis „{occupied.name}“ zugeordnet."
            )

    def _asset_phases(self, asset_id: UUID) -> list[str]:
        statement = select(ElectricalConnection).where(
            col(ElectricalConnection.deleted_at).is_(None),
            (
                (ElectricalConnection.source_kind == "asset")
                & (ElectricalConnection.source_id == asset_id)
            )
            | (
                (ElectricalConnection.target_kind == "asset")
                & (ElectricalConnection.target_id == asset_id)
            ),
        )
        phases: set[str] = set()
        for connection in self.session.exec(statement).all():
            if connection.phase_l1:
                phases.add("L1")
            if connection.phase_l2:
                phases.add("L2")
            if connection.phase_l3:
                phases.add("L3")
        return [phase for phase in ("L1", "L2", "L3") if phase in phases]

    @staticmethod
    def _to_asset_read(
        projection: ElectricalCircuitAssetProjection,
    ) -> ElectricalCircuitAssetRead:
        return ElectricalCircuitAssetRead(
            link_id=projection.link.id,
            circuit_id=projection.link.circuit_id,
            asset_id=projection.asset.id,
            asset_name=projection.asset.name,
            asset_code=projection.asset.jarvis_code,
            asset_status=projection.asset.status,
            asset_type_name=projection.asset_type_name,
            location_name=projection.location_name,
            asset_deleted_at=projection.asset.deleted_at,
            assigned_at=projection.link.created_at,
            removed_at=projection.link.deleted_at,
        )
