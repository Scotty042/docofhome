import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.models.asset_engine import (
    Asset,
    AssetCodeCounter,
    AssetEngineRecord,
    AssetLabelLink,
    AssetType,
    Label,
    Location,
    Product,
    Relationship,
)
from app.models.document_link import DocumentLink
from app.models.electrical import (
    ElectricalAssetPlacement,
    ElectricalCabinetComponent,
    ElectricalComponent,
    ElectricalDistribution,
    ElectricalDistributionArea,
    ElectricalDistributionSection,
    ElectricalMeterPlacement,
    ElectricalProtectiveDevice,
)
from app.repositories.asset_engine import (
    AssetRepository,
    LocationProjection,
    LocationRepository,
    PageResult,
    SoftDeleteRepository,
)
from app.repositories.electrical import ElectricalComponentRepository
from app.repositories.network import NetworkRepository
from app.schemas.asset_engine import (
    AssetDuplicateWrite,
    AssetRead,
    AssetReplacementRead,
    AssetSeriesRead,
    AssetSeriesWrite,
    AssetTypeWrite,
    AssetWrite,
    LabelRead,
    LabelWrite,
    LocationBreadcrumb,
    LocationMoveWrite,
    LocationRead,
    LocationTreeNode,
    LocationType,
    LocationWrite,
    Page,
    ProductWrite,
    ReferenceRead,
    RelationshipRead,
    RelationshipWrite,
    SortOrder,
)


class ResourceNotFoundError(LookupError):
    """Raised when an asset engine resource does not exist or was deleted."""


class InvalidReferenceError(ValueError):
    """Raised when a payload points at a missing or deleted resource."""


class InvalidSortError(ValueError):
    """Raised when a list endpoint receives an unsupported sort field."""


class ResourceConflictError(RuntimeError):
    """Raised when a requested mutation conflicts with immutable history or uniqueness."""


class CrudService[ModelT: AssetEngineRecord, WriteT: BaseModel]:
    """Transaction boundary and common CRUD behavior for simple records."""

    def __init__(self, session: Session, repository: SoftDeleteRepository[ModelT]) -> None:
        self.session = session
        self.repository = repository

    def get(self, record_id: UUID) -> ModelT:
        record = self.repository.get(record_id)
        if record is None:
            raise ResourceNotFoundError
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
    ) -> Page[ModelT]:
        try:
            result = self.repository.list(
                page=page,
                page_size=page_size,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
                include_deleted=include_deleted,
                filters=filters,
            )
        except ValueError as exc:
            raise InvalidSortError(str(exc)) from exc
        return Page.create(result.items, result.total, page, page_size)

    def _create(self, model: type[ModelT], payload: WriteT) -> ModelT:
        record = model(**payload.model_dump(mode="python"))
        self.repository.add(record)
        self._commit()
        return record

    def _update(self, record_id: UUID, payload: WriteT) -> ModelT:
        record = self.get(record_id)
        record.sqlmodel_update(payload.model_dump(mode="python"))
        record.updated_at = datetime.now(UTC)
        self._commit()
        return record

    def delete(self, record_id: UUID) -> None:
        record = self.get(record_id)
        record.deleted_at = datetime.now(UTC)
        record.updated_at = datetime.now(UTC)
        self._commit()

    def _commit(self) -> None:
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise


class AssetTypeService(CrudService[AssetType, AssetTypeWrite]):
    def __init__(self, session: Session) -> None:
        super().__init__(
            session,
            SoftDeleteRepository(
                session,
                AssetType,
                search_fields=("name", "description"),
                sort_fields=frozenset({"name", "created_at", "updated_at"}),
            ),
        )

    def create(self, payload: AssetTypeWrite) -> AssetType:
        prefix = self._available_prefix(payload.name)
        asset_type = AssetType(**payload.model_dump(mode="python"), code_prefix=prefix)
        self.repository.add(asset_type)
        self.session.add(AssetCodeCounter(prefix=prefix, next_value=1))
        self._commit()
        return asset_type

    def update(self, record_id: UUID, payload: AssetTypeWrite) -> AssetType:
        return self._update(record_id, payload)

    def _available_prefix(self, name: str) -> str:
        words = re.findall(r"[A-Z0-9]+", name.upper())
        if not words:
            base = "ASSET"
        elif len(words) == 1:
            base = words[0][:3]
        else:
            base = f"{words[0][:2]}-{words[1][:4]}"
        prefix = base
        suffix = 2
        while self.repository.find_by("code_prefix", prefix, include_deleted=True) is not None:
            marker = f"-{suffix}"
            prefix = f"{base[: 20 - len(marker)]}{marker}"
            suffix += 1
        return prefix


class ProductService(CrudService[Product, ProductWrite]):
    def __init__(self, session: Session) -> None:
        super().__init__(
            session,
            SoftDeleteRepository(
                session,
                Product,
                search_fields=("name", "manufacturer", "model_number", "description"),
                sort_fields=frozenset(
                    {"name", "manufacturer", "model_number", "created_at", "updated_at"}
                ),
            ),
        )
        self.asset_types = AssetTypeService(session)
        self.assets = AssetRepository(session)

    def create(self, payload: ProductWrite) -> Product:
        self._validate(payload)
        return self._create(Product, payload)

    def update(self, record_id: UUID, payload: ProductWrite) -> Product:
        self.get(record_id)
        self._validate(payload)
        if payload.asset_type_id is not None and self.assets.has_product_type_mismatch(
            record_id, payload.asset_type_id
        ):
            raise InvalidReferenceError(
                "Product type conflicts with an active asset using this product"
            )
        return self._update(record_id, payload)

    def _validate(self, payload: ProductWrite) -> None:
        if (
            payload.asset_type_id is not None
            and self.asset_types.repository.get(payload.asset_type_id) is None
        ):
            raise InvalidReferenceError("Asset type does not exist")


class LocationService(CrudService[Location, LocationWrite]):
    def __init__(self, session: Session) -> None:
        self.location_repository = LocationRepository(session)
        super().__init__(session, self.location_repository)

    def get_read(self, record_id: UUID, *, include_deleted: bool = False) -> LocationRead:
        try:
            projection = self.location_repository.get_projection(
                record_id,
                include_deleted=include_deleted,
            )
        except ValueError as exc:
            raise InvalidReferenceError(str(exc)) from exc
        if projection is None:
            raise ResourceNotFoundError
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
        parent_id: UUID | None,
        location_type: LocationType | None,
    ) -> Page[LocationRead]:
        try:
            result = self.location_repository.list_locations(
                page=page,
                page_size=page_size,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
                include_deleted=include_deleted,
                parent_id=parent_id,
                location_type=location_type,
            )
        except ValueError as exc:
            if str(exc).startswith("Unsupported sort field"):
                raise InvalidSortError(str(exc)) from exc
            raise InvalidReferenceError(str(exc)) from exc
        return Page.create(
            [self._to_read(item) for item in result.items],
            result.total,
            page,
            page_size,
        )

    def tree_read(self, *, include_deleted: bool = False) -> list[LocationTreeNode]:
        try:
            projections = self.location_repository.tree_locations(include_deleted=include_deleted)
        except ValueError as exc:
            raise InvalidReferenceError(str(exc)) from exc
        available_ids = {item.record.id for item in projections}
        children: dict[UUID, list[LocationProjection]] = {}
        roots: list[LocationProjection] = []
        for item in projections:
            parent_id = item.record.parent_id
            if parent_id is None or parent_id not in available_ids:
                roots.append(item)
            else:
                children.setdefault(parent_id, []).append(item)

        def build(item: LocationProjection) -> LocationTreeNode:
            return LocationTreeNode(
                **self._read_data(item),
                children=[build(child) for child in children.get(item.record.id, [])],
            )

        return [build(root) for root in roots]

    def create(self, payload: LocationWrite) -> LocationRead:
        location_type = payload.location_type or LocationType.AREA
        self._validate_hierarchy(None, payload.parent_id, location_type)
        record = Location(
            **payload.model_dump(mode="python", exclude={"location_type"}),
            location_type=location_type.value,
        )
        self.location_repository.add(record)
        self._commit()
        return self.get_read(record.id)

    def update(self, record_id: UUID, payload: LocationWrite) -> LocationRead:
        record = self.get(record_id)
        location_type = payload.location_type or LocationType(record.location_type)
        parent_id = (
            payload.parent_id if "parent_id" in payload.model_fields_set else record.parent_id
        )
        self._validate_hierarchy(record_id, parent_id, location_type)
        values = payload.model_dump(mode="python", exclude={"location_type"})
        values["parent_id"] = parent_id
        record.sqlmodel_update(values)
        record.location_type = location_type.value
        record.updated_at = datetime.now(UTC)
        self._commit()
        return self.get_read(record.id)

    def move(self, record_id: UUID, payload: LocationMoveWrite) -> LocationRead:
        record = self.get(record_id)
        location_type = LocationType(record.location_type)
        self._validate_hierarchy(record_id, payload.parent_id, location_type)
        record.parent_id = payload.parent_id
        record.updated_at = datetime.now(UTC)
        self._commit()
        return self.get_read(record.id)

    def delete(self, record_id: UUID) -> None:
        record = self.get(record_id)
        if record.parent_id is None:
            raise ResourceConflictError("The root location cannot be archived")
        if self.location_repository.has_active_children(record_id):
            raise ResourceConflictError("Location has active child locations")
        if self.location_repository.has_active_assets(record_id):
            raise ResourceConflictError("Location has active assigned assets")
        super().delete(record_id)

    def ensure_root(self, name: str, *, rename_existing: bool) -> Location:
        root = self.location_repository.active_root()
        if root is None:
            root = Location(name=name, location_type=LocationType.BUILDING.value)
            self.location_repository.add(root)
        elif rename_existing:
            root.name = name
            root.updated_at = datetime.now(UTC)
        self.session.flush()
        return root

    def _validate_hierarchy(
        self,
        record_id: UUID | None,
        parent_id: UUID | None,
        location_type: LocationType,
    ) -> None:
        if parent_id is None:
            if location_type != LocationType.BUILDING:
                raise InvalidReferenceError("Only the building root may omit a parent location")
            root = self.location_repository.active_root()
            if root is not None and root.id != record_id:
                raise ResourceConflictError("A root location already exists")
            return
        if location_type == LocationType.BUILDING:
            raise ResourceConflictError("Only the root location may use type 'building'")

        current_id: UUID | None = parent_id
        visited: set[UUID] = set()
        while current_id is not None:
            if current_id == record_id or current_id in visited:
                raise ResourceConflictError("Location hierarchy must not contain a cycle")
            visited.add(current_id)
            parent = self.location_repository.get(current_id)
            if parent is None:
                raise InvalidReferenceError("Parent location does not exist")
            current_id = parent.parent_id

    @staticmethod
    def _read_data(projection: LocationProjection) -> dict[str, Any]:
        return {
            **projection.record.model_dump(),
            "breadcrumbs": [
                LocationBreadcrumb(
                    id=item.id,
                    name=item.name,
                    location_type=LocationType(item.location_type),
                )
                for item in projection.breadcrumbs
            ],
            "path": projection.path,
            "direct_asset_count": projection.direct_asset_count,
            "descendant_asset_count": projection.descendant_asset_count,
        }

    @classmethod
    def _to_read(cls, projection: LocationProjection) -> LocationRead:
        return LocationRead.model_validate(cls._read_data(projection))


class LabelService(CrudService[Label, LabelWrite]):
    def __init__(self, session: Session) -> None:
        super().__init__(
            session,
            SoftDeleteRepository(
                session,
                Label,
                search_fields=("name",),
                sort_fields=frozenset({"name", "created_at", "updated_at"}),
            ),
        )

    def create(self, payload: LabelWrite) -> Label:
        normalized_name = self._validate_unique_name(payload.name)
        label = Label(**payload.model_dump(mode="python"), normalized_name=normalized_name)
        self.repository.add(label)
        self._commit()
        return label

    def update(self, record_id: UUID, payload: LabelWrite) -> Label:
        label = self.get(record_id)
        normalized_name = self._validate_unique_name(payload.name, record_id=record_id)
        label.sqlmodel_update(payload.model_dump(mode="python"))
        label.normalized_name = normalized_name
        label.updated_at = datetime.now(UTC)
        self._commit()
        return label

    def _validate_unique_name(self, name: str, *, record_id: UUID | None = None) -> str:
        normalized_name = name.strip().casefold()
        existing = self.repository.find_by("normalized_name", normalized_name, include_deleted=True)
        if existing is not None and existing.id != record_id:
            raise ResourceConflictError("A label with this normalized name already exists")
        return normalized_name


class AssetService(CrudService[Asset, AssetWrite]):
    def __init__(self, session: Session) -> None:
        self.asset_repository = AssetRepository(session)
        super().__init__(session, self.asset_repository)
        self.asset_types = AssetTypeService(session)
        self.products = ProductService(session)
        self.locations = LocationService(session)
        self.labels = LabelService(session)
        self.electrical_components = ElectricalComponentRepository(session)
        self.network = NetworkRepository(session)

    def get_read(self, record_id: UUID) -> AssetRead:
        return self._to_read(self.get(record_id))

    def list_read(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        sort_by: str,
        sort_order: SortOrder,
        include_deleted: bool,
        filters: dict[str, Any],
        label_id: UUID | None,
    ) -> Page[AssetRead]:
        try:
            result: PageResult[Asset] = self.asset_repository.list_assets(
                page=page,
                page_size=page_size,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
                include_deleted=include_deleted,
                filters=filters,
                label_id=label_id,
            )
        except ValueError as exc:
            raise InvalidSortError(str(exc)) from exc
        return Page.create(
            self._to_reads(result.items), result.total, page, page_size
        )

    def create(self, payload: AssetWrite) -> AssetRead:
        self._validate_inventory_number(payload.inventory_number)
        try:
            asset = self._build_asset(payload)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflictError(
                "Die Inventarnummer ist bereits einem anderen Asset zugeordnet"
            ) from exc
        except Exception:
            self.session.rollback()
            raise
        return self._to_read(asset)

    def duplicate(
        self, record_id: UUID, payload: AssetDuplicateWrite
    ) -> AssetRead:
        source = self.get(record_id)
        name = payload.name or f"{source.name} Kopie"
        try:
            duplicate = self._clone_asset(
                source,
                name=name,
                copy_location=payload.copy_location,
                copy_labels=payload.copy_labels,
                copy_electrical_role=payload.copy_electrical_role,
            )
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return self._to_read(duplicate)

    def create_series(
        self, record_id: UUID, payload: AssetSeriesWrite
    ) -> AssetSeriesRead:
        source = self.get(record_id)
        source_component = self.electrical_components.active_for_asset(source.id)
        source_device = (
            self.session.get(ElectricalProtectiveDevice, source_component.id)
            if source_component is not None and source_component.role == "protective_device"
            else None
        )
        product = self.products.repository.get(source.product_id) if source.product_id else None
        asset_type = self.asset_types.repository.get(source.asset_type_id)
        module_width = (
            source_device.module_width
            if source_device is not None and source_device.module_width is not None
            else source.module_width
            if source.module_width is not None
            else product.module_width
            if product is not None and product.din_rail_mount and product.module_width is not None
            else asset_type.module_width
            if asset_type is not None
            else None
        )
        slots: list[tuple[int, int]] = []
        if (
            payload.place_sequentially
            and source_device is not None
            and not payload.copy_electrical_role
        ):
            raise InvalidReferenceError(
                "Für die fortlaufende Platzierung von Schutzgeräten müssen "
                "die technischen Gerätedaten übernommen werden."
            )
        if payload.place_sequentially:
            if module_width is None:
                raise InvalidReferenceError(
                    "Für die fortlaufende Platzierung fehlt eine TE-Breite "
                    "am Schutzgerät, Asset, Asset-Typ oder Produkt."
                )
            assert payload.distribution_id is not None
            assert payload.row_number is not None
            assert payload.start_position is not None
            slots = self._series_slots(
                distribution_id=payload.distribution_id,
                area_id=payload.area_id,
                row_number=payload.row_number,
                start_position=payload.start_position,
                module_width=module_width,
                count=payload.count,
            )

        created: list[Asset] = []
        try:
            for index in range(payload.count):
                number = payload.start_number + index
                try:
                    name = payload.name_template.format(name=source.name, n=number).strip()
                except (KeyError, ValueError, IndexError) as exc:
                    raise InvalidReferenceError(
                        "Das Namensschema kann nicht verarbeitet werden."
                    ) from exc
                if not name or len(name) > 150:
                    raise InvalidReferenceError(
                        f"Das Namensschema erzeugt für Nummer {number} keinen gültigen Namen."
                    )
                clone = self._clone_asset(
                    source,
                    name=name,
                    copy_location=payload.copy_location,
                    copy_labels=payload.copy_labels,
                    copy_electrical_role=payload.copy_electrical_role,
                    technical_distribution_id=(
                        payload.distribution_id if payload.place_sequentially else None
                    ),
                    technical_area_id=(payload.area_id if payload.place_sequentially else None),
                    technical_slot=(slots[index] if slots else None),
                    technical_module_width=module_width,
                )
                if payload.place_sequentially and source_device is None:
                    assert payload.distribution_id is not None
                    row_number, start_position = slots[index]
                    self.session.add(
                        ElectricalAssetPlacement(
                            distribution_id=payload.distribution_id,
                            area_id=payload.area_id,
                            asset_id=clone.id,
                            row_number=row_number,
                            start_position=start_position,
                            module_width=module_width,
                        )
                    )
                created.append(clone)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflictError(
                "Die Serie konnte wegen einer bereits belegten Position oder "
                "Kennung nicht vollständig angelegt werden."
            ) from exc
        except Exception:
            self.session.rollback()
            raise
        return AssetSeriesRead(
            items=[self._to_read(item) for item in created],
            created_count=len(created),
        )

    def update(self, record_id: UUID, payload: AssetWrite) -> AssetRead:
        if self.asset_repository.replacement_for(record_id) is not None:
            raise ResourceConflictError("A replaced asset is immutable historical data")
        self._validate(payload)
        asset = self.get(record_id)
        self._validate_inventory_number(payload.inventory_number, exclude_id=record_id)
        self._validate_electrical_lifecycle(asset, payload)
        self._validate_meter_placement_lifecycle(asset, payload)
        self._validate_din_placement_lifecycle(asset, payload)
        self._validate_network_lifecycle(asset, payload)
        asset.sqlmodel_update(payload.model_dump(mode="python", exclude={"label_ids"}))
        asset.updated_at = datetime.now(UTC)
        try:
            self.asset_repository.replace_labels(asset.id, payload.label_ids)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return self._to_read(asset)

    def delete(self, record_id: UUID) -> None:
        if self.asset_repository.replacement_for(record_id) is not None:
            raise ResourceConflictError("A replaced asset is immutable historical data")
        self._require_archived_electrical_role(record_id)
        self._require_unplaced_meter_asset(record_id)
        self._require_unplaced_din_asset(record_id)
        self._require_archived_network_role(record_id)
        super().delete(record_id)

    def replace(
        self,
        record_id: UUID,
        payload: AssetWrite,
        reason: str | None,
    ) -> AssetReplacementRead:
        archived = self.get(record_id)
        if archived.status == "retired" or self.asset_repository.replacement_for(record_id):
            raise ResourceConflictError("Asset already has an immutable replacement")
        self._require_archived_electrical_role(record_id)
        self._require_unplaced_meter_asset(record_id)
        self._require_unplaced_din_asset(record_id)
        self._require_archived_network_role(record_id)
        if payload.status == "retired":
            raise InvalidReferenceError("A replacement asset must not start as retired")
        self._validate_inventory_number(payload.inventory_number)

        try:
            replacement = self._build_asset(payload)
            archived.status = "retired"
            archived.updated_at = datetime.now(UTC)
            relationship = Relationship(
                source_asset_id=archived.id,
                target_asset_id=replacement.id,
                relationship_type="replaced_by",
                description=reason,
            )
            self.session.add(relationship)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return AssetReplacementRead(
            archived=self._to_read(archived),
            replacement=self._to_read(replacement),
            relationship=RelationshipRead.model_validate(relationship),
        )

    def _clone_asset(
        self,
        source: Asset,
        *,
        name: str,
        copy_location: bool,
        copy_labels: bool,
        copy_electrical_role: bool,
        technical_distribution_id: UUID | None = None,
        technical_area_id: UUID | None = None,
        technical_slot: tuple[int, int] | None = None,
        technical_module_width: int | None = None,
    ) -> Asset:
        asset_type = self.asset_types.repository.get(source.asset_type_id)
        if asset_type is None:
            raise InvalidReferenceError("Der Asset-Typ der Vorlage ist nicht mehr verfügbar.")
        clone = Asset(
            name=name,
            jarvis_code=self.asset_repository.allocate_code(asset_type.code_prefix),
            description=source.description,
            asset_type_id=source.asset_type_id,
            product_id=source.product_id,
            location_id=source.location_id if copy_location else None,
            serial_number=None,
            inventory_number=None,
            module_width=source.module_width,
            status="active",
        )
        self.session.add(clone)
        self.session.flush()
        if copy_labels:
            self.asset_repository.replace_labels(
                clone.id, [label.id for label in self.asset_repository.labels_for(source.id)]
            )
        self._copy_document_links(source.id, clone.id)
        if copy_electrical_role:
            source_component = self.electrical_components.active_for_asset(source.id)
            if source_component is not None:
                if source_component.role != "protective_device":
                    raise ResourceConflictError(
                        "Verteilungsrollen können nicht automatisch dupliziert werden. "
                        "Deaktiviere „Elektro-Rolle kopieren“ oder lege die "
                        "Verteilung bewusst neu an."
                    )
                source_device = self.session.get(
                    ElectricalProtectiveDevice, source_component.id
                )
                if source_device is None:
                    raise InvalidReferenceError(
                        "Die Schutzgeräte-Rolle der Vorlage ist unvollständig."
                    )
                component = ElectricalComponent(asset_id=clone.id, role="protective_device")
                self.session.add(component)
                self.session.flush()
                row_number = technical_slot[0] if technical_slot else None
                start_position = technical_slot[1] if technical_slot else None
                self.session.add(
                    ElectricalProtectiveDevice(
                        id=component.id,
                        distribution_id=technical_distribution_id or source_device.distribution_id,
                        area_id=technical_area_id if technical_slot else None,
                        device_type=source_device.device_type,
                        row_number=row_number,
                        start_position=start_position,
                        module_width=(
                            technical_module_width
                            if technical_module_width is not None
                            else source_device.module_width
                        ),
                        rated_current_a=source_device.rated_current_a,
                        residual_current_ma=source_device.residual_current_ma,
                        characteristic=source_device.characteristic,
                        poles=source_device.poles,
                        breaking_capacity_ka=source_device.breaking_capacity_ka,
                        rcd_type=source_device.rcd_type,
                        fuse_type=source_device.fuse_type,
                        spd_type=source_device.spd_type,
                        description=source_device.description,
                        notes=source_device.notes,
                    )
                )
        return clone

    def _copy_document_links(self, source_id: UUID, target_id: UUID) -> None:
        links = self.session.exec(
            select(DocumentLink).where(
                DocumentLink.target_type == "asset",
                DocumentLink.target_id == source_id,
                col(DocumentLink.deleted_at).is_(None),
            )
        ).all()
        for link in links:
            self.session.add(
                DocumentLink(
                    target_type="asset",
                    target_id=target_id,
                    document_path=link.document_path,
                    document_name=link.document_name,
                    document_etag=link.document_etag,
                )
            )

    def _series_slots(
        self,
        *,
        distribution_id: UUID,
        area_id: UUID | None,
        row_number: int,
        start_position: int,
        module_width: int,
        count: int,
    ) -> list[tuple[int, int]]:
        distribution = self.session.get(ElectricalDistribution, distribution_id)
        role = self.session.get(ElectricalComponent, distribution_id)
        if distribution is None or role is None or role.deleted_at is not None:
            raise InvalidReferenceError("Die gewählte Verteilung ist nicht aktiv.")

        area: ElectricalDistributionArea | None = None
        if distribution.layout_mode == "sections":
            if area_id is None:
                raise InvalidReferenceError(
                    "Für die Feld-/Bereichsaufteilung muss ein DIN-Bereich gewählt werden."
                )
            area = self.session.get(ElectricalDistributionArea, area_id)
            if area is None or area.deleted_at is not None or area.area_type != "device_rows":
                raise InvalidReferenceError(
                    "Der gewählte Bereich ist kein aktiver Gerätebereich."
                )
            section = self.session.get(ElectricalDistributionSection, area.section_id)
            if (
                section is None
                or section.deleted_at is not None
                or section.distribution_id != distribution_id
            ):
                raise InvalidReferenceError(
                    "Der gewählte Bereich gehört nicht zur angegebenen Verteilung."
                )
            rows = area.rows
            modules_per_row = area.modules_per_row
        else:
            if area_id is not None:
                raise InvalidReferenceError(
                    "Die einfache Reihenaufteilung verwendet keinen DIN-Bereich."
                )
            rows = distribution.rows
            modules_per_row = distribution.modules_per_row

        if rows is None or modules_per_row is None:
            raise InvalidReferenceError(
                "In der Verteilung fehlen Reihenanzahl oder Teilungseinheiten."
            )

        occupied: dict[int, list[tuple[int, int]]] = {}
        device_statement = (
            select(ElectricalProtectiveDevice)
            .join(
                ElectricalComponent,
                ElectricalComponent.id == ElectricalProtectiveDevice.id,
            )
            .where(
                ElectricalProtectiveDevice.distribution_id == distribution_id,
                col(ElectricalComponent.deleted_at).is_(None),
            )
        )
        device_statement = (
            device_statement.where(ElectricalProtectiveDevice.area_id == area.id)
            if area is not None
            else device_statement.where(col(ElectricalProtectiveDevice.area_id).is_(None))
        )
        for device in self.session.exec(device_statement).all():
            if (
                device.row_number is not None
                and device.start_position is not None
                and device.module_width is not None
            ):
                occupied.setdefault(device.row_number, []).append(
                    (device.start_position, device.start_position + device.module_width - 1)
                )

        asset_statement = select(ElectricalAssetPlacement).where(
            ElectricalAssetPlacement.distribution_id == distribution_id,
            col(ElectricalAssetPlacement.deleted_at).is_(None),
        )
        asset_statement = (
            asset_statement.where(ElectricalAssetPlacement.area_id == area.id)
            if area is not None
            else asset_statement.where(col(ElectricalAssetPlacement.area_id).is_(None))
        )
        for placement in self.session.exec(asset_statement).all():
            occupied.setdefault(placement.row_number, []).append(
                (placement.start_position, placement.start_position + placement.module_width - 1)
            )

        cabinet_statement = select(ElectricalCabinetComponent).where(
            ElectricalCabinetComponent.distribution_id == distribution_id,
            col(ElectricalCabinetComponent.deleted_at).is_(None),
        )
        cabinet_statement = (
            cabinet_statement.where(ElectricalCabinetComponent.area_id == area.id)
            if area is not None
            else cabinet_statement.where(col(ElectricalCabinetComponent.area_id).is_(None))
        )
        for component in self.session.exec(cabinet_statement).all():
            occupied.setdefault(component.row_number, []).append(
                (
                    component.start_position,
                    component.start_position + component.module_width - 1,
                )
            )

        slots: list[tuple[int, int]] = []
        current_row = row_number
        current_position = start_position
        while len(slots) < count:
            if current_row > rows:
                raise ResourceConflictError(
                    f"Für {count} Kopien stehen ab Reihe {row_number}, TE {start_position} "
                    "nicht genügend freie Teilungseinheiten zur Verfügung."
                )
            if current_position + module_width - 1 > modules_per_row:
                current_row += 1
                current_position = 1
                continue
            candidate_end = current_position + module_width - 1
            conflicts = any(
                current_position <= end and candidate_end >= start
                for start, end in occupied.get(current_row, [])
            )
            if conflicts:
                current_position += 1
                continue
            slots.append((current_row, current_position))
            occupied.setdefault(current_row, []).append((current_position, candidate_end))
            current_position = candidate_end + 1
        return slots

    def next_inventory_number(self) -> str:
        all_assets = self.asset_repository.all(include_deleted=True)
        values = {
            int(asset.inventory_number)
            for asset in all_assets
            if asset.inventory_number and asset.inventory_number.isdecimal()
        }
        widths = [
            len(asset.inventory_number)
            for asset in all_assets
            if asset.inventory_number and asset.inventory_number.isdecimal()
        ]
        candidate = 1
        while candidate in values:
            candidate += 1
        return str(candidate).zfill(max(widths, default=4))

    def _validate_inventory_number(
        self,
        value: str | None,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        if value is None:
            return
        normalized = value.casefold()
        for asset in self.asset_repository.all(include_deleted=True):
            if (
                asset.inventory_number
                and asset.inventory_number.casefold() == normalized
                and asset.id != exclude_id
            ):
                raise ResourceConflictError(
                    "Die Inventarnummer ist bereits einem aktiven oder archivierten "
                    "Asset zugeordnet"
                )

    def _validate_electrical_lifecycle(self, asset: Asset, payload: AssetWrite) -> None:
        if self.electrical_components.active_for_asset(asset.id) is None:
            return
        if payload.status != "active" or payload.location_id != asset.location_id:
            raise ResourceConflictError(
                "Archive the active electrical role before changing Asset status or location"
            )

    def _validate_meter_placement_lifecycle(
        self,
        asset: Asset,
        payload: AssetWrite,
    ) -> None:
        if not self._has_active_meter_asset_placement(asset.id):
            return
        if payload.status != "active" or payload.asset_type_id != asset.asset_type_id:
            raise ResourceConflictError(
                "Remove the meter from the cabinet layout before changing the Asset status or type"
            )

    def _validate_din_placement_lifecycle(
        self, asset: Asset, payload: AssetWrite
    ) -> None:
        if not self._has_active_din_asset_placement(asset.id):
            return
        if (
            payload.status != "active"
            or payload.product_id != asset.product_id
            or payload.asset_type_id != asset.asset_type_id
            or payload.module_width != asset.module_width
        ):
            raise ResourceConflictError(
                "Entferne das DIN-Hutschienengerät zuerst aus dem Zählerschrank, "
                "bevor Status, Produkt, Asset-Typ oder DIN-Breite geändert werden."
            )

    def _validate_network_lifecycle(self, asset: Asset, payload: AssetWrite) -> None:
        if self.network.active_device_for_asset(asset.id) is None:
            return
        if payload.status != "active":
            raise ResourceConflictError(
                "Archive the active network role before changing the Asset status"
            )

    def _require_archived_electrical_role(self, asset_id: UUID) -> None:
        if self.electrical_components.active_for_asset(asset_id) is not None:
            raise ResourceConflictError(
                "Archive the active electrical role before deleting or replacing the Asset"
            )

    def _has_active_meter_asset_placement(self, asset_id: UUID) -> bool:
        return self.session.exec(
            select(ElectricalMeterPlacement).where(
                ElectricalMeterPlacement.asset_id == asset_id,
                col(ElectricalMeterPlacement.deleted_at).is_(None),
            )
        ).first() is not None

    def _require_unplaced_meter_asset(self, asset_id: UUID) -> None:
        if self._has_active_meter_asset_placement(asset_id):
            raise ResourceConflictError(
                "Remove the meter from the cabinet layout before deleting or replacing the Asset"
            )

    def _has_active_din_asset_placement(self, asset_id: UUID) -> bool:
        return self.session.exec(
            select(ElectricalAssetPlacement).where(
                ElectricalAssetPlacement.asset_id == asset_id,
                col(ElectricalAssetPlacement.deleted_at).is_(None),
            )
        ).first() is not None

    def _require_unplaced_din_asset(self, asset_id: UUID) -> None:
        if self._has_active_din_asset_placement(asset_id):
            raise ResourceConflictError(
                "Entferne das DIN-Hutschienengerät vor dem Löschen oder Ersetzen "
                "aus dem Zählerschrank."
            )

    def _require_archived_network_role(self, asset_id: UUID) -> None:
        if self.network.active_device_for_asset(asset_id) is not None:
            raise ResourceConflictError(
                "Archive the active network role before deleting or replacing the Asset"
            )

    def _build_asset(self, payload: AssetWrite) -> Asset:
        asset_type = self._validate(payload)
        data = payload.model_dump(mode="python", exclude={"label_ids"})
        asset = Asset(
            **data,
            jarvis_code=self.asset_repository.allocate_code(asset_type.code_prefix),
        )
        self.repository.add(asset)
        self.session.flush()
        self.asset_repository.replace_labels(asset.id, payload.label_ids)
        return asset

    def _validate(self, payload: AssetWrite) -> AssetType:
        asset_type = self.asset_types.repository.get(payload.asset_type_id)
        if asset_type is None:
            raise InvalidReferenceError("Asset type does not exist")
        if payload.product_id is not None:
            product = self.products.repository.get(payload.product_id)
            if product is None:
                raise InvalidReferenceError("Product does not exist")
            if product.asset_type_id is not None and product.asset_type_id != payload.asset_type_id:
                raise InvalidReferenceError("Product type does not match the asset type")
        if (
            payload.location_id is not None
            and self.locations.repository.get(payload.location_id) is None
        ):
            raise InvalidReferenceError("Location does not exist")
        for label_id in payload.label_ids:
            if self.labels.repository.get(label_id) is None:
                raise InvalidReferenceError("Label does not exist")
        return asset_type

    def _to_reads(self, assets: list[Asset]) -> list[AssetRead]:
        if not assets:
            return []
        asset_ids = [asset.id for asset in assets]
        type_ids = {asset.asset_type_id for asset in assets}
        product_ids = {asset.product_id for asset in assets if asset.product_id is not None}
        location_ids = {asset.location_id for asset in assets if asset.location_id is not None}
        asset_types = {
            item.id: item
            for item in self.session.exec(
                select(AssetType).where(col(AssetType.id).in_(type_ids))
            ).all()
        }
        products = {
            item.id: item
            for item in self.session.exec(
                select(Product).where(col(Product.id).in_(product_ids))
            ).all()
        } if product_ids else {}
        locations = {
            item.id: item
            for item in self.session.exec(
                select(Location).where(col(Location.id).in_(location_ids))
            ).all()
        } if location_ids else {}
        labels_by_asset: dict[UUID, list[Label]] = {asset_id: [] for asset_id in asset_ids}
        label_rows = self.session.exec(
            select(AssetLabelLink.asset_id, Label)
            .join(Label, col(Label.id) == AssetLabelLink.label_id)
            .where(col(AssetLabelLink.asset_id).in_(asset_ids))
            .order_by(col(Label.name), col(Label.id))
        ).all()
        for asset_id, label in label_rows:
            labels_by_asset.setdefault(asset_id, []).append(label)
        return [
            self._to_read_data(
                asset,
                asset_type=asset_types.get(asset.asset_type_id),
                product=products.get(asset.product_id) if asset.product_id else None,
                location=locations.get(asset.location_id) if asset.location_id else None,
                labels=labels_by_asset.get(asset.id, []),
            )
            for asset in assets
        ]

    def _to_read(self, asset: Asset) -> AssetRead:
        asset_type = self.asset_types.repository.get(asset.asset_type_id, include_deleted=True)
        if asset_type is None:
            raise InvalidReferenceError("Stored asset type does not exist")
        product = (
            self.products.repository.get(asset.product_id, include_deleted=True)
            if asset.product_id is not None
            else None
        )
        location = (
            self.locations.repository.get(asset.location_id, include_deleted=True)
            if asset.location_id is not None
            else None
        )
        return self._to_read_data(
            asset,
            asset_type=asset_type,
            product=product,
            location=location,
            labels=self.asset_repository.labels_for(asset.id),
        )

    @staticmethod
    def _to_read_data(
        asset: Asset,
        *,
        asset_type: AssetType | None,
        product: Product | None,
        location: Location | None,
        labels: list[Label],
    ) -> AssetRead:
        if asset_type is None:
            raise InvalidReferenceError("Stored asset type does not exist")
        return AssetRead.model_validate(
            {
                **asset.model_dump(),
                "asset_type": ReferenceRead(id=asset_type.id, name=asset_type.name),
                "product": ReferenceRead(id=product.id, name=product.name) if product else None,
                "product_image_url": product.image_url if product else None,
                "effective_module_width": (
                    asset.module_width
                    if asset.module_width is not None
                    else product.module_width
                    if (
                        product is not None
                        and product.din_rail_mount
                        and product.module_width is not None
                    )
                    else asset_type.module_width
                ),
                "location": ReferenceRead(id=location.id, name=location.name) if location else None,
                "labels": [LabelRead.model_validate(label) for label in labels],
            }
        )


class RelationshipService(CrudService[Relationship, RelationshipWrite]):
    replacement_type = "replaced_by"

    def __init__(self, session: Session) -> None:
        super().__init__(
            session,
            SoftDeleteRepository(
                session,
                Relationship,
                search_fields=("relationship_type", "description"),
                sort_fields=frozenset({"relationship_type", "created_at", "updated_at"}),
            ),
        )
        self.assets = AssetRepository(session)

    def create(self, payload: RelationshipWrite) -> Relationship:
        self._prevent_replacement_mutation(payload.relationship_type)
        self._validate(payload)
        return self._create(Relationship, payload)

    def update(self, record_id: UUID, payload: RelationshipWrite) -> Relationship:
        current = self.get(record_id)
        self._prevent_replacement_mutation(current.relationship_type)
        self._prevent_replacement_mutation(payload.relationship_type)
        self._validate(payload)
        return self._update(record_id, payload)

    def delete(self, record_id: UUID) -> None:
        current = self.get(record_id)
        self._prevent_replacement_mutation(current.relationship_type)
        super().delete(record_id)

    def _prevent_replacement_mutation(self, relationship_type: str) -> None:
        if relationship_type.casefold() == self.replacement_type:
            raise ResourceConflictError(
                "Replacement relationships are immutable and created by the replacement workflow"
            )

    def _validate(self, payload: RelationshipWrite) -> None:
        if self.assets.get(payload.source_asset_id) is None:
            raise InvalidReferenceError("Source asset does not exist")
        if self.assets.get(payload.target_asset_id) is None:
            raise InvalidReferenceError("Target asset does not exist")
