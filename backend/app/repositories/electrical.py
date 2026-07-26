from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import Session, col, select

from app.models.asset_engine import Asset, AssetType, Relationship
from app.models.electrical import (
    ElectricalComponent,
    ElectricalDistribution,
    ElectricalProtectiveDevice,
)
from app.repositories.asset_engine import LocationRepository, PageResult
from app.schemas.asset_engine import SortOrder
from app.schemas.electrical import (
    DistributionType,
    ElectricalRole,
    ProtectiveDeviceType,
)


@dataclass(frozen=True)
class AssetRoleProjection:
    record: Asset
    location_path: str


@dataclass(frozen=True)
class DistributionProjection:
    component: ElectricalComponent
    record: ElectricalDistribution
    asset: AssetRoleProjection
    breadcrumbs: tuple[tuple[UUID, str], ...]
    direct_subdistribution_count: int
    direct_protective_device_count: int


@dataclass(frozen=True)
class ProtectiveDeviceProjection:
    component: ElectricalComponent
    record: ElectricalProtectiveDevice
    asset: AssetRoleProjection
    distribution_name: str


class ElectricalComponentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(
        self,
        component_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> ElectricalComponent | None:
        component = self.session.get(ElectricalComponent, component_id)
        if component is None:
            return None
        if not include_deleted and component.deleted_at is not None:
            return None
        return component

    def active_for_asset(self, asset_id: UUID) -> ElectricalComponent | None:
        statement = select(ElectricalComponent).where(
            ElectricalComponent.asset_id == asset_id,
            col(ElectricalComponent.deleted_at).is_(None),
        )
        return self.session.exec(statement).one_or_none()

    def add(self, component: ElectricalComponent) -> None:
        self.session.add(component)


class ElectricalDistributionRepository:
    sort_fields = frozenset(
        {
            "designation",
            "distribution_type",
            "asset_name",
            "jarvis_code",
            "location_path",
            "created_at",
            "updated_at",
        }
    )

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(
        self,
        distribution_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> DistributionProjection | None:
        projection = self._projections().get(distribution_id)
        if projection is None or not self._visible(projection, include_deleted):
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
        distribution_type: DistributionType | None,
        parent_distribution_id: UUID | None,
        location_id: UUID | None,
    ) -> PageResult[DistributionProjection]:
        self._validate_sort(sort_by)
        candidates = [
            item for item in self._projections().values() if self._visible(item, include_deleted)
        ]
        if distribution_type is not None:
            candidates = [
                item
                for item in candidates
                if item.record.distribution_type == distribution_type.value
            ]
        if parent_distribution_id is not None:
            candidates = [
                item
                for item in candidates
                if item.record.parent_distribution_id == parent_distribution_id
            ]
        if location_id is not None:
            candidates = [
                item for item in candidates if item.asset.record.location_id == location_id
            ]
        normalized_search = search.strip().casefold() if search else ""
        if normalized_search:
            candidates = [
                item
                for item in candidates
                if any(
                    normalized_search in value.casefold()
                    for value in (
                        item.record.designation or "",
                        item.record.description or "",
                        item.record.notes or "",
                        item.asset.record.name,
                        item.asset.record.jarvis_code,
                        item.asset.location_path,
                    )
                )
            ]
        candidates.sort(
            key=lambda item: (self._sort_value(item, sort_by), str(item.component.id)),
            reverse=sort_order == SortOrder.DESC,
        )
        total = len(candidates)
        offset = (page - 1) * page_size
        return PageResult(items=candidates[offset : offset + page_size], total=total)

    def tree(self, *, include_deleted: bool = False) -> list[DistributionProjection]:
        return sorted(
            (item for item in self._projections().values() if self._visible(item, include_deleted)),
            key=lambda item: (
                self.display_name(item).casefold(),
                str(item.component.id),
            ),
        )

    def has_active_children(self, distribution_id: UUID) -> bool:
        return any(
            item.record.parent_distribution_id == distribution_id and self._visible(item, False)
            for item in self._projections().values()
        )

    def has_active_devices(self, distribution_id: UUID) -> bool:
        return bool(
            ElectricalProtectiveDeviceRepository(self.session).for_distribution(
                distribution_id,
                include_deleted=False,
            )
        )

    def add(self, distribution: ElectricalDistribution) -> None:
        self.session.add(distribution)

    def descendant_ids(self, distribution_id: UUID) -> set[UUID]:
        projections = self._projections()
        children: dict[UUID, list[UUID]] = {}
        for item in projections.values():
            parent_id = item.record.parent_distribution_id
            if parent_id is not None and self._visible(item, False):
                children.setdefault(parent_id, []).append(item.component.id)
        descendants: set[UUID] = set()
        pending = list(children.get(distribution_id, []))
        while pending:
            current = pending.pop()
            if current in descendants:
                raise ValueError("Stored distribution hierarchy contains a cycle")
            descendants.add(current)
            pending.extend(children.get(current, []))
        return descendants

    @staticmethod
    def display_name(projection: DistributionProjection) -> str:
        return projection.record.designation or projection.asset.record.name

    def _projections(self) -> dict[UUID, DistributionProjection]:
        components = {
            item.id: item
            for item in self.session.exec(select(ElectricalComponent)).all()
            if item.role == ElectricalRole.DISTRIBUTION.value
        }
        distributions = {
            item.id: item for item in self.session.exec(select(ElectricalDistribution)).all()
        }
        assets = {item.id: item for item in self.session.exec(select(Asset)).all()}
        locations = self._location_paths()

        names: dict[UUID, str] = {}
        asset_projections: dict[UUID, AssetRoleProjection] = {}
        for distribution_id, distribution in distributions.items():
            component = components.get(distribution_id)
            if component is None:
                continue
            asset = assets.get(component.asset_id)
            if asset is None or asset.location_id is None:
                raise ValueError("Stored electrical distribution has an invalid asset")
            asset_projection = AssetRoleProjection(
                record=asset,
                location_path=locations.get(asset.location_id, ""),
            )
            asset_projections[distribution_id] = asset_projection
            names[distribution_id] = distribution.designation or asset.name

        breadcrumbs_cache: dict[UUID, tuple[tuple[UUID, str], ...]] = {}

        def breadcrumbs(
            distribution_id: UUID,
            visiting: set[UUID],
        ) -> tuple[tuple[UUID, str], ...]:
            cached = breadcrumbs_cache.get(distribution_id)
            if cached is not None:
                return cached
            if distribution_id in visiting:
                raise ValueError("Stored distribution hierarchy contains a cycle")
            record = distributions[distribution_id]
            current: tuple[tuple[UUID, str], ...] = ((distribution_id, names[distribution_id]),)
            if record.parent_distribution_id is None:
                result = current
            else:
                if record.parent_distribution_id not in names:
                    raise ValueError("Stored distribution hierarchy has a missing parent")
                result = (
                    breadcrumbs(
                        record.parent_distribution_id,
                        visiting | {distribution_id},
                    )
                    + current
                )
            breadcrumbs_cache[distribution_id] = result
            return result

        active_distribution_ids = {
            distribution_id
            for distribution_id, component in components.items()
            if component.deleted_at is None
            and distribution_id in asset_projections
            and self._asset_is_visible(asset_projections[distribution_id].record)
        }
        subdistribution_counts: dict[UUID, int] = {}
        for distribution_id in active_distribution_ids:
            parent_id = distributions[distribution_id].parent_distribution_id
            if parent_id is not None:
                subdistribution_counts[parent_id] = subdistribution_counts.get(parent_id, 0) + 1
        device_counts = ElectricalProtectiveDeviceRepository.active_counts(
            self.session,
            assets,
        )

        return {
            distribution_id: DistributionProjection(
                component=components[distribution_id],
                record=distribution,
                asset=asset_projections[distribution_id],
                breadcrumbs=breadcrumbs(distribution_id, set()),
                direct_subdistribution_count=subdistribution_counts.get(distribution_id, 0),
                direct_protective_device_count=device_counts.get(distribution_id, 0),
            )
            for distribution_id, distribution in distributions.items()
            if distribution_id in components and distribution_id in asset_projections
        }

    def _location_paths(self) -> dict[UUID, str]:
        return {
            projection.record.id: projection.path
            for projection in LocationRepository(self.session).tree_locations(include_deleted=True)
        }

    @staticmethod
    def _asset_is_visible(asset: Asset) -> bool:
        return asset.deleted_at is None and asset.status != "retired"

    @classmethod
    def _visible(
        cls,
        projection: DistributionProjection,
        include_deleted: bool,
    ) -> bool:
        return include_deleted or (
            projection.component.deleted_at is None
            and cls._asset_is_visible(projection.asset.record)
        )

    def _validate_sort(self, sort_by: str) -> None:
        if sort_by not in self.sort_fields:
            allowed = ", ".join(sorted(self.sort_fields))
            raise ValueError(f"Unsupported sort field '{sort_by}'. Allowed fields: {allowed}")

    @staticmethod
    def _sort_value(projection: DistributionProjection, sort_by: str) -> Any:
        value: str | datetime | None
        if sort_by == "asset_name":
            value = projection.asset.record.name
        elif sort_by == "jarvis_code":
            value = projection.asset.record.jarvis_code
        elif sort_by == "location_path":
            value = projection.asset.location_path
        elif sort_by in {"created_at", "updated_at"}:
            value = getattr(projection.component, sort_by)
        else:
            value = getattr(projection.record, sort_by)
        if isinstance(value, str):
            return (value == "", value.casefold())
        return (value is None, value or datetime.min)


class ElectricalProtectiveDeviceRepository:
    sort_fields = frozenset(
        {
            "device_type",
            "asset_name",
            "jarvis_code",
            "location_path",
            "row_number",
            "start_position",
            "rated_current_a",
            "created_at",
            "updated_at",
        }
    )

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(
        self,
        device_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> ProtectiveDeviceProjection | None:
        projection = self._projections().get(device_id)
        if projection is None or not self._visible(projection, include_deleted):
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
        device_type: ProtectiveDeviceType | None,
        location_id: UUID | None,
    ) -> PageResult[ProtectiveDeviceProjection]:
        self._validate_sort(sort_by)
        candidates = [
            item for item in self._projections().values() if self._visible(item, include_deleted)
        ]
        if distribution_id is not None:
            candidates = [
                item for item in candidates if item.record.distribution_id == distribution_id
            ]
        if device_type is not None:
            candidates = [
                item for item in candidates if item.record.device_type == device_type.value
            ]
        if location_id is not None:
            candidates = [
                item for item in candidates if item.asset.record.location_id == location_id
            ]
        normalized_search = search.strip().casefold() if search else ""
        if normalized_search:
            candidates = [
                item
                for item in candidates
                if any(
                    normalized_search in value.casefold()
                    for value in (
                        item.asset.record.name,
                        item.asset.record.jarvis_code,
                        item.asset.location_path,
                        item.record.characteristic or "",
                        item.record.rcd_type or "",
                        item.record.fuse_type or "",
                        item.record.spd_type or "",
                        item.record.description or "",
                        item.record.notes or "",
                    )
                )
            ]
        candidates.sort(
            key=lambda item: (self._sort_value(item, sort_by), str(item.component.id)),
            reverse=sort_order == SortOrder.DESC,
        )
        total = len(candidates)
        offset = (page - 1) * page_size
        return PageResult(items=candidates[offset : offset + page_size], total=total)

    def for_distribution(
        self,
        distribution_id: UUID,
        *,
        include_deleted: bool,
    ) -> list[ProtectiveDeviceProjection]:
        return sorted(
            (
                item
                for item in self._projections().values()
                if item.record.distribution_id == distribution_id
                and self._visible(item, include_deleted)
            ),
            key=lambda item: (
                item.record.row_number is None,
                item.record.row_number or 0,
                item.record.start_position is None,
                item.record.start_position or 0,
                item.asset.record.name.casefold(),
                str(item.component.id),
            ),
        )

    def add(self, device: ElectricalProtectiveDevice) -> None:
        self.session.add(device)

    @staticmethod
    def active_counts(session: Session, assets: dict[UUID, Asset]) -> dict[UUID, int]:
        components = {
            item.id: item
            for item in session.exec(select(ElectricalComponent)).all()
            if item.role == ElectricalRole.PROTECTIVE_DEVICE.value and item.deleted_at is None
        }
        counts: dict[UUID, int] = {}
        for device in session.exec(select(ElectricalProtectiveDevice)).all():
            component = components.get(device.id)
            if component is None:
                continue
            asset = assets.get(component.asset_id)
            if asset is None or asset.deleted_at is not None or asset.status == "retired":
                continue
            counts[device.distribution_id] = counts.get(device.distribution_id, 0) + 1
        return counts

    def _projections(self) -> dict[UUID, ProtectiveDeviceProjection]:
        components = {
            item.id: item
            for item in self.session.exec(select(ElectricalComponent)).all()
            if item.role == ElectricalRole.PROTECTIVE_DEVICE.value
        }
        devices = list(self.session.exec(select(ElectricalProtectiveDevice)).all())
        assets = {item.id: item for item in self.session.exec(select(Asset)).all()}
        location_paths = {
            projection.record.id: projection.path
            for projection in LocationRepository(self.session).tree_locations(include_deleted=True)
        }
        distributions = ElectricalDistributionRepository(self.session)._projections()
        projections: dict[UUID, ProtectiveDeviceProjection] = {}
        for device in devices:
            component = components.get(device.id)
            if component is None:
                continue
            asset = assets.get(component.asset_id)
            distribution = distributions.get(device.distribution_id)
            if asset is None or asset.location_id is None or distribution is None:
                raise ValueError("Stored protective device has an invalid reference")
            projections[device.id] = ProtectiveDeviceProjection(
                component=component,
                record=device,
                asset=AssetRoleProjection(
                    record=asset,
                    location_path=location_paths.get(asset.location_id, ""),
                ),
                distribution_name=ElectricalDistributionRepository.display_name(distribution),
            )
        return projections

    @staticmethod
    def _visible(
        projection: ProtectiveDeviceProjection,
        include_deleted: bool,
    ) -> bool:
        return include_deleted or (
            projection.component.deleted_at is None
            and projection.asset.record.deleted_at is None
            and projection.asset.record.status != "retired"
        )

    def _validate_sort(self, sort_by: str) -> None:
        if sort_by not in self.sort_fields:
            allowed = ", ".join(sorted(self.sort_fields))
            raise ValueError(f"Unsupported sort field '{sort_by}'. Allowed fields: {allowed}")

    @staticmethod
    def _sort_value(projection: ProtectiveDeviceProjection, sort_by: str) -> Any:
        value: str | int | float | datetime | None
        if sort_by == "asset_name":
            value = projection.asset.record.name
        elif sort_by == "jarvis_code":
            value = projection.asset.record.jarvis_code
        elif sort_by == "location_path":
            value = projection.asset.location_path
        elif sort_by in {"created_at", "updated_at"}:
            value = getattr(projection.component, sort_by)
        else:
            value = getattr(projection.record, sort_by)
        if isinstance(value, str):
            return (value == "", value.casefold())
        return (value is None, value or 0)


class AvailableElectricalAssetRepository:
    sort_fields = frozenset({"name", "jarvis_code", "location_path"})

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_page(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        sort_by: str,
        sort_order: SortOrder,
        current_component_id: UUID | None,
        role: ElectricalRole,
    ) -> PageResult[AssetRoleProjection]:
        if sort_by not in self.sort_fields:
            allowed = ", ".join(sorted(self.sort_fields))
            raise ValueError(f"Unsupported sort field '{sort_by}'. Allowed fields: {allowed}")
        current_asset_id: UUID | None = None
        if current_component_id is not None:
            current = self.session.get(ElectricalComponent, current_component_id)
            current_asset_id = current.asset_id if current is not None else None
        assigned_asset_ids = {
            item.asset_id
            for item in self.session.exec(select(ElectricalComponent)).all()
            if item.deleted_at is None and item.id != current_component_id
        }
        replaced_asset_ids = {
            item.source_asset_id
            for item in self.session.exec(select(Relationship)).all()
            if item.deleted_at is None and item.relationship_type.casefold() == "replaced_by"
        }
        locations = {
            projection.record.id: projection
            for projection in LocationRepository(self.session).tree_locations(include_deleted=True)
        }
        asset_types = {item.id: item for item in self.session.exec(select(AssetType)).all()}
        candidates: list[AssetRoleProjection] = []
        for asset in self.session.exec(select(Asset)).all():
            if (
                asset.deleted_at is not None
                or asset.status != "active"
                or asset.location_id is None
                or asset.id in replaced_asset_ids
                or (asset.id in assigned_asset_ids and asset.id != current_asset_id)
            ):
                continue
            location = locations.get(asset.location_id)
            if location is None or location.record.deleted_at is not None:
                continue
            if role == ElectricalRole.DISTRIBUTION:
                asset_type = asset_types.get(asset.asset_type_id)
                if (
                    asset_type is None
                    or asset_type.name.strip().casefold() != "elektrische verteilung"
                ):
                    continue
            candidates.append(AssetRoleProjection(record=asset, location_path=location.path))
        normalized_search = search.strip().casefold() if search else ""
        if normalized_search:
            candidates = [
                item
                for item in candidates
                if normalized_search in item.record.name.casefold()
                or normalized_search in item.record.jarvis_code.casefold()
                or normalized_search in item.location_path.casefold()
            ]
        candidates.sort(
            key=lambda item: (
                self._sort_value(item, sort_by),
                str(item.record.id),
            ),
            reverse=sort_order == SortOrder.DESC,
        )
        total = len(candidates)
        offset = (page - 1) * page_size
        return PageResult(items=candidates[offset : offset + page_size], total=total)

    @staticmethod
    def _sort_value(projection: AssetRoleProjection, sort_by: str) -> str:
        if sort_by == "location_path":
            return projection.location_path.casefold()
        return str(getattr(projection.record, sort_by)).casefold()
