from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import Session, col, select

from app.models.asset_engine import Asset, AssetType, Location
from app.models.electrical import (
    ElectricalComponent,
    ElectricalDistribution,
    ElectricalProtectiveDevice,
)
from app.models.electrical_circuit import (
    ElectricalCircuit,
    ElectricalCircuitAssetLink,
)
from app.repositories.asset_engine import PageResult
from app.schemas.asset_engine import SortOrder


@dataclass(frozen=True)
class ElectricalCircuitProjection:
    record: ElectricalCircuit
    distribution_name: str
    protective_device_name: str | None
    protective_device_code: str | None


@dataclass(frozen=True)
class ElectricalCircuitAssetProjection:
    link: ElectricalCircuitAssetLink
    asset: Asset
    asset_type_name: str
    location_name: str | None


class ElectricalCircuitRepository:
    sort_fields = frozenset(
        {
            "name",
            "circuit_number",
            "distribution_name",
            "protective_device_name",
            "created_at",
            "updated_at",
        }
    )

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(
        self,
        circuit_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> ElectricalCircuitProjection | None:
        projection = self._projections().get(circuit_id)
        if projection is None:
            return None
        if not include_deleted and projection.record.deleted_at is not None:
            return None
        return projection

    def list_page(
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
    ) -> PageResult[ElectricalCircuitProjection]:
        if sort_by not in self.sort_fields:
            allowed = ", ".join(sorted(self.sort_fields))
            raise ValueError(f"Unsupported sort field '{sort_by}'. Allowed fields: {allowed}")
        candidates = [
            item
            for item in self._projections().values()
            if include_deleted or item.record.deleted_at is None
        ]
        if distribution_id is not None:
            candidates = [
                item for item in candidates if item.record.distribution_id == distribution_id
            ]
        if protective_device_id is not None:
            candidates = [
                item
                for item in candidates
                if item.record.protective_device_id == protective_device_id
            ]
        normalized_search = search.strip().casefold() if search else ""
        if normalized_search:
            candidates = [
                item
                for item in candidates
                if any(
                    normalized_search in value.casefold()
                    for value in (
                        item.record.name,
                        item.record.circuit_number or "",
                        item.record.description or "",
                        item.record.notes or "",
                        item.distribution_name,
                        item.protective_device_name or "",
                        item.protective_device_code or "",
                    )
                )
            ]
        candidates.sort(
            key=lambda item: (self._sort_value(item, sort_by), str(item.record.id)),
            reverse=sort_order == SortOrder.DESC,
        )
        total = len(candidates)
        offset = (page - 1) * page_size
        return PageResult(items=candidates[offset : offset + page_size], total=total)

    def add(self, circuit: ElectricalCircuit) -> None:
        self.session.add(circuit)

    def add_asset_link(self, link: ElectricalCircuitAssetLink) -> None:
        self.session.add(link)

    def get_active_asset_link(
        self,
        circuit_id: UUID,
        asset_id: UUID,
    ) -> ElectricalCircuitAssetLink | None:
        statement = select(ElectricalCircuitAssetLink).where(
            ElectricalCircuitAssetLink.circuit_id == circuit_id,
            ElectricalCircuitAssetLink.asset_id == asset_id,
            col(ElectricalCircuitAssetLink.deleted_at).is_(None),
        )
        return self.session.exec(statement).first()

    def list_asset_links(
        self,
        circuit_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> list[ElectricalCircuitAssetProjection]:
        statement = select(ElectricalCircuitAssetLink).where(
            ElectricalCircuitAssetLink.circuit_id == circuit_id
        )
        if not include_deleted:
            statement = statement.where(col(ElectricalCircuitAssetLink.deleted_at).is_(None))
        links = list(self.session.exec(statement).all())
        assets = {item.id: item for item in self.session.exec(select(Asset)).all()}
        asset_types = {item.id: item for item in self.session.exec(select(AssetType)).all()}
        locations = {item.id: item for item in self.session.exec(select(Location)).all()}
        result: list[ElectricalCircuitAssetProjection] = []
        for link in links:
            asset = assets.get(link.asset_id)
            if asset is None:
                raise ValueError("Stored circuit assignment has no asset")
            asset_type = asset_types.get(asset.asset_type_id)
            if asset_type is None:
                raise ValueError("Stored circuit assignment asset has no type")
            location = locations.get(asset.location_id) if asset.location_id else None
            result.append(
                ElectricalCircuitAssetProjection(
                    link=link,
                    asset=asset,
                    asset_type_name=asset_type.name,
                    location_name=location.name if location else None,
                )
            )
        return sorted(
            result,
            key=lambda item: (
                item.link.deleted_at is not None,
                item.asset.name.casefold(),
                str(item.link.id),
            ),
        )

    def has_active_for_distribution(self, distribution_id: UUID) -> bool:
        statement = select(ElectricalCircuit.id).where(
            ElectricalCircuit.distribution_id == distribution_id,
            col(ElectricalCircuit.deleted_at).is_(None),
        )
        return self.session.exec(statement).first() is not None

    def has_active_for_device(self, device_id: UUID) -> bool:
        statement = select(ElectricalCircuit.id).where(
            ElectricalCircuit.protective_device_id == device_id,
            col(ElectricalCircuit.deleted_at).is_(None),
        )
        return self.session.exec(statement).first() is not None

    def number_exists(
        self,
        *,
        distribution_id: UUID,
        circuit_number: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        statement = select(ElectricalCircuit.id).where(
            ElectricalCircuit.distribution_id == distribution_id,
            ElectricalCircuit.circuit_number == circuit_number,
            col(ElectricalCircuit.deleted_at).is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(ElectricalCircuit.id != exclude_id)
        return self.session.exec(statement).first() is not None

    def _projections(self) -> dict[UUID, ElectricalCircuitProjection]:
        distributions = {
            item.id: item for item in self.session.exec(select(ElectricalDistribution)).all()
        }
        components = {
            item.id: item for item in self.session.exec(select(ElectricalComponent)).all()
        }
        assets = {item.id: item for item in self.session.exec(select(Asset)).all()}
        devices = {
            item.id: item for item in self.session.exec(select(ElectricalProtectiveDevice)).all()
        }
        projections: dict[UUID, ElectricalCircuitProjection] = {}
        for circuit in self.session.exec(select(ElectricalCircuit)).all():
            distribution = distributions.get(circuit.distribution_id)
            distribution_component = components.get(circuit.distribution_id)
            if distribution is None or distribution_component is None:
                raise ValueError("Stored electrical circuit has an invalid distribution")
            distribution_asset = assets.get(distribution_component.asset_id)
            if distribution_asset is None:
                raise ValueError("Stored electrical circuit distribution has no asset")
            distribution_name = distribution.designation or distribution_asset.name
            device_name: str | None = None
            device_code: str | None = None
            if circuit.protective_device_id is not None:
                device = devices.get(circuit.protective_device_id)
                device_component = components.get(circuit.protective_device_id)
                if device is None or device_component is None:
                    raise ValueError("Stored electrical circuit has an invalid protective device")
                device_asset = assets.get(device_component.asset_id)
                if device_asset is None:
                    raise ValueError("Stored circuit protective device has no asset")
                device_name = device_asset.name
                device_code = device_asset.jarvis_code
            projections[circuit.id] = ElectricalCircuitProjection(
                record=circuit,
                distribution_name=distribution_name,
                protective_device_name=device_name,
                protective_device_code=device_code,
            )
        return projections

    @staticmethod
    def _sort_value(
        projection: ElectricalCircuitProjection,
        sort_by: str,
    ) -> Any:
        value: str | datetime | None
        if sort_by == "distribution_name":
            value = projection.distribution_name
        elif sort_by == "protective_device_name":
            value = projection.protective_device_name
        else:
            value = getattr(projection.record, sort_by)
        if isinstance(value, str):
            return (value == "", value.casefold())
        return (value is None, value or datetime.min)
