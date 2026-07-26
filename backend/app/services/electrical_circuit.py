from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.models.electrical_circuit import ElectricalCircuit, ElectricalCircuitAssetLink
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
)
from app.services.electrical import (
    ElectricalConflictError,
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
            )
        except ValueError as exc:
            raise ElectricalSortError(str(exc)) from exc
        return Page.create(
            [self._to_read(item) for item in result.items],
            result.total,
            page,
            page_size,
        )

    def create(self, payload: ElectricalCircuitWrite) -> ElectricalCircuitRead:
        self._validate_references(payload)
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
        self._validate_references(payload)
        self._validate_number(payload, exclude_id=circuit_id)
        projection.record.sqlmodel_update(payload.model_dump(mode="python"))
        projection.record.updated_at = datetime.now(UTC)
        self._commit()
        return self.get_read(circuit_id)

    def delete(self, circuit_id: UUID) -> None:
        projection = self.repository.get(circuit_id)
        if projection is None:
            raise ElectricalNotFoundError
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

    def _validate_references(self, payload: ElectricalCircuitWrite) -> None:
        if self.distributions.get(payload.distribution_id) is None:
            raise ElectricalValidationError("Target distribution does not exist or is archived")
        if payload.protective_device_id is None:
            return
        device = self.devices.get(payload.protective_device_id)
        if device is None:
            raise ElectricalValidationError("Protective device does not exist or is archived")
        if device.record.distribution_id != payload.distribution_id:
            raise ElectricalConflictError(
                "Protective device and circuit must belong to the same distribution"
            )

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

    @staticmethod
    def _to_read(projection: ElectricalCircuitProjection) -> ElectricalCircuitRead:
        return ElectricalCircuitRead.model_validate(
            {
                **projection.record.model_dump(),
                "distribution_name": projection.distribution_name,
                "protective_device_name": projection.protective_device_name,
                "protective_device_code": projection.protective_device_code,
            }
        )

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
