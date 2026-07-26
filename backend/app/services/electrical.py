from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.models.asset_engine import Asset, AssetType, Relationship
from app.models.electrical import (
    ElectricalAssetPlacement,
    ElectricalCabinetComponent,
    ElectricalComponent,
    ElectricalDistribution,
    ElectricalProtectiveDevice,
)
from app.repositories.asset_engine import LocationRepository
from app.repositories.electrical import (
    AssetRoleProjection,
    AvailableElectricalAssetRepository,
    DistributionProjection,
    ElectricalComponentRepository,
    ElectricalDistributionRepository,
    ElectricalProtectiveDeviceRepository,
    ProtectiveDeviceProjection,
)
from app.repositories.electrical_circuit import ElectricalCircuitRepository
from app.schemas.asset_engine import Page, SortOrder
from app.schemas.electrical import (
    AvailableAssetRead,
    DistributionBreadcrumbRead,
    DistributionDetailRead,
    DistributionMoveWrite,
    DistributionRead,
    DistributionTreeNode,
    DistributionType,
    DistributionWrite,
    ElectricalAssetRead,
    ElectricalRole,
    ProtectiveDeviceRead,
    ProtectiveDeviceType,
    ProtectiveDeviceWrite,
)
from app.schemas.electrical_topology import ElectricalPhase
from app.services.din_width import effective_asset_module_width


class ElectricalNotFoundError(Exception):
    pass


class ElectricalValidationError(Exception):
    pass


class ElectricalConflictError(Exception):
    pass


class ElectricalSortError(Exception):
    pass


class ElectricalServiceBase:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.components = ElectricalComponentRepository(session)
        self.locations = LocationRepository(session)

    def _validate_asset(
        self,
        asset_id: UUID,
        *,
        current_component_id: UUID | None = None,
        required_asset_type: str | None = None,
    ) -> Asset:
        asset = self.session.get(Asset, asset_id)
        if asset is None:
            raise ElectricalValidationError("Asset does not exist")
        if asset.deleted_at is not None or asset.status != "active":
            raise ElectricalConflictError("Electrical roles require an active asset")
        if required_asset_type is not None:
            asset_type = self.session.get(AssetType, asset.asset_type_id)
            if (
                asset_type is None
                or asset_type.name.strip().casefold() != required_asset_type.casefold()
            ):
                raise ElectricalValidationError(
                    f"Für diese Rolle ist ein Asset vom Typ „{required_asset_type}“ erforderlich"
                )
        replacement = self.session.exec(
            select(Relationship).where(
                Relationship.source_asset_id == asset_id,
                col(Relationship.deleted_at).is_(None),
                Relationship.relationship_type == "replaced_by",
            )
        ).first()
        if replacement is not None:
            raise ElectricalConflictError("A replaced asset cannot receive a new role")
        if asset.location_id is None:
            raise ElectricalValidationError("Electrical roles require an assigned location")
        location = self.locations.get(asset.location_id)
        if location is None:
            raise ElectricalConflictError("The asset location is archived or missing")
        assigned = self.components.active_for_asset(asset_id)
        if assigned is not None and assigned.id != current_component_id:
            raise ElectricalConflictError("Asset already has an active electrical role")
        return asset

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ElectricalConflictError(
                "The electrical change conflicts with existing data"
            ) from exc
        except Exception:
            self.session.rollback()
            raise

    def _rollback(self) -> None:
        self.session.rollback()


class ElectricalDistributionService(ElectricalServiceBase):
    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.repository = ElectricalDistributionRepository(session)
        self.devices = ElectricalProtectiveDeviceRepository(session)
        self.circuits = ElectricalCircuitRepository(session)

    def get_read(
        self,
        distribution_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> DistributionDetailRead:
        projection = self.repository.get(
            distribution_id,
            include_deleted=include_deleted,
        )
        if projection is None:
            raise ElectricalNotFoundError
        devices = self.devices.for_distribution(
            distribution_id,
            include_deleted=False,
        )
        return DistributionDetailRead.model_validate(
            {
                **self._read_data(projection),
                "protective_devices": [self._device_read(item) for item in devices],
            }
        )

    def list_read(
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
    ) -> Page[DistributionRead]:
        try:
            result = self.repository.list_page(
                page=page,
                page_size=page_size,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
                include_deleted=include_deleted,
                distribution_type=distribution_type,
                parent_distribution_id=parent_distribution_id,
                location_id=location_id,
            )
        except ValueError as exc:
            raise ElectricalSortError(str(exc)) from exc
        return Page.create(
            [DistributionRead.model_validate(self._read_data(item)) for item in result.items],
            result.total,
            page,
            page_size,
        )

    def tree_read(self, *, include_deleted: bool = False) -> list[DistributionTreeNode]:
        try:
            projections = self.repository.tree(include_deleted=include_deleted)
        except ValueError as exc:
            raise ElectricalValidationError(str(exc)) from exc
        by_id = {item.component.id: item for item in projections}
        children: dict[UUID, list[DistributionProjection]] = {}
        roots: list[DistributionProjection] = []
        for item in projections:
            parent_id = item.record.parent_distribution_id
            if parent_id is None or parent_id not in by_id:
                roots.append(item)
            else:
                children.setdefault(parent_id, []).append(item)

        def build(item: DistributionProjection) -> DistributionTreeNode:
            return DistributionTreeNode.model_validate(
                {
                    **self._read_data(item),
                    "children": [build(child) for child in children.get(item.component.id, [])],
                }
            )

        return [build(root) for root in roots]

    def create(self, payload: DistributionWrite) -> DistributionDetailRead:
        self._validate_asset(payload.asset_id, required_asset_type="Elektrische Verteilung")
        self._validate_parent(
            None,
            payload.parent_distribution_id,
            payload.distribution_type,
        )
        component = ElectricalComponent(
            asset_id=payload.asset_id,
            role=ElectricalRole.DISTRIBUTION.value,
        )
        distribution = ElectricalDistribution(
            id=component.id,
            **payload.model_dump(
                mode="python",
                exclude={"asset_id", "distribution_type"},
            ),
            distribution_type=payload.distribution_type.value,
        )
        try:
            self.components.add(component)
            self.repository.add(distribution)
            self._commit()
        except Exception:
            self._rollback()
            raise
        return self.get_read(component.id)

    def update(
        self,
        distribution_id: UUID,
        payload: DistributionWrite,
    ) -> DistributionDetailRead:
        projection = self.repository.get(distribution_id)
        if projection is None:
            raise ElectricalNotFoundError
        if payload.asset_id != projection.component.asset_id:
            raise ElectricalConflictError("Electrical role asset identity is immutable")
        asset = self._validate_asset(
            projection.component.asset_id,
            current_component_id=distribution_id,
            required_asset_type="Elektrische Verteilung",
        )
        self._validate_parent(
            distribution_id,
            payload.parent_distribution_id,
            payload.distribution_type,
        )
        self._validate_device_locations(distribution_id, asset.location_id)
        self._validate_layout_transition(
            distribution_id,
            current_mode=projection.record.layout_mode,
            new_mode=payload.layout_mode.value,
        )
        self._validate_device_capacity(
            distribution_id,
            rows=payload.rows,
            modules_per_row=payload.modules_per_row,
        )
        values = payload.model_dump(
            mode="python",
            exclude={"asset_id", "distribution_type"},
        )
        projection.record.sqlmodel_update(values)
        projection.record.distribution_type = payload.distribution_type.value
        projection.component.updated_at = datetime.now(UTC)
        self._commit()
        return self.get_read(distribution_id)

    def move(
        self,
        distribution_id: UUID,
        payload: DistributionMoveWrite,
    ) -> DistributionDetailRead:
        projection = self.repository.get(distribution_id)
        if projection is None:
            raise ElectricalNotFoundError
        distribution_type = (
            DistributionType.MAIN
            if payload.parent_distribution_id is None
            else DistributionType.SUB
        )
        self._validate_parent(
            distribution_id,
            payload.parent_distribution_id,
            distribution_type,
        )
        projection.record.parent_distribution_id = payload.parent_distribution_id
        projection.record.distribution_type = distribution_type.value
        projection.component.updated_at = datetime.now(UTC)
        self._commit()
        return self.get_read(distribution_id)

    def delete(self, distribution_id: UUID) -> None:
        projection = self.repository.get(distribution_id)
        if projection is None:
            raise ElectricalNotFoundError
        if self.repository.has_active_children(distribution_id):
            raise ElectricalConflictError("Distribution has active subdistributions")
        if self.repository.has_active_devices(distribution_id):
            raise ElectricalConflictError("Distribution has active protective devices")
        if self.circuits.has_active_for_distribution(distribution_id):
            raise ElectricalConflictError("Distribution has active circuits")
        if self.session.exec(
            select(ElectricalCabinetComponent).where(
                ElectricalCabinetComponent.distribution_id == distribution_id,
                col(ElectricalCabinetComponent.deleted_at).is_(None),
            )
        ).first() is not None:
            raise ElectricalConflictError(
                "Entferne zuerst die aktiven Schrankkomponenten aus der Verteilung"
            )
        if self.session.exec(
            select(ElectricalAssetPlacement).where(
                ElectricalAssetPlacement.distribution_id == distribution_id,
                col(ElectricalAssetPlacement.deleted_at).is_(None),
            )
        ).first() is not None:
            raise ElectricalConflictError(
                "Entferne zuerst die platzierten DIN-Hutschienengeräte aus der Verteilung"
            )
        now = datetime.now(UTC)
        projection.component.deleted_at = now
        projection.component.updated_at = now
        self._commit()

    def _validate_parent(
        self,
        distribution_id: UUID | None,
        parent_id: UUID | None,
        distribution_type: DistributionType,
    ) -> None:
        if parent_id is None:
            if distribution_type != DistributionType.MAIN:
                raise ElectricalValidationError("A distribution without a parent must be main")
            return
        if distribution_type != DistributionType.SUB:
            raise ElectricalValidationError("A distribution with a parent must be sub")
        if parent_id == distribution_id:
            raise ElectricalConflictError("A distribution cannot be its own parent")
        parent = self.repository.get(parent_id)
        if parent is None:
            raise ElectricalValidationError("Parent distribution does not exist or is archived")
        if distribution_id is not None:
            try:
                descendants = self.repository.descendant_ids(distribution_id)
            except ValueError as exc:
                raise ElectricalConflictError(str(exc)) from exc
            if parent_id in descendants:
                raise ElectricalConflictError("Distribution hierarchy must not contain a cycle")

    def _validate_layout_transition(
        self,
        distribution_id: UUID,
        *,
        current_mode: str,
        new_mode: str,
    ) -> None:
        if current_mode == new_mode:
            return
        if new_mode == "sections":
            for projection in self.devices.for_distribution(
                distribution_id, include_deleted=False
            ):
                record = projection.record
                if record.area_id is None and record.row_number is not None:
                    raise ElectricalConflictError(
                        "Vor dem Wechsel zur Feld-/Bereichsaufteilung müssen die "
                        "Schutzgeräte aus der einfachen Reihenaufteilung entfernt werden."
                    )
            rows_asset = self.session.exec(
                select(ElectricalAssetPlacement).where(
                    ElectricalAssetPlacement.distribution_id == distribution_id,
                    col(ElectricalAssetPlacement.area_id).is_(None),
                    col(ElectricalAssetPlacement.deleted_at).is_(None),
                )
            ).first()
            rows_component = self.session.exec(
                select(ElectricalCabinetComponent).where(
                    ElectricalCabinetComponent.distribution_id == distribution_id,
                    col(ElectricalCabinetComponent.area_id).is_(None),
                    col(ElectricalCabinetComponent.deleted_at).is_(None),
                )
            ).first()
            if rows_asset is not None or rows_component is not None:
                raise ElectricalConflictError(
                    "Vor dem Wechsel zur Feld-/Bereichsaufteilung müssen alle "
                    "DIN-Geräte und Schrankkomponenten neu zugeordnet werden."
                )
        else:
            section_asset = self.session.exec(
                select(ElectricalAssetPlacement).where(
                    ElectricalAssetPlacement.distribution_id == distribution_id,
                    col(ElectricalAssetPlacement.area_id).is_not(None),
                    col(ElectricalAssetPlacement.deleted_at).is_(None),
                )
            ).first()
            section_component = self.session.exec(
                select(ElectricalCabinetComponent).where(
                    ElectricalCabinetComponent.distribution_id == distribution_id,
                    col(ElectricalCabinetComponent.area_id).is_not(None),
                    col(ElectricalCabinetComponent.deleted_at).is_(None),
                )
            ).first()
            if section_asset is not None or section_component is not None:
                raise ElectricalConflictError(
                    "Vor dem Wechsel zur einfachen Reihenaufteilung müssen alle "
                    "Bereichsplatzierungen entfernt werden."
                )
            for projection in self.devices.for_distribution(
                distribution_id, include_deleted=False
            ):
                if projection.record.area_id is not None:
                    raise ElectricalConflictError(
                        "Vor dem Wechsel zur einfachen Reihenaufteilung müssen die "
                        "Schutzgeräte aus ihren DIN-Bereichen entfernt werden."
                    )

    def _validate_device_capacity(
        self,
        distribution_id: UUID,
        *,
        rows: int | None,
        modules_per_row: int | None,
    ) -> None:
        placements: list[tuple[str, int, int, int]] = []
        for device in self.devices.for_distribution(
            distribution_id,
            include_deleted=False,
        ):
            record = device.record
            if (
                record.area_id is None
                and record.row_number is not None
                and record.start_position is not None
                and record.module_width is not None
            ):
                placements.append(
                    (
                        device.asset.record.name,
                        record.row_number,
                        record.start_position,
                        record.module_width,
                    )
                )
        for placement in self.session.exec(
            select(ElectricalAssetPlacement).where(
                ElectricalAssetPlacement.distribution_id == distribution_id,
                col(ElectricalAssetPlacement.area_id).is_(None),
                col(ElectricalAssetPlacement.deleted_at).is_(None),
            )
        ).all():
            placements.append(
                (
                    "DIN-Hutschienengerät",
                    placement.row_number,
                    placement.start_position,
                    placement.module_width,
                )
            )
        for component in self.session.exec(
            select(ElectricalCabinetComponent).where(
                ElectricalCabinetComponent.distribution_id == distribution_id,
                col(ElectricalCabinetComponent.area_id).is_(None),
                col(ElectricalCabinetComponent.deleted_at).is_(None),
            )
        ).all():
            placements.append(
                (
                    component.name,
                    component.row_number,
                    component.start_position,
                    component.module_width,
                )
            )
        for name, row_number, start_position, module_width in placements:
            if rows is not None and row_number > rows:
                raise ElectricalConflictError(
                    f"{name} verwendet Reihe {row_number}; verfügbar sind nur {rows} Reihen."
                )
            end_position = start_position + module_width - 1
            if modules_per_row is not None and end_position > modules_per_row:
                raise ElectricalConflictError(
                    f"{name} endet bei TE {end_position}; verfügbar sind nur "
                    f"{modules_per_row} TE."
                )

    def _validate_device_locations(
        self,
        distribution_id: UUID,
        location_id: UUID | None,
    ) -> None:
        for device in self.devices.for_distribution(
            distribution_id,
            include_deleted=False,
        ):
            if device.asset.record.location_id != location_id:
                raise ElectricalConflictError(
                    "Distribution location must match all assigned protective devices"
                )

    def _read_data(self, projection: DistributionProjection) -> dict[str, object]:
        return {
            **projection.component.model_dump(),
            **projection.record.model_dump(exclude={"id"}),
            "asset": self._asset_read(projection.asset),
            "display_name": self.repository.display_name(projection),
            "breadcrumbs": [
                DistributionBreadcrumbRead(id=item_id, display_name=name)
                for item_id, name in projection.breadcrumbs
            ],
            "direct_subdistribution_count": projection.direct_subdistribution_count,
            "direct_protective_device_count": projection.direct_protective_device_count,
        }

    def _asset_read(self, projection: AssetRoleProjection) -> ElectricalAssetRead:
        asset = projection.record
        if asset.location_id is None:
            raise ElectricalValidationError("Stored electrical asset has no location")
        return ElectricalAssetRead(
            id=asset.id,
            name=asset.name,
            jarvis_code=asset.jarvis_code,
            location_id=asset.location_id,
            location_path=projection.location_path,
            status=asset.status,
            effective_module_width=effective_asset_module_width(self.session, asset),
        )

    def _device_read(self, projection: ProtectiveDeviceProjection) -> ProtectiveDeviceRead:
        return ElectricalProtectiveDeviceService(self.session)._to_read(projection)


class ElectricalProtectiveDeviceService(ElectricalServiceBase):
    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.repository = ElectricalProtectiveDeviceRepository(session)
        self.distributions = ElectricalDistributionRepository(session)
        self.circuits = ElectricalCircuitRepository(session)

    def get_read(
        self,
        device_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> ProtectiveDeviceRead:
        projection = self.repository.get(device_id, include_deleted=include_deleted)
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
        device_type: ProtectiveDeviceType | None,
        location_id: UUID | None,
    ) -> Page[ProtectiveDeviceRead]:
        try:
            result = self.repository.list_page(
                page=page,
                page_size=page_size,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
                include_deleted=include_deleted,
                distribution_id=distribution_id,
                device_type=device_type,
                location_id=location_id,
            )
        except ValueError as exc:
            raise ElectricalSortError(str(exc)) from exc
        return Page.create(
            [self._to_read(item) for item in result.items],
            result.total,
            page,
            page_size,
        )

    def create(self, payload: ProtectiveDeviceWrite) -> ProtectiveDeviceRead:
        asset = self._validate_asset(payload.asset_id)
        distribution = self._validate_distribution(payload.distribution_id)
        self._validate_location(asset, distribution)
        self._validate_group_links(
            payload.distribution_id,
            None,
            payload.assigned_rcd_id,
            payload.neutral_rail_id,
        )
        module_width = self._resolved_module_width(
            asset,
            payload.module_width,
            placement_requested=payload.row_number is not None,
        )
        self._validate_position(
            payload,
            distribution,
            current_device_id=None,
            module_width=module_width,
        )
        component = ElectricalComponent(
            asset_id=payload.asset_id,
            role=ElectricalRole.PROTECTIVE_DEVICE.value,
        )
        device_values = payload.model_dump(
            mode="python", exclude={"asset_id", "device_type"}
        )
        device_values["module_width"] = module_width
        device = ElectricalProtectiveDevice(
            id=component.id,
            **device_values,
            device_type=payload.device_type.value,
        )
        try:
            self.components.add(component)
            self.repository.add(device)
            self._commit()
        except Exception:
            self._rollback()
            raise
        return self.get_read(component.id)

    def update(
        self,
        device_id: UUID,
        payload: ProtectiveDeviceWrite,
    ) -> ProtectiveDeviceRead:
        projection = self.repository.get(device_id)
        if projection is None:
            raise ElectricalNotFoundError
        if payload.asset_id != projection.component.asset_id:
            raise ElectricalConflictError("Electrical role asset identity is immutable")
        asset = self._validate_asset(
            projection.component.asset_id,
            current_component_id=device_id,
        )
        if (
            payload.distribution_id != projection.record.distribution_id
            and self.circuits.has_active_for_device(device_id)
        ):
            raise ElectricalConflictError(
                "Protective device with active circuits cannot change distribution"
            )
        distribution = self._validate_distribution(payload.distribution_id)
        self._validate_location(asset, distribution)
        self._validate_group_links(
            payload.distribution_id,
            device_id,
            payload.assigned_rcd_id,
            payload.neutral_rail_id,
        )
        module_width = self._resolved_module_width(
            asset,
            payload.module_width,
            placement_requested=payload.row_number is not None,
            legacy_width=projection.record.module_width,
        )
        self._validate_position(
            payload,
            distribution,
            current_device_id=device_id,
            module_width=module_width,
        )
        values = payload.model_dump(
            mode="python", exclude={"asset_id", "device_type"}
        )
        values["module_width"] = module_width
        projection.record.sqlmodel_update(values)
        projection.record.device_type = payload.device_type.value
        projection.component.updated_at = datetime.now(UTC)
        self._commit()
        return self.get_read(device_id)

    def delete(self, device_id: UUID) -> None:
        projection = self.repository.get(device_id)
        if projection is None:
            raise ElectricalNotFoundError
        if self.circuits.has_active_for_device(device_id):
            raise ElectricalConflictError("Protective device has active circuits")
        if self.session.exec(
            select(ElectricalCabinetComponent).where(
                ElectricalCabinetComponent.linked_rcd_device_id == device_id,
                col(ElectricalCabinetComponent.deleted_at).is_(None),
            )
        ).first() is not None:
            raise ElectricalConflictError(
                "Der FI/RCD ist noch einer Sammel- oder N-Schiene zugeordnet."
            )
        if self.session.exec(
            select(ElectricalProtectiveDevice).where(
                ElectricalProtectiveDevice.assigned_rcd_id == device_id
            )
        ).first() is not None:
            raise ElectricalConflictError(
                "Der FI/RCD ist noch anderen Schutzgeräten zugeordnet."
            )
        now = datetime.now(UTC)
        projection.component.deleted_at = now
        projection.component.updated_at = now
        self._commit()

    def _validate_distribution(self, distribution_id: UUID) -> DistributionProjection:
        distribution = self.distributions.get(distribution_id)
        if distribution is None:
            raise ElectricalValidationError("Target distribution does not exist or is archived")
        return distribution

    @staticmethod
    def _validate_location(asset: Asset, distribution: DistributionProjection) -> None:
        if asset.location_id != distribution.asset.record.location_id:
            raise ElectricalConflictError(
                "Protective device and distribution must use the same location"
            )

    def _validate_group_links(
        self,
        distribution_id: UUID,
        device_id: UUID | None,
        assigned_rcd_id: UUID | None,
        neutral_rail_id: UUID | None,
    ) -> None:
        if assigned_rcd_id is not None:
            if assigned_rcd_id == device_id:
                raise ElectricalValidationError(
                    "Ein FI kann nicht sich selbst als vorgeschalteten FI verwenden."
                )
            rcd = self.repository.get(assigned_rcd_id)
            if (
                rcd is None
                or rcd.record.distribution_id != distribution_id
                or rcd.record.device_type != ProtectiveDeviceType.RCD.value
            ):
                raise ElectricalValidationError(
                    "Der ausgewählte FI/RCD ist in dieser Verteilung nicht verfügbar."
                )
        if neutral_rail_id is None:
            return
        rail = self.session.get(ElectricalCabinetComponent, neutral_rail_id)
        if (
            rail is None
            or rail.deleted_at is not None
            or rail.distribution_id != distribution_id
            or rail.component_type != "neutral_rail"
        ):
            raise ElectricalValidationError(
                "Die ausgewählte N-Schiene ist in dieser Verteilung nicht verfügbar."
            )
        if assigned_rcd_id is not None and rail.linked_rcd_device_id not in (None, assigned_rcd_id):
            raise ElectricalValidationError(
                "Die N-Schiene ist einem anderen FI/RCD zugeordnet."
            )

    def _device_name(self, device_id: UUID | None) -> str | None:
        if device_id is None:
            return None
        projection = self.repository.get(device_id)
        return projection.asset.record.name if projection is not None else None

    @staticmethod
    def _busbar_phase_pattern(component: ElectricalCabinetComponent) -> list[ElectricalPhase]:
        enabled = [
            phase
            for phase, selected in (
                (ElectricalPhase.L1, component.phase_l1),
                (ElectricalPhase.L2, component.phase_l2),
                (ElectricalPhase.L3, component.phase_l3),
            )
            if selected
        ]
        if not enabled:
            return []
        standard = [ElectricalPhase.L1, ElectricalPhase.L2, ElectricalPhase.L3]
        start = (
            ElectricalPhase(component.start_phase)
            if component.start_phase in {item.value for item in standard}
            else enabled[0]
        )
        start_index = standard.index(start)
        rotated = standard[start_index:] + standard[:start_index]
        return [phase for phase in rotated if phase in enabled]

    def _group_read_data(
        self, projection: ProtectiveDeviceProjection
    ) -> dict[str, object]:
        record = projection.record
        warnings: list[str] = []
        components = list(
            self.session.exec(
                select(ElectricalCabinetComponent).where(
                    ElectricalCabinetComponent.distribution_id == record.distribution_id,
                    col(ElectricalCabinetComponent.deleted_at).is_(None),
                )
            ).all()
        )
        busbars: list[ElectricalCabinetComponent] = []
        if record.row_number is not None and record.start_position is not None:
            for component in components:
                if (
                    component.component_type != "busbar"
                    or component.area_id != record.area_id
                    or component.row_number != record.row_number
                ):
                    continue
                end = component.start_position + component.module_width - 1
                if component.start_position <= record.start_position <= end:
                    busbars.append(component)
        busbars.sort(key=lambda item: (item.module_width, item.start_position, item.name.casefold()))
        busbar = busbars[0] if busbars else None
        if len(busbars) > 1:
            warnings.append("Mehrere Sammelschienen überdecken die Position dieses Geräts.")

        effective_rcd_id = record.assigned_rcd_id or (busbar.linked_rcd_device_id if busbar else None)
        if (
            record.assigned_rcd_id is not None
            and busbar is not None
            and busbar.linked_rcd_device_id is not None
            and record.assigned_rcd_id != busbar.linked_rcd_device_id
        ):
            warnings.append("Manuelle FI-Zuordnung weicht von der Sammelschiene ab.")

        explicit_neutral_rail = (
            self.session.get(ElectricalCabinetComponent, record.neutral_rail_id)
            if record.neutral_rail_id is not None
            else None
        )
        neutral_rail = explicit_neutral_rail
        if neutral_rail is None and effective_rcd_id is not None:
            matches = [
                item for item in components
                if item.component_type == "neutral_rail"
                and item.linked_rcd_device_id == effective_rcd_id
            ]
            matches.sort(key=lambda item: (item.area_id is None, item.row_number, item.name.casefold()))
            neutral_rail = matches[0] if matches else None
            if len(matches) > 1:
                warnings.append("Mehrere N-Schienen sind demselben FI/RCD zugeordnet.")
        if (
            neutral_rail is not None
            and effective_rcd_id is not None
            and neutral_rail.linked_rcd_device_id not in (None, effective_rcd_id)
        ):
            warnings.append("Die N-Schiene gehört zu einem anderen FI/RCD.")
        if (
            effective_rcd_id is not None
            and neutral_rail is None
            and record.device_type in {"fuse", "mcb", "rcbo"}
            and (record.poles or 1) <= 2
        ):
            warnings.append("Für die FI-Gruppe ist noch keine N-Schiene dokumentiert.")

        phases: list[ElectricalPhase] = []
        if busbar is not None and record.start_position is not None:
            pattern = self._busbar_phase_pattern(busbar)
            if pattern:
                offset = record.start_position - busbar.start_position
                count = min(3, record.poles or 1)
                phases = [pattern[(offset + index) % len(pattern)] for index in range(count)]
                if (
                    record.module_width is not None
                    and record.start_position + record.module_width - 1
                    > busbar.start_position + busbar.module_width - 1
                ):
                    warnings.append("Das Gerät ragt über das Ende der Sammelschiene hinaus.")

        return {
            "assigned_rcd_id": record.assigned_rcd_id,
            "assigned_rcd_name": self._device_name(record.assigned_rcd_id),
            "neutral_rail_id": record.neutral_rail_id,
            "neutral_rail_name": explicit_neutral_rail.name if explicit_neutral_rail else None,
            "effective_rcd_id": effective_rcd_id,
            "effective_rcd_name": self._device_name(effective_rcd_id),
            "effective_neutral_rail_id": neutral_rail.id if neutral_rail else None,
            "effective_neutral_rail_name": neutral_rail.name if neutral_rail else None,
            "busbar_component_id": busbar.id if busbar else None,
            "busbar_component_name": busbar.name if busbar else None,
            "calculated_phases": [phase.value for phase in phases],
            "group_warnings": warnings,
        }

    def _resolved_module_width(
        self,
        asset: Asset,
        requested_width: int | None,
        *,
        placement_requested: bool,
        legacy_width: int | None = None,
    ) -> int | None:
        if not placement_requested:
            return None
        inherited_width = effective_asset_module_width(self.session, asset)
        if inherited_width is not None:
            if requested_width is not None and requested_width != inherited_width:
                raise ElectricalValidationError(
                    "Die Schutzgerätebreite muss der am Asset, Asset-Typ oder Produkt "
                    "hinterlegten DIN-Breite entsprechen."
                )
            return inherited_width
        if legacy_width is not None and requested_width in (None, legacy_width):
            return legacy_width
        if requested_width is not None:
            return requested_width
        raise ElectricalValidationError(
            "Das Schutzgeräte-Asset benötigt eine DIN-Breite am Asset, Asset-Typ "
            "oder Produkt, bevor es auf der Hutschiene platziert werden kann."
        )

    def _validate_position(
        self,
        payload: ProtectiveDeviceWrite,
        distribution: DistributionProjection,
        *,
        current_device_id: UUID | None,
        module_width: int | None,
    ) -> None:
        if payload.row_number is None:
            return
        if payload.start_position is None or module_width is None:
            raise ElectricalValidationError("Protective-device position is incomplete")
        if distribution.record.rows is not None and payload.row_number > distribution.record.rows:
            raise ElectricalConflictError("Row exceeds the distribution capacity")
        end_position = payload.start_position + module_width - 1
        if (
            distribution.record.modules_per_row is not None
            and end_position > distribution.record.modules_per_row
        ):
            raise ElectricalConflictError("Module position exceeds the distribution capacity")
        for other in self.repository.for_distribution(
            distribution.component.id,
            include_deleted=False,
        ):
            if other.component.id == current_device_id:
                continue
            if (
                other.record.row_number != payload.row_number
                or other.record.start_position is None
                or other.record.module_width is None
            ):
                continue
            other_end = other.record.start_position + other.record.module_width - 1
            if payload.start_position <= other_end and end_position >= other.record.start_position:
                raise ElectricalConflictError("Protective-device module positions must not overlap")

    def _to_read(self, projection: ProtectiveDeviceProjection) -> ProtectiveDeviceRead:
        asset = projection.asset.record
        if asset.location_id is None:
            raise ElectricalValidationError("Stored electrical asset has no location")
        return ProtectiveDeviceRead.model_validate(
            {
                **projection.component.model_dump(),
                **projection.record.model_dump(exclude={"id"}),
                "asset": ElectricalAssetRead(
                    id=asset.id,
                    name=asset.name,
                    jarvis_code=asset.jarvis_code,
                    location_id=asset.location_id,
                    location_path=projection.asset.location_path,
                    status=asset.status,
                    effective_module_width=effective_asset_module_width(
                        self.session, asset
                    ),
                ),
                "distribution_name": projection.distribution_name,
                **self._group_read_data(projection),
            }
        )


class AvailableElectricalAssetService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = AvailableElectricalAssetRepository(session)

    def list_read(
        self,
        *,
        role: ElectricalRole,
        page: int,
        page_size: int,
        search: str | None,
        sort_by: str,
        sort_order: SortOrder,
        current_component_id: UUID | None,
    ) -> Page[AvailableAssetRead]:
        if role not in (ElectricalRole.DISTRIBUTION, ElectricalRole.PROTECTIVE_DEVICE):
            raise ElectricalValidationError("Unsupported electrical role")
        try:
            result = self.repository.list_page(
                page=page,
                page_size=page_size,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
                current_component_id=current_component_id,
                role=role,
            )
        except ValueError as exc:
            raise ElectricalSortError(str(exc)) from exc
        return Page.create(
            [
                AvailableAssetRead(
                    id=item.record.id,
                    name=item.record.name,
                    jarvis_code=item.record.jarvis_code,
                    location_id=item.record.location_id,
                    location_path=item.location_path,
                    effective_module_width=effective_asset_module_width(
                        self.session, item.record
                    ),
                )
                for item in result.items
                if item.record.location_id is not None
            ],
            result.total,
            page,
            page_size,
        )
