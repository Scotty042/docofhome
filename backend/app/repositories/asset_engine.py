from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, update
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, col, select

from app.models.asset_engine import (
    Asset,
    AssetCodeCounter,
    AssetEngineRecord,
    AssetLabelLink,
    Label,
    Location,
    Relationship,
)
from app.schemas.asset_engine import LocationType, SortOrder


@dataclass(frozen=True)
class PageResult[ItemT]:
    items: list[ItemT]
    total: int


@dataclass(frozen=True)
class LocationProjection:
    record: Location
    breadcrumbs: tuple[Location, ...]
    path: str
    direct_asset_count: int
    descendant_asset_count: int


class SoftDeleteRepository[ModelT: AssetEngineRecord]:
    """Reusable persistence operations for soft-deletable asset records."""

    def __init__(
        self,
        session: Session,
        model: type[ModelT],
        *,
        search_fields: tuple[str, ...],
        sort_fields: frozenset[str],
    ) -> None:
        self.session = session
        self.model = model
        self.search_fields = search_fields
        self.sort_fields = sort_fields

    def get(self, record_id: UUID, *, include_deleted: bool = False) -> ModelT | None:
        record = self.session.get(self.model, record_id)
        if record is None:
            return None
        if not include_deleted and record.deleted_at is not None:
            return None
        return record

    def list(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        sort_by: str,
        sort_order: SortOrder,
        include_deleted: bool,
        filters: dict[str, Any] | None = None,
        conditions: list[ColumnElement[bool]] | None = None,
    ) -> PageResult[ModelT]:
        if sort_by not in self.sort_fields:
            allowed = ", ".join(sorted(self.sort_fields))
            raise ValueError(f"Unsupported sort field '{sort_by}'. Allowed fields: {allowed}")

        clauses: list[ColumnElement[bool]] = list(conditions or [])
        deleted_column = col(self.model.deleted_at)
        if not include_deleted:
            clauses.append(deleted_column.is_(None))
        for field_name, value in (filters or {}).items():
            if value is not None:
                clauses.append(getattr(self.model, field_name) == value)
        if search:
            pattern = f"%{search.strip()}%"
            if pattern != "%%":
                search_clauses = (
                    col(getattr(self.model, field)).ilike(pattern) for field in self.search_fields
                )
                clauses.append(or_(*search_clauses))

        count_statement = select(func.count()).select_from(self.model).where(*clauses)
        total = int(self.session.exec(count_statement).one())
        sort_column = getattr(self.model, sort_by)
        order_expression = sort_column.desc() if sort_order == SortOrder.DESC else sort_column.asc()
        statement = (
            select(self.model)
            .where(*clauses)
            .order_by(order_expression, col(self.model.id).asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return PageResult(items=list(self.session.exec(statement).all()), total=total)

    def add(self, record: ModelT) -> None:
        self.session.add(record)

    def find_by(
        self,
        field_name: str,
        value: object,
        *,
        include_deleted: bool = False,
    ) -> ModelT | None:
        statement = select(self.model).where(getattr(self.model, field_name) == value)
        if not include_deleted:
            statement = statement.where(col(self.model.deleted_at).is_(None))
        return self.session.exec(statement).first()


class LocationRepository(SoftDeleteRepository[Location]):
    def __init__(self, session: Session) -> None:
        super().__init__(
            session,
            Location,
            search_fields=("name", "short_name", "description", "notes"),
            sort_fields=frozenset(
                {
                    "name",
                    "location_type",
                    "path",
                    "sort_order",
                    "created_at",
                    "updated_at",
                }
            ),
        )

    def active_root(self) -> Location | None:
        statement = select(Location).where(
            col(Location.parent_id).is_(None),
            col(Location.deleted_at).is_(None),
        )
        return self.session.exec(statement).one_or_none()

    def get_projection(
        self,
        record_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> LocationProjection | None:
        record = self.get(record_id, include_deleted=include_deleted)
        if record is None:
            return None
        return self._projections()[record.id]

    def list_locations(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        sort_by: str,
        sort_order: SortOrder,
        include_deleted: bool,
        parent_id: UUID | None,
        location_type: LocationType | None,
    ) -> PageResult[LocationProjection]:
        if sort_by not in self.sort_fields:
            allowed = ", ".join(sorted(self.sort_fields))
            raise ValueError(f"Unsupported sort field '{sort_by}'. Allowed fields: {allowed}")

        candidates = list(self._projections().values())
        if not include_deleted:
            candidates = [item for item in candidates if item.record.deleted_at is None]
        if parent_id is not None:
            candidates = [item for item in candidates if item.record.parent_id == parent_id]
        if location_type is not None:
            candidates = [
                item for item in candidates if item.record.location_type == location_type.value
            ]
        normalized_search = search.strip().casefold() if search else ""
        if normalized_search:
            candidates = [
                item
                for item in candidates
                if normalized_search in item.record.name.casefold()
                or normalized_search in item.path.casefold()
            ]

        candidates.sort(
            key=lambda item: (self._sort_value(item, sort_by), str(item.record.id)),
            reverse=sort_order == SortOrder.DESC,
        )
        total = len(candidates)
        offset = (page - 1) * page_size
        return PageResult(items=candidates[offset : offset + page_size], total=total)

    def tree_locations(self, *, include_deleted: bool = False) -> list[LocationProjection]:
        projections = list(self._projections().values())
        if not include_deleted:
            projections = [item for item in projections if item.record.deleted_at is None]
        return sorted(
            projections,
            key=lambda item: (
                item.record.sort_order is None,
                item.record.sort_order or 0,
                item.record.name.casefold(),
                str(item.record.id),
            ),
        )

    def has_active_children(self, record_id: UUID) -> bool:
        statement = (
            select(func.count())
            .select_from(Location)
            .where(
                Location.parent_id == record_id,
                col(Location.deleted_at).is_(None),
            )
        )
        return bool(self.session.exec(statement).one())

    def has_active_assets(self, record_id: UUID) -> bool:
        statement = (
            select(func.count())
            .select_from(Asset)
            .where(
                Asset.location_id == record_id,
                col(Asset.deleted_at).is_(None),
            )
        )
        return bool(self.session.exec(statement).one())

    def _projections(self) -> dict[UUID, LocationProjection]:
        locations = list(self.session.exec(select(Location).order_by(col(Location.id))).all())
        by_id = {location.id: location for location in locations}
        direct_counts = self._direct_asset_counts()
        active_children: dict[UUID, list[Location]] = {}
        for location in locations:
            if location.parent_id is not None and location.deleted_at is None:
                active_children.setdefault(location.parent_id, []).append(location)

        descendant_cache: dict[UUID, int] = {}

        def descendant_count(location_id: UUID, visiting: set[UUID]) -> int:
            cached = descendant_cache.get(location_id)
            if cached is not None:
                return cached
            if location_id in visiting:
                raise ValueError("Stored location hierarchy contains a cycle")
            total = 0
            for child in active_children.get(location_id, []):
                total += direct_counts.get(child.id, 0)
                total += descendant_count(child.id, visiting | {location_id})
            descendant_cache[location_id] = total
            return total

        projections: dict[UUID, LocationProjection] = {}
        for location in locations:
            breadcrumbs = self._breadcrumbs(location, by_id)
            projections[location.id] = LocationProjection(
                record=location,
                breadcrumbs=breadcrumbs,
                path=" / ".join(item.name for item in breadcrumbs),
                direct_asset_count=direct_counts.get(location.id, 0),
                descendant_asset_count=descendant_count(location.id, set()),
            )
        return projections

    def _direct_asset_counts(self) -> dict[UUID, int]:
        statement = (
            select(Asset.location_id, func.count())
            .where(
                col(Asset.location_id).is_not(None),
                col(Asset.deleted_at).is_(None),
            )
            .group_by(col(Asset.location_id))
        )
        rows = self.session.exec(statement).all()
        return {location_id: int(count) for location_id, count in rows if location_id is not None}

    @staticmethod
    def _breadcrumbs(
        location: Location,
        by_id: dict[UUID, Location],
    ) -> tuple[Location, ...]:
        result: list[Location] = []
        visited: set[UUID] = set()
        current: Location | None = location
        while current is not None:
            if current.id in visited:
                raise ValueError("Stored location hierarchy contains a cycle")
            visited.add(current.id)
            result.append(current)
            if current.parent_id is None:
                break
            current = by_id.get(current.parent_id)
            if current is None:
                raise ValueError("Stored location hierarchy contains a missing parent")
        result.reverse()
        return tuple(result)

    @staticmethod
    def _sort_value(projection: LocationProjection, sort_by: str) -> Any:
        if sort_by == "path":
            return projection.path.casefold()
        value = getattr(projection.record, sort_by)
        if isinstance(value, str):
            return value.casefold()
        if value is None:
            return 1_000_001
        return value


class AssetRepository(SoftDeleteRepository[Asset]):
    def __init__(self, session: Session) -> None:
        super().__init__(
            session,
            Asset,
            search_fields=(
                "name",
                "jarvis_code",
                "description",
                "serial_number",
                "inventory_number",
            ),
            sort_fields=frozenset(
                {
                    "name",
                    "jarvis_code",
                    "status",
                    "serial_number",
                    "inventory_number",
                    "created_at",
                    "updated_at",
                }
            ),
        )

    def allocate_code(self, prefix: str) -> str:
        statement = (
            update(AssetCodeCounter)
            .where(col(AssetCodeCounter.prefix) == prefix)
            .values(next_value=col(AssetCodeCounter.next_value) + 1)
            .returning(col(AssetCodeCounter.next_value))
        )
        next_value = self.session.execute(statement).scalar_one_or_none()
        if next_value is not None:
            return f"{prefix}-{next_value - 1:03d}"

        # Older seeded asset types could exist without a matching counter row.
        # Reconstruct the next value from persisted codes instead of failing with
        # NoResultFound and surfacing an HTTP 500 during asset creation.
        marker = f"{prefix}-"
        highest = 0
        codes = self.session.exec(select(Asset.jarvis_code)).all()
        for code in codes:
            if not code.startswith(marker):
                continue
            suffix = code[len(marker):]
            if suffix.isdigit():
                highest = max(highest, int(suffix))
        number = highest + 1
        self.session.add(AssetCodeCounter(prefix=prefix, next_value=number + 1))
        self.session.flush()
        return f"{prefix}-{number:03d}"

    def all(self, *, include_deleted: bool = False) -> list[Asset]:
        statement = select(Asset)
        if not include_deleted:
            statement = statement.where(col(Asset.deleted_at).is_(None))
        return list(self.session.exec(statement).all())

    def has_product_type_mismatch(self, product_id: UUID, asset_type_id: UUID) -> bool:
        statement = (
            select(func.count())
            .select_from(Asset)
            .where(
                Asset.product_id == product_id,
                col(Asset.deleted_at).is_(None),
                Asset.asset_type_id != asset_type_id,
            )
        )
        return bool(self.session.exec(statement).one())

    def replacement_for(self, asset_id: UUID) -> Relationship | None:
        statement = select(Relationship).where(
            Relationship.source_asset_id == asset_id,
            Relationship.relationship_type == "replaced_by",
            col(Relationship.deleted_at).is_(None),
        )
        return self.session.exec(statement).first()

    def list_assets(
        self,
        *,
        label_id: UUID | None,
        **kwargs: Any,
    ) -> PageResult[Asset]:
        conditions: list[ColumnElement[bool]] = []
        if label_id is not None:
            label_assets = select(AssetLabelLink.asset_id).where(
                AssetLabelLink.label_id == label_id
            )
            conditions.append(col(Asset.id).in_(label_assets))
        return self.list(conditions=conditions, **kwargs)

    def labels_for(self, asset_id: UUID) -> list[Label]:
        statement = (
            select(Label)
            .join(AssetLabelLink, col(Label.id) == AssetLabelLink.label_id)
            .where(AssetLabelLink.asset_id == asset_id)
            .order_by(col(Label.name), col(Label.id))
        )
        return list(self.session.exec(statement).all())

    def replace_labels(self, asset_id: UUID, label_ids: list[UUID]) -> None:
        existing = self.session.exec(
            select(AssetLabelLink).where(AssetLabelLink.asset_id == asset_id)
        ).all()
        for link in existing:
            self.session.delete(link)
        for label_id in label_ids:
            self.session.add(AssetLabelLink(asset_id=asset_id, label_id=label_id))
