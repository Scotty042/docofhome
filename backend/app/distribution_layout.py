from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.models.asset_engine import Asset, AssetType, Location, Product
from app.models.consumption import ConsumptionMeter, ConsumptionReading
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
from app.models.electrical_topology import ElectricalConnection
from app.models.home_assistant import HomeAssistantAssetLink
from app.repositories.asset_engine import LocationRepository
from app.schemas.electrical import ProtectiveDeviceWrite
from app.schemas.electrical_layout import (
    DistributionAreaRead,
    DistributionAreaSide,
    DistributionAreaType,
    DistributionAreaWidth,
    DistributionAreaWrite,
    DistributionLayoutMode,
    DistributionSectionRead,
    DistributionSectionWrite,
    ElectricalAssetPlacementRead,
    ElectricalAssetPlacementWrite,
    ElectricalCabinetComponentRead,
    ElectricalCabinetComponentType,
    ElectricalCabinetComponentWrite,
    ElectricalLiveValueRead,
    ElectricalMeterPlacementRead,
    ElectricalMeterPlacementWrite,
)
from app.schemas.electrical_topology import ElectricalPhase
from app.schemas.home_assistant import (
    HomeAssistantEntityRead,
    HomeAssistantEntityRole,
    HomeAssistantObjectType,
)
from app.services.electrical import (
    ElectricalConflictError,
    ElectricalNotFoundError,
    ElectricalValidationError,
)
from app.services.din_width import effective_asset_module_width
from app.services.home_assistant import (
    HomeAssistantConfigurationError,
    HomeAssistantConnectionError,
    HomeAssistantService,
)


class ElectricalLayoutService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def read(self, distribution_id: UUID) -> list[DistributionSectionRead]:
        self._structured_distribution(distribution_id)
        areas = self._areas()
        return [
            self._section_read(
                section,
                [area for area in areas if area.section_id == section.id],
            )
            for section in self._sections(distribution_id)
        ]

    def create_section(
        self,
        distribution_id: UUID,
        payload: DistributionSectionWrite,
    ) -> DistributionSectionRead:
        self._structured_distribution(distribution_id)
        section = ElectricalDistributionSection(
            distribution_id=distribution_id,
            name=payload.name,
            position=payload.position,
            description=payload.description,
        )
        self.session.add(section)
        self._commit("A field with this position already exists")
        return self._section_read(section, [])

    def update_section(
        self,
        distribution_id: UUID,
        section_id: UUID,
        payload: DistributionSectionWrite,
    ) -> DistributionSectionRead:
        self._structured_distribution(distribution_id)
        section = self._section(section_id, distribution_id)
        section.name = payload.name
        section.position = payload.position
        section.description = payload.description
        section.updated_at = datetime.now(UTC)
        self._commit("A field with this position already exists")
        areas = [area for area in self._areas() if area.section_id == section.id]
        return self._section_read(section, areas)

    def archive_section(self, distribution_id: UUID, section_id: UUID) -> None:
        self._structured_distribution(distribution_id)
        section = self._section(section_id, distribution_id)
        if any(area.section_id == section.id for area in self._areas()):
            raise ElectricalConflictError("The field still contains active areas")
        now = datetime.now(UTC)
        section.deleted_at = now
        section.updated_at = now
        self._commit()

    def create_area(
        self,
        distribution_id: UUID,
        section_id: UUID,
        payload: DistributionAreaWrite,
    ) -> DistributionAreaRead:
        self._structured_distribution(distribution_id)
        self._section(section_id, distribution_id)
        self._validate_area_level(section_id, payload, exclude_id=None)
        area = ElectricalDistributionArea(
            section_id=section_id,
            name=payload.name,
            area_type=payload.area_type.value,
            position=payload.position,
            rows=payload.rows,
            modules_per_row=payload.modules_per_row,
            width=payload.width.value,
            side=payload.side.value if payload.side is not None else None,
            description=payload.description,
        )
        self.session.add(area)
        self._commit(self._area_conflict_message(payload))
        return self._area_read(area)

    def update_area(
        self,
        distribution_id: UUID,
        area_id: UUID,
        payload: DistributionAreaWrite,
    ) -> DistributionAreaRead:
        self._structured_distribution(distribution_id)
        area = self._area(area_id, distribution_id)
        active_devices = self._active_devices(area.id)
        active_assets = self._active_asset_placements(area.id)
        active_components = self._active_cabinet_components(area.id)
        active_meters = self._active_meter_placements(area.id)
        has_rail_devices = active_devices or active_assets or active_components
        if (
            has_rail_devices
            and payload.area_type != DistributionAreaType.DEVICE_ROWS
        ):
            raise ElectricalConflictError(
                "Der Bereich enthält noch Hutschienengeräte und muss ein Gerätebereich bleiben"
            )
        if active_meters and payload.area_type != DistributionAreaType.METER:
            raise ElectricalConflictError(
                "Der Bereich enthält noch Zähler und muss ein Zählerfeld bleiben"
            )
        self._validate_area_capacity(area.id, payload.rows, payload.modules_per_row)
        self._validate_area_level(area.section_id, payload, exclude_id=area.id)
        area.name = payload.name
        area.area_type = payload.area_type.value
        area.position = payload.position
        area.rows = payload.rows
        area.modules_per_row = payload.modules_per_row
        area.width = payload.width.value
        area.side = payload.side.value if payload.side is not None else None
        area.description = payload.description
        area.updated_at = datetime.now(UTC)
        self._commit(self._area_conflict_message(payload))
        return self._area_read(area)

    def archive_area(self, distribution_id: UUID, area_id: UUID) -> None:
        self._structured_distribution(distribution_id)
        area = self._area(area_id, distribution_id)
        if (
            self._active_devices(area.id)
            or self._active_asset_placements(area.id)
            or self._active_cabinet_components(area.id)
        ):
            raise ElectricalConflictError(
                "Der Bereich enthält noch aktive Hutschienengeräte"
            )
        if self._active_meter_placements(area.id):
            raise ElectricalConflictError("Das Zählerfeld enthält noch aktive Zähler")
        now = datetime.now(UTC)
        area.deleted_at = now
        area.updated_at = now
        self._commit()

    def list_asset_placements(
        self, distribution_id: UUID
    ) -> list[ElectricalAssetPlacementRead]:
        self._distribution(distribution_id)
        statement = (
            select(ElectricalAssetPlacement)
            .where(
                ElectricalAssetPlacement.distribution_id == distribution_id,
                col(ElectricalAssetPlacement.deleted_at).is_(None),
            )
            .order_by(
                col(ElectricalAssetPlacement.area_id),
                col(ElectricalAssetPlacement.row_number),
                col(ElectricalAssetPlacement.start_position),
            )
        )
        placements = list(self.session.exec(statement).all())
        if not placements:
            return []

        asset_ids = {item.asset_id for item in placements}
        area_ids = {item.area_id for item in placements if item.area_id is not None}
        areas = {
            item.id: item
            for item in self.session.exec(
                select(ElectricalDistributionArea).where(
                    col(ElectricalDistributionArea.id).in_(area_ids)
                )
            ).all()
        } if area_ids else {}
        assets = {
            item.id: item
            for item in self.session.exec(
                select(Asset).where(col(Asset.id).in_(asset_ids))
            ).all()
        }
        product_ids = {
            item.product_id for item in assets.values() if item.product_id is not None
        }
        products = {
            item.id: item
            for item in self.session.exec(
                select(Product).where(col(Product.id).in_(product_ids))
            ).all()
        } if product_ids else {}
        location_paths = {
            item.record.id: item.path
            for item in LocationRepository(self.session).tree_locations(include_deleted=True)
        }
        links = list(
            self.session.exec(
                select(HomeAssistantAssetLink).where(
                    HomeAssistantAssetLink.object_type == HomeAssistantObjectType.ENTITY.value,
                    col(HomeAssistantAssetLink.asset_id).in_(asset_ids),
                )
            ).all()
        )
        links_by_asset: dict[UUID, list[HomeAssistantAssetLink]] = {
            asset_id: [] for asset_id in asset_ids
        }
        for link in links:
            links_by_asset.setdefault(link.asset_id, []).append(link)
        entity_ids = {link.external_id for link in links}
        live_by_id: dict[str, HomeAssistantEntityRead] = {}
        live_warning: str | None = None
        if entity_ids:
            try:
                _, entities, _, missing_entities, _ = HomeAssistantService(
                    self.session
                ).linked_objects(device_ids=set(), entity_ids=entity_ids)
                live_by_id = {entity.entity_id: entity for entity in entities}
                if missing_entities:
                    live_warning = (
                        f"{len(missing_entities)} verknüpfte Home-Assistant-Entität(en) "
                        "wurden nicht gefunden."
                    )
            except HomeAssistantConfigurationError:
                live_warning = "Home Assistant ist nicht vollständig konfiguriert."
            except HomeAssistantConnectionError:
                live_warning = "Home Assistant ist derzeit nicht erreichbar."
        return [
            self._asset_placement_read(
                item,
                live_by_id,
                live_warning,
                area=areas.get(item.area_id) if item.area_id is not None else None,
                asset=assets.get(item.asset_id),
                product=(
                    products.get(assets[item.asset_id].product_id)
                    if item.asset_id in assets and assets[item.asset_id].product_id is not None
                    else None
                ),
                location_path=(
                    location_paths.get(assets[item.asset_id].location_id)
                    if item.asset_id in assets and assets[item.asset_id].location_id is not None
                    else None
                ),
                links=links_by_asset.get(item.asset_id, []),
            )
            for item in placements
        ]

    def place_asset(
        self,
        distribution_id: UUID,
        asset_id: UUID,
        payload: ElectricalAssetPlacementWrite,
    ) -> ElectricalAssetPlacementRead:
        distribution, area = self._placement_context(distribution_id, payload.area_id)
        asset = self.session.get(Asset, asset_id)
        if asset is None or asset.deleted_at is not None or asset.status != "active":
            raise ElectricalNotFoundError
        product = self.session.get(Product, asset.product_id) if asset.product_id else None
        module_width = effective_asset_module_width(self.session, asset)
        if module_width is None:
            raise ElectricalValidationError(
                "Das Asset benötigt eine DIN-Breite in Teilungseinheiten. "
                "Sie kann direkt am Asset, am Asset-Typ oder am Produkt hinterlegt werden."
            )
        if payload.module_width is not None and payload.module_width != module_width:
            raise ElectricalValidationError(
                "Die Platzierungsbreite muss der am Asset, Asset-Typ oder Produkt "
                "hinterlegten DIN-Breite entsprechen."
            )
        existing = self.session.exec(
            select(ElectricalAssetPlacement).where(
                ElectricalAssetPlacement.asset_id == asset.id,
                col(ElectricalAssetPlacement.deleted_at).is_(None),
            )
        ).first()
        self._validate_module_placement(
            distribution,
            area,
            row_number=payload.row_number,
            start_position=payload.start_position,
            module_width=module_width,
            exclude_asset_placement_id=existing.id if existing else None,
        )
        now = datetime.now(UTC)
        if existing is None:
            existing = ElectricalAssetPlacement(
                distribution_id=distribution_id,
                area_id=area.id if area else None,
                asset_id=asset.id,
                row_number=payload.row_number,
                start_position=payload.start_position,
                module_width=module_width,
                created_at=now,
                updated_at=now,
            )
        else:
            existing.distribution_id = distribution_id
            existing.area_id = area.id if area else None
            existing.row_number = payload.row_number
            existing.start_position = payload.start_position
            existing.module_width = module_width
            existing.updated_at = now
        self.session.add(existing)
        self._commit("Das Asset ist bereits an einer anderen Stelle platziert.")
        self.session.refresh(existing)
        return self._asset_placement_read(existing, {}, None, area=area)

    def unplace_asset(self, distribution_id: UUID, asset_id: UUID) -> None:
        self._distribution(distribution_id)
        placement = self.session.exec(
            select(ElectricalAssetPlacement).where(
                ElectricalAssetPlacement.distribution_id == distribution_id,
                ElectricalAssetPlacement.asset_id == asset_id,
                col(ElectricalAssetPlacement.deleted_at).is_(None),
            )
        ).first()
        if placement is None:
            raise ElectricalNotFoundError
        now = datetime.now(UTC)
        placement.deleted_at = now
        placement.updated_at = now
        self.session.add(placement)
        self._commit()

    def list_cabinet_components(
        self, distribution_id: UUID
    ) -> list[ElectricalCabinetComponentRead]:
        self._distribution(distribution_id)
        statement = (
            select(ElectricalCabinetComponent)
            .where(
                ElectricalCabinetComponent.distribution_id == distribution_id,
                col(ElectricalCabinetComponent.deleted_at).is_(None),
            )
            .order_by(
                col(ElectricalCabinetComponent.area_id),
                col(ElectricalCabinetComponent.row_number),
                col(ElectricalCabinetComponent.start_position),
                col(ElectricalCabinetComponent.name),
            )
        )
        return [
            self._cabinet_component_read(item)
            for item in self.session.exec(statement).all()
        ]

    def create_cabinet_component(
        self,
        distribution_id: UUID,
        payload: ElectricalCabinetComponentWrite,
    ) -> ElectricalCabinetComponentRead:
        distribution, area = self._placement_context(distribution_id, payload.area_id)
        self._validate_cabinet_component_links(distribution_id, payload)
        self._validate_module_placement(
            distribution,
            area,
            row_number=payload.row_number,
            start_position=payload.start_position,
            module_width=payload.module_width,
            placing_component_type=payload.component_type.value,
        )
        record = ElectricalCabinetComponent(
            distribution_id=distribution_id,
            area_id=area.id if area else None,
            **self._cabinet_component_values(payload),
        )
        self.session.add(record)
        self._commit("Die Position ist bereits durch eine andere Schrankkomponente belegt.")
        self.session.refresh(record)
        return self._cabinet_component_read(record)

    def update_cabinet_component(
        self,
        distribution_id: UUID,
        component_id: UUID,
        payload: ElectricalCabinetComponentWrite,
    ) -> ElectricalCabinetComponentRead:
        record = self._cabinet_component(component_id, distribution_id)
        distribution, area = self._placement_context(distribution_id, payload.area_id)
        self._validate_cabinet_component_links(distribution_id, payload)
        self._validate_module_placement(
            distribution,
            area,
            row_number=payload.row_number,
            start_position=payload.start_position,
            module_width=payload.module_width,
            exclude_cabinet_component_id=record.id,
            placing_component_type=payload.component_type.value,
        )
        record.area_id = area.id if area else None
        record.sqlmodel_update(self._cabinet_component_values(payload))
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        self._commit("Die Position ist bereits durch eine andere Schrankkomponente belegt.")
        self.session.refresh(record)
        return self._cabinet_component_read(record)

    def archive_cabinet_component(
        self, distribution_id: UUID, component_id: UUID
    ) -> None:
        record = self._cabinet_component(component_id, distribution_id)
        attached_connection = self.session.exec(
            select(ElectricalConnection).where(
                col(ElectricalConnection.deleted_at).is_(None),
                (
                    (ElectricalConnection.source_kind == "cabinet_component")
                    & (ElectricalConnection.source_id == record.id)
                )
                | (
                    (ElectricalConnection.target_kind == "cabinet_component")
                    & (ElectricalConnection.target_id == record.id)
                ),
            )
        ).first()
        if attached_connection is not None:
            raise ElectricalConflictError(
                "Die Schrankkomponente ist noch verkabelt. Entferne zuerst ihre Verbindungen."
            )
        if self.session.exec(
            select(ElectricalProtectiveDevice).where(
                ElectricalProtectiveDevice.neutral_rail_id == record.id
            )
        ).first() is not None:
            raise ElectricalConflictError(
                "Die N-Schiene ist noch Schutzgeräten zugeordnet. Entferne zuerst diese Zuordnungen."
            )
        now = datetime.now(UTC)
        record.deleted_at = now
        record.updated_at = now
        self.session.add(record)
        self._commit()

    def list_meter_placements(
        self,
        distribution_id: UUID,
    ) -> list[ElectricalMeterPlacementRead]:
        self._structured_distribution(distribution_id)
        statement = (
            select(ElectricalMeterPlacement)
            .where(
                ElectricalMeterPlacement.distribution_id == distribution_id,
                col(ElectricalMeterPlacement.deleted_at).is_(None),
            )
            .order_by(
                col(ElectricalMeterPlacement.area_id),
                col(ElectricalMeterPlacement.position),
            )
        )
        return [self._meter_placement_read(item) for item in self.session.exec(statement).all()]

    def place_meter(
        self,
        distribution_id: UUID,
        meter_id: UUID,
        payload: ElectricalMeterPlacementWrite,
    ) -> ElectricalMeterPlacementRead:
        self._structured_distribution(distribution_id)
        meter = self.session.get(ConsumptionMeter, meter_id)
        if meter is None or meter.deleted_at is not None:
            raise ElectricalNotFoundError
        area = self._area(payload.area_id, distribution_id)
        if area.area_type != DistributionAreaType.METER.value:
            raise ElectricalValidationError(
                "Zähler können nur in einem Zählerfeld platziert werden"
            )
        if meter.asset_id is not None:
            direct_asset = self.session.exec(
                select(ElectricalMeterPlacement).where(
                    ElectricalMeterPlacement.asset_id == meter.asset_id,
                    col(ElectricalMeterPlacement.deleted_at).is_(None),
                )
            ).first()
            if direct_asset is not None:
                raise ElectricalConflictError(
                    "Das verknüpfte Zähler-Asset ist bereits direkt im Schrank platziert"
                )
        existing = self.session.exec(
            select(ElectricalMeterPlacement).where(
                ElectricalMeterPlacement.meter_id == meter_id,
                col(ElectricalMeterPlacement.deleted_at).is_(None),
            )
        ).first()
        if existing is None:
            existing = ElectricalMeterPlacement(
                distribution_id=distribution_id,
                area_id=area.id,
                meter_id=meter_id,
                asset_id=None,
                position=payload.position,
            )
        else:
            existing.distribution_id = distribution_id
            existing.area_id = area.id
            existing.position = payload.position
            existing.updated_at = datetime.now(UTC)
        self.session.add(existing)
        self._commit("Diese Position ist bereits durch einen anderen Zähler belegt")
        self.session.refresh(existing)
        return self._meter_placement_read(existing)

    def place_asset_meter(
        self,
        distribution_id: UUID,
        asset_id: UUID,
        payload: ElectricalMeterPlacementWrite,
    ) -> ElectricalMeterPlacementRead:
        self._structured_distribution(distribution_id)
        asset = self.session.get(Asset, asset_id)
        if asset is None or asset.deleted_at is not None or asset.status != "active":
            raise ElectricalNotFoundError
        asset_type = self.session.get(AssetType, asset.asset_type_id)
        if asset_type is None or asset_type.name.strip().casefold() != "zähler":
            raise ElectricalValidationError(
                "Direkt platzierbare Assets müssen vom Typ „Zähler“ sein"
            )
        area = self._area(payload.area_id, distribution_id)
        if area.area_type != DistributionAreaType.METER.value:
            raise ElectricalValidationError(
                "Zähler können nur in einem Zählerfeld platziert werden"
            )
        linked_meter_ids = {
            meter.id
            for meter in self.session.exec(
                select(ConsumptionMeter).where(
                    ConsumptionMeter.asset_id == asset.id,
                    col(ConsumptionMeter.deleted_at).is_(None),
                )
            ).all()
        }
        if linked_meter_ids:
            linked_placement = self.session.exec(
                select(ElectricalMeterPlacement).where(
                    col(ElectricalMeterPlacement.meter_id).in_(linked_meter_ids),
                    col(ElectricalMeterPlacement.deleted_at).is_(None),
                )
            ).first()
            if linked_placement is not None:
                raise ElectricalConflictError(
                    "Ein mit diesem Asset verknüpfter Verbrauchszähler ist bereits platziert"
                )
        existing = self.session.exec(
            select(ElectricalMeterPlacement).where(
                ElectricalMeterPlacement.asset_id == asset.id,
                col(ElectricalMeterPlacement.deleted_at).is_(None),
            )
        ).first()
        if existing is None:
            existing = ElectricalMeterPlacement(
                distribution_id=distribution_id,
                area_id=area.id,
                meter_id=None,
                asset_id=asset.id,
                position=payload.position,
            )
        else:
            existing.distribution_id = distribution_id
            existing.area_id = area.id
            existing.position = payload.position
            existing.updated_at = datetime.now(UTC)
        self.session.add(existing)
        self._commit("Diese Position ist bereits durch einen anderen Zähler belegt")
        self.session.refresh(existing)
        return self._meter_placement_read(existing)

    def unplace_asset_meter(self, distribution_id: UUID, asset_id: UUID) -> None:
        self._structured_distribution(distribution_id)
        placement = self.session.exec(
            select(ElectricalMeterPlacement).where(
                ElectricalMeterPlacement.distribution_id == distribution_id,
                ElectricalMeterPlacement.asset_id == asset_id,
                col(ElectricalMeterPlacement.deleted_at).is_(None),
            )
        ).first()
        if placement is None:
            raise ElectricalNotFoundError
        now = datetime.now(UTC)
        placement.deleted_at = now
        placement.updated_at = now
        self.session.add(placement)
        self._commit()

    def unplace_meter(self, distribution_id: UUID, meter_id: UUID) -> None:
        self._structured_distribution(distribution_id)
        placement = self.session.exec(
            select(ElectricalMeterPlacement).where(
                ElectricalMeterPlacement.distribution_id == distribution_id,
                ElectricalMeterPlacement.meter_id == meter_id,
                col(ElectricalMeterPlacement.deleted_at).is_(None),
            )
        ).first()
        if placement is None:
            raise ElectricalNotFoundError
        now = datetime.now(UTC)
        placement.deleted_at = now
        placement.updated_at = now
        self.session.add(placement)
        self._commit()

    def place_device(
        self,
        distribution_id: UUID,
        device_id: UUID,
        *,
        area_id: UUID | None,
        row_number: int | None,
        start_position: int | None,
        module_width: int | None,
        assigned_rcd_id: UUID | None = None,
        neutral_rail_id: UUID | None = None,
    ) -> None:
        distribution = self._distribution(distribution_id)
        device, component = self._device(device_id, distribution_id)
        self._validate_device_group_links(
            distribution_id,
            device_id,
            assigned_rcd_id,
            neutral_rail_id,
        )
        device.assigned_rcd_id = assigned_rcd_id
        device.neutral_rail_id = neutral_rail_id
        row_and_start = (row_number, start_position)
        if any(value is not None for value in row_and_start) and any(
            value is None for value in row_and_start
        ):
            raise ElectricalValidationError(
                "Eine Platzierung benötigt Reihe und Startposition."
            )
        if all(value is None for value in row_and_start):
            if module_width is not None:
                raise ElectricalValidationError(
                    "Eine Breite kann nur zusammen mit einer Position gespeichert werden."
                )
            area: ElectricalDistributionArea | None = None
            if distribution.layout_mode == DistributionLayoutMode.SECTIONS.value:
                if area_id is not None:
                    _, area = self._placement_context(distribution_id, area_id)
            elif area_id is not None:
                raise ElectricalValidationError(
                    "Die einfache Reihenaufteilung verwendet keinen DIN-Bereich."
                )
            device.area_id = area.id if area else None
            device.row_number = None
            device.start_position = None
            device.module_width = None
            component.updated_at = datetime.now(UTC)
            self._commit()
            return
        assert row_number is not None and start_position is not None
        asset = self.session.get(Asset, component.asset_id)
        if asset is None or asset.deleted_at is not None:
            raise ElectricalValidationError(
                "Das zum Schutzgerät gehörende Asset ist nicht verfügbar."
            )
        inherited_width = effective_asset_module_width(self.session, asset)
        if inherited_width is not None:
            if module_width is not None and module_width != inherited_width:
                raise ElectricalValidationError(
                    "Die Schutzgerätebreite muss der am Asset, Asset-Typ oder Produkt "
                    "hinterlegten DIN-Breite entsprechen."
                )
            resolved_width = inherited_width
        elif device.module_width is not None and module_width in (None, device.module_width):
            resolved_width = device.module_width
        elif module_width is not None:
            resolved_width = module_width
        else:
            raise ElectricalValidationError(
                "Das Schutzgeräte-Asset benötigt eine DIN-Breite am Asset, Asset-Typ "
                "oder Produkt, bevor es auf der Hutschiene platziert werden kann."
            )
        _, area = self._placement_context(distribution_id, area_id)
        self._validate_module_placement(
            distribution,
            area,
            row_number=row_number,
            start_position=start_position,
            module_width=resolved_width,
            exclude_device_id=device_id,
        )
        device.area_id = area.id if area else None
        device.row_number = row_number
        device.start_position = start_position
        device.module_width = resolved_width
        component.updated_at = datetime.now(UTC)
        self._commit()

    def update_device_technical(
        self,
        distribution_id: UUID,
        device_id: UUID,
        payload: ProtectiveDeviceWrite,
    ) -> None:
        self._distribution(distribution_id)
        device, component = self._device(device_id, distribution_id)
        if payload.distribution_id != distribution_id:
            raise ElectricalConflictError(
                "Protective device cannot be moved through the technical editor"
            )
        if payload.asset_id != component.asset_id:
            raise ElectricalConflictError("Electrical role asset identity is immutable")
        self._validate_device_group_links(
            distribution_id,
            device_id,
            payload.assigned_rcd_id,
            payload.neutral_rail_id,
        )
        device.device_type = payload.device_type.value
        device.rated_current_a = payload.rated_current_a
        device.residual_current_ma = payload.residual_current_ma
        device.characteristic = payload.characteristic
        device.poles = payload.poles
        device.breaking_capacity_ka = payload.breaking_capacity_ka
        device.rcd_type = payload.rcd_type
        device.fuse_type = payload.fuse_type
        device.spd_type = payload.spd_type
        device.assigned_rcd_id = payload.assigned_rcd_id
        device.neutral_rail_id = payload.neutral_rail_id
        device.description = payload.description
        device.notes = payload.notes
        component.updated_at = datetime.now(UTC)
        self._commit()

    def _validate_placement(
        self,
        device_id: UUID,
        area: ElectricalDistributionArea,
        row_number: int,
        start_position: int,
        module_width: int,
    ) -> None:
        distribution = self._distribution_for_area(area)
        self._validate_module_placement(
            distribution,
            area,
            row_number=row_number,
            start_position=start_position,
            module_width=module_width,
            exclude_device_id=device_id,
        )

    def _validate_area_level(
        self,
        section_id: UUID,
        payload: DistributionAreaWrite,
        *,
        exclude_id: UUID | None,
    ) -> None:
        for existing in self._areas():
            if (
                existing.section_id != section_id
                or existing.position != payload.position
                or existing.id == exclude_id
            ):
                continue
            if (
                payload.width == DistributionAreaWidth.FULL
                or existing.width == DistributionAreaWidth.FULL.value
            ):
                raise ElectricalConflictError(
                    f"Ebene {payload.position} ist bereits belegt. Ein Bereich voller Breite "
                    "kann nicht mit einem weiteren Bereich kombiniert werden."
                )
            requested_side = payload.side.value if payload.side is not None else None
            if existing.side == requested_side:
                side_name = (
                    "linke"
                    if requested_side == DistributionAreaSide.LEFT.value
                    else "rechte"
                )
                raise ElectricalConflictError(
                    f"Auf Ebene {payload.position} ist die {side_name} Hälfte bereits belegt."
                )

    @staticmethod
    def _area_conflict_message(payload: DistributionAreaWrite) -> str:
        if payload.width == DistributionAreaWidth.FULL:
            return (
                f"Ebene {payload.position} ist bereits belegt. Ein Bereich voller Breite "
                "kann nicht mit weiteren Bereichen kombiniert werden."
            )
        side_name = "linke" if payload.side == DistributionAreaSide.LEFT else "rechte"
        return f"Auf Ebene {payload.position} ist die {side_name} Hälfte bereits belegt."

    def _validate_generic_placement(
        self,
        area: ElectricalDistributionArea,
        *,
        row_number: int,
        start_position: int,
        module_width: int,
        exclude_id: UUID | None,
    ) -> None:
        distribution = self._distribution_for_area(area)
        self._validate_module_placement(
            distribution,
            area,
            row_number=row_number,
            start_position=start_position,
            module_width=module_width,
            exclude_asset_placement_id=exclude_id,
        )

    def _distribution(self, distribution_id: UUID) -> ElectricalDistribution:
        distribution = self.session.get(ElectricalDistribution, distribution_id)
        component = self.session.get(ElectricalComponent, distribution_id)
        if distribution is None or component is None or component.deleted_at is not None:
            raise ElectricalNotFoundError
        return distribution

    def _distribution_for_area(
        self, area: ElectricalDistributionArea
    ) -> ElectricalDistribution:
        section = self.session.get(ElectricalDistributionSection, area.section_id)
        if section is None or section.deleted_at is not None:
            raise ElectricalNotFoundError
        return self._distribution(section.distribution_id)

    def _placement_context(
        self,
        distribution_id: UUID,
        area_id: UUID | None,
    ) -> tuple[ElectricalDistribution, ElectricalDistributionArea | None]:
        distribution = self._distribution(distribution_id)
        if distribution.layout_mode == DistributionLayoutMode.SECTIONS.value:
            if area_id is None:
                raise ElectricalValidationError(
                    "Für diese Verteilung muss ein Gerätebereich ausgewählt werden."
                )
            area = self._area(area_id, distribution_id)
            if area.area_type != DistributionAreaType.DEVICE_ROWS.value:
                raise ElectricalValidationError(
                    "DIN-Komponenten können nur in einem Gerätebereich platziert werden."
                )
            return distribution, area
        if area_id is not None:
            raise ElectricalValidationError(
                "Die einfache Reihenaufteilung verwendet keinen DIN-Bereich."
            )
        return distribution, None

    def _validate_module_placement(
        self,
        distribution: ElectricalDistribution,
        area: ElectricalDistributionArea | None,
        *,
        row_number: int,
        start_position: int,
        module_width: int,
        exclude_device_id: UUID | None = None,
        exclude_asset_placement_id: UUID | None = None,
        exclude_cabinet_component_id: UUID | None = None,
        placing_component_type: str | None = None,
    ) -> None:
        rows = area.rows if area is not None else distribution.rows
        modules_per_row = (
            area.modules_per_row if area is not None else distribution.modules_per_row
        )
        if rows is not None and row_number > rows:
            raise ElectricalConflictError(
                f"Reihe {row_number} überschreitet die Kapazität von {rows} Reihen."
            )
        end_position = start_position + module_width - 1
        if modules_per_row is not None and end_position > modules_per_row:
            raise ElectricalConflictError(
                f"Die Komponente endet bei TE {end_position}; verfügbar sind nur "
                f"{modules_per_row} TE."
            )
        area_id = area.id if area else None
        placing_busbar = placing_component_type == ElectricalCabinetComponentType.BUSBAR.value
        for device in self._active_devices_for_context(distribution.id, area_id):
            if placing_busbar:
                continue
            if device.id == exclude_device_id or device.row_number != row_number:
                continue
            if device.start_position is None or device.module_width is None:
                continue
            other_end = device.start_position + device.module_width - 1
            if start_position <= other_end and end_position >= device.start_position:
                raise ElectricalConflictError(
                    "Die Position überschneidet sich mit einem vorhandenen Schutzgerät."
                )
        for placement in self._active_asset_placements_for_context(
            distribution.id, area_id
        ):
            if (
                placement.id == exclude_asset_placement_id
                or placement.row_number != row_number
            ):
                continue
            other_end = placement.start_position + placement.module_width - 1
            if start_position <= other_end and end_position >= placement.start_position:
                raise ElectricalConflictError(
                    "Die Position überschneidet sich mit einem vorhandenen DIN-Hutschienengerät."
                )
        for component in self._active_cabinet_components_for_context(
            distribution.id, area_id
        ):
            if (
                component.id == exclude_cabinet_component_id
                or component.row_number != row_number
            ):
                continue
            other_end = component.start_position + component.module_width - 1
            if start_position <= other_end and end_position >= component.start_position:
                existing_busbar = (
                    component.component_type == ElectricalCabinetComponentType.BUSBAR.value
                )
                # Kammschienen liegen als Overlay ausschließlich unter Schutzgeräten.
                # DIN-Assets und andere passive Komponenten belegen weiterhin echten Platz.
                if existing_busbar and exclude_device_id is not None:
                    continue
                raise ElectricalConflictError(
                    "Die Position überschneidet sich mit einer vorhandenen Schrankkomponente."
                )

    def _active_devices_for_context(
        self, distribution_id: UUID, area_id: UUID | None
    ) -> list[ElectricalProtectiveDevice]:
        statement = (
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
        statement = (
            statement.where(col(ElectricalProtectiveDevice.area_id).is_(None))
            if area_id is None
            else statement.where(ElectricalProtectiveDevice.area_id == area_id)
        )
        return list(self.session.exec(statement).all())

    def _active_asset_placements_for_context(
        self, distribution_id: UUID, area_id: UUID | None
    ) -> list[ElectricalAssetPlacement]:
        statement = select(ElectricalAssetPlacement).where(
            ElectricalAssetPlacement.distribution_id == distribution_id,
            col(ElectricalAssetPlacement.deleted_at).is_(None),
        )
        statement = (
            statement.where(col(ElectricalAssetPlacement.area_id).is_(None))
            if area_id is None
            else statement.where(ElectricalAssetPlacement.area_id == area_id)
        )
        return list(self.session.exec(statement).all())

    def _active_cabinet_components_for_context(
        self, distribution_id: UUID, area_id: UUID | None
    ) -> list[ElectricalCabinetComponent]:
        statement = select(ElectricalCabinetComponent).where(
            ElectricalCabinetComponent.distribution_id == distribution_id,
            col(ElectricalCabinetComponent.deleted_at).is_(None),
        )
        statement = (
            statement.where(col(ElectricalCabinetComponent.area_id).is_(None))
            if area_id is None
            else statement.where(ElectricalCabinetComponent.area_id == area_id)
        )
        return list(self.session.exec(statement).all())

    def _cabinet_component(
        self, component_id: UUID, distribution_id: UUID
    ) -> ElectricalCabinetComponent:
        record = self.session.get(ElectricalCabinetComponent, component_id)
        if (
            record is None
            or record.deleted_at is not None
            or record.distribution_id != distribution_id
        ):
            raise ElectricalNotFoundError
        return record

    def _cabinet_component_read(
        self, record: ElectricalCabinetComponent
    ) -> ElectricalCabinetComponentRead:
        distribution = self._distribution(record.distribution_id)
        role = self.session.get(ElectricalComponent, distribution.id)
        asset = self.session.get(Asset, role.asset_id) if role else None
        area = (
            self.session.get(ElectricalDistributionArea, record.area_id)
            if record.area_id is not None
            else None
        )
        return ElectricalCabinetComponentRead(
            id=record.id,
            distribution_id=record.distribution_id,
            distribution_name=distribution.designation or (asset.name if asset else "Verteilung"),
            area_id=record.area_id,
            area_name=area.name if area else "Einfache Reihenaufteilung",
            name=record.name,
            component_type=ElectricalCabinetComponentType(record.component_type),
            row_number=record.row_number,
            start_position=record.start_position,
            module_width=record.module_width,
            phases=self._cabinet_component_phases(record),
            rated_current_a=record.rated_current_a,
            max_cross_section_mm2=record.max_cross_section_mm2,
            outgoing_connections=record.outgoing_connections,
            linked_rcd_device_id=record.linked_rcd_device_id,
            linked_rcd_name=self._protective_device_display_name(record.linked_rcd_device_id),
            start_phase=(
                ElectricalPhase(record.start_phase) if record.start_phase is not None else None
            ),
            description=record.description,
            notes=record.notes,
            created_at=record.created_at,
            updated_at=record.updated_at,
            deleted_at=record.deleted_at,
        )

    @staticmethod
    def _cabinet_component_values(
        payload: ElectricalCabinetComponentWrite,
    ) -> dict[str, object]:
        phases = set(payload.phases)
        return {
            "name": payload.name,
            "component_type": payload.component_type.value,
            "row_number": payload.row_number,
            "start_position": payload.start_position,
            "module_width": payload.module_width,
            "phase_l1": ElectricalPhase.L1 in phases,
            "phase_l2": ElectricalPhase.L2 in phases,
            "phase_l3": ElectricalPhase.L3 in phases,
            "neutral": ElectricalPhase.N in phases,
            "protective_earth": ElectricalPhase.PE in phases,
            "rated_current_a": payload.rated_current_a,
            "max_cross_section_mm2": payload.max_cross_section_mm2,
            "outgoing_connections": payload.outgoing_connections,
            "linked_rcd_device_id": payload.linked_rcd_device_id,
            "start_phase": (
                payload.start_phase.value if payload.start_phase is not None else None
            ),
            "description": payload.description,
            "notes": payload.notes,
        }

    @staticmethod
    def _cabinet_component_phases(
        record: ElectricalCabinetComponent,
    ) -> list[ElectricalPhase]:
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

    def _protective_device_display_name(self, device_id: UUID | None) -> str | None:
        if device_id is None:
            return None
        device = self.session.get(ElectricalProtectiveDevice, device_id)
        role = self.session.get(ElectricalComponent, device_id)
        asset = self.session.get(Asset, role.asset_id) if role else None
        if device is None or role is None or role.deleted_at is not None:
            return None
        return asset.name if asset else str(device_id)

    def _validate_rcd(self, distribution_id: UUID, device_id: UUID | None) -> None:
        if device_id is None:
            return
        device = self.session.get(ElectricalProtectiveDevice, device_id)
        component = self.session.get(ElectricalComponent, device_id)
        if (
            device is None
            or component is None
            or component.deleted_at is not None
            or device.distribution_id != distribution_id
            or device.device_type != "rcd"
        ):
            raise ElectricalValidationError(
                "Der ausgewählte FI/RCD ist in dieser Verteilung nicht verfügbar."
            )

    def _validate_device_group_links(
        self,
        distribution_id: UUID,
        device_id: UUID,
        assigned_rcd_id: UUID | None,
        neutral_rail_id: UUID | None,
    ) -> None:
        if assigned_rcd_id == device_id:
            raise ElectricalValidationError("Ein FI kann nicht sich selbst als vorgeschalteten FI verwenden.")
        self._validate_rcd(distribution_id, assigned_rcd_id)
        if neutral_rail_id is None:
            return
        rail = self.session.get(ElectricalCabinetComponent, neutral_rail_id)
        if (
            rail is None
            or rail.deleted_at is not None
            or rail.distribution_id != distribution_id
            or rail.component_type != ElectricalCabinetComponentType.NEUTRAL_RAIL.value
        ):
            raise ElectricalValidationError(
                "Die ausgewählte N-Schiene ist in dieser Verteilung nicht verfügbar."
            )
        if assigned_rcd_id is not None and rail.linked_rcd_device_id not in (None, assigned_rcd_id):
            raise ElectricalValidationError(
                "Die N-Schiene ist einem anderen FI/RCD zugeordnet."
            )

    def _validate_cabinet_component_links(
        self,
        distribution_id: UUID,
        payload: ElectricalCabinetComponentWrite,
    ) -> None:
        self._validate_rcd(distribution_id, payload.linked_rcd_device_id)
        if (
            payload.linked_rcd_device_id is not None
            and payload.component_type not in {
                ElectricalCabinetComponentType.BUSBAR,
                ElectricalCabinetComponentType.NEUTRAL_RAIL,
            }
        ):
            raise ElectricalValidationError(
                "Eine FI-Zuordnung ist nur für Sammelschienen und N-Schienen vorgesehen."
            )

    def _structured_distribution(
        self,
        distribution_id: UUID,
    ) -> ElectricalDistribution:
        distribution = self._distribution(distribution_id)
        if distribution.layout_mode != DistributionLayoutMode.SECTIONS.value:
            raise ElectricalConflictError(
                "Diese Verteilung verwendet die einfache Reihenaufteilung."
            )
        return distribution

    def _device(
        self,
        device_id: UUID,
        distribution_id: UUID,
    ) -> tuple[ElectricalProtectiveDevice, ElectricalComponent]:
        device = self.session.get(ElectricalProtectiveDevice, device_id)
        component = self.session.get(ElectricalComponent, device_id)
        if (
            device is None
            or component is None
            or component.deleted_at is not None
            or device.distribution_id != distribution_id
        ):
            raise ElectricalNotFoundError
        return device, component

    def _section(
        self,
        section_id: UUID,
        distribution_id: UUID,
    ) -> ElectricalDistributionSection:
        section = self.session.get(ElectricalDistributionSection, section_id)
        if (
            section is None
            or section.deleted_at is not None
            or section.distribution_id != distribution_id
        ):
            raise ElectricalNotFoundError
        return section

    def _area(
        self,
        area_id: UUID,
        distribution_id: UUID,
    ) -> ElectricalDistributionArea:
        area = self.session.get(ElectricalDistributionArea, area_id)
        if area is None or area.deleted_at is not None:
            raise ElectricalNotFoundError
        self._section(area.section_id, distribution_id)
        return area

    def _sections(
        self,
        distribution_id: UUID,
    ) -> list[ElectricalDistributionSection]:
        statement = (
            select(ElectricalDistributionSection)
            .where(
                ElectricalDistributionSection.distribution_id == distribution_id,
                col(ElectricalDistributionSection.deleted_at).is_(None),
            )
            .order_by(
                col(ElectricalDistributionSection.position),
                col(ElectricalDistributionSection.name),
            )
        )
        return list(self.session.exec(statement).all())

    def _areas(self) -> list[ElectricalDistributionArea]:
        statement = (
            select(ElectricalDistributionArea)
            .where(col(ElectricalDistributionArea.deleted_at).is_(None))
            .order_by(
                col(ElectricalDistributionArea.position),
                col(ElectricalDistributionArea.name),
            )
        )
        return list(self.session.exec(statement).all())

    def _active_devices(
        self,
        area_id: UUID,
    ) -> list[ElectricalProtectiveDevice]:
        statement = (
            select(ElectricalProtectiveDevice)
            .join(
                ElectricalComponent,
                ElectricalComponent.id == ElectricalProtectiveDevice.id,
            )
            .where(
                ElectricalProtectiveDevice.area_id == area_id,
                col(ElectricalComponent.deleted_at).is_(None),
            )
        )
        return list(self.session.exec(statement).all())

    def _active_asset_placements(
        self, area_id: UUID
    ) -> list[ElectricalAssetPlacement]:
        statement = select(ElectricalAssetPlacement).where(
            ElectricalAssetPlacement.area_id == area_id,
            col(ElectricalAssetPlacement.deleted_at).is_(None),
        )
        return list(self.session.exec(statement).all())

    def _active_cabinet_components(
        self, area_id: UUID
    ) -> list[ElectricalCabinetComponent]:
        statement = select(ElectricalCabinetComponent).where(
            ElectricalCabinetComponent.area_id == area_id,
            col(ElectricalCabinetComponent.deleted_at).is_(None),
        )
        return list(self.session.exec(statement).all())

    def _active_meter_placements(
        self,
        area_id: UUID,
    ) -> list[ElectricalMeterPlacement]:
        statement = select(ElectricalMeterPlacement).where(
            ElectricalMeterPlacement.area_id == area_id,
            col(ElectricalMeterPlacement.deleted_at).is_(None),
        )
        return list(self.session.exec(statement).all())

    def _validate_area_capacity(
        self,
        area_id: UUID,
        rows: int | None,
        modules_per_row: int | None,
    ) -> None:
        placements: list[tuple[int, int, int]] = []
        for device in self._active_devices(area_id):
            if (
                device.row_number is not None
                and device.start_position is not None
                and device.module_width is not None
            ):
                placements.append(
                    (device.row_number, device.start_position, device.module_width)
                )
        placements.extend(
            (item.row_number, item.start_position, item.module_width)
            for item in self._active_asset_placements(area_id)
        )
        placements.extend(
            (item.row_number, item.start_position, item.module_width)
            for item in self._active_cabinet_components(area_id)
        )
        for row_number, start_position, module_width in placements:
            if rows is not None and row_number > rows:
                raise ElectricalConflictError(
                    "Ein platziertes Gerät überschreitet die neue Anzahl an Reihen."
                )
            end_position = start_position + module_width - 1
            if modules_per_row is not None and end_position > modules_per_row:
                raise ElectricalConflictError(
                    "Ein platziertes Gerät überschreitet die neue Anzahl an Teilungseinheiten."
                )

    @staticmethod
    def _area_read(area: ElectricalDistributionArea) -> DistributionAreaRead:
        return DistributionAreaRead(
            id=area.id,
            section_id=area.section_id,
            name=area.name,
            area_type=DistributionAreaType(area.area_type),
            position=area.position,
            rows=area.rows,
            modules_per_row=area.modules_per_row,
            width=DistributionAreaWidth(area.width),
            side=DistributionAreaSide(area.side) if area.side is not None else None,
            description=area.description,
            created_at=area.created_at,
            updated_at=area.updated_at,
            deleted_at=area.deleted_at,
        )

    def _asset_placement_read(
        self,
        placement: ElectricalAssetPlacement,
        live_by_id: dict[str, HomeAssistantEntityRead],
        live_warning: str | None,
        *,
        area: ElectricalDistributionArea | None = None,
        asset: Asset | None = None,
        product: Product | None = None,
        location_path: str | None = None,
        links: list[HomeAssistantAssetLink] | None = None,
    ) -> ElectricalAssetPlacementRead:
        if area is None and placement.area_id is not None:
            area = self.session.get(ElectricalDistributionArea, placement.area_id)
        asset = asset or self.session.get(Asset, placement.asset_id)
        if asset is None:
            raise ElectricalValidationError(
                "Gespeicherte DIN-Hutschienenplatzierung ist unvollständig."
            )
        if product is None and asset.product_id is not None:
            product = self.session.get(Product, asset.product_id)
        if location_path is None and asset.location_id is not None:
            projection = LocationRepository(self.session).get_projection(
                asset.location_id, include_deleted=True
            )
            location_path = projection.path if projection else None
        if links is None:
            links = list(
                self.session.exec(
                    select(HomeAssistantAssetLink).where(
                        HomeAssistantAssetLink.asset_id == asset.id,
                        HomeAssistantAssetLink.object_type
                        == HomeAssistantObjectType.ENTITY.value,
                    )
                ).all()
            )
        live_values: list[ElectricalLiveValueRead] = []
        for link in sorted(links, key=lambda item: (item.role, item.external_id)):
            entity = live_by_id.get(link.external_id)
            if entity is None:
                continue
            live_values.append(
                ElectricalLiveValueRead(
                    entity_id=entity.entity_id,
                    name=entity.name,
                    role=link.role,
                    state=entity.state,
                    unit=entity.unit,
                    available=entity.available,
                    last_updated=entity.last_updated,
                )
            )
        primary = next(
            (
                item
                for item in live_values
                if item.role == HomeAssistantEntityRole.PRIMARY_LIVE.value
            ),
            live_values[0] if live_values else None,
        )
        return ElectricalAssetPlacementRead(
            id=placement.id,
            distribution_id=placement.distribution_id,
            area_id=placement.area_id,
            area_name=area.name if area else "Einfache Reihenaufteilung",
            asset_id=asset.id,
            asset_name=asset.name,
            asset_code=asset.jarvis_code,
            product_name=product.name if product else None,
            location_path=location_path,
            row_number=placement.row_number,
            start_position=placement.start_position,
            module_width=placement.module_width,
            primary_live_value=primary,
            live_values=live_values,
            live_warning=live_warning,
            created_at=placement.created_at,
            updated_at=placement.updated_at,
        )

    def _meter_placement_read(
        self,
        placement: ElectricalMeterPlacement,
    ) -> ElectricalMeterPlacementRead:
        area = self.session.get(ElectricalDistributionArea, placement.area_id)
        meter = (
            self.session.get(ConsumptionMeter, placement.meter_id)
            if placement.meter_id is not None
            else None
        )
        asset = (
            self.session.get(Asset, placement.asset_id)
            if placement.asset_id is not None
            else self.session.get(Asset, meter.asset_id)
            if meter is not None and meter.asset_id is not None
            else None
        )
        if area is None or (meter is None and asset is None):
            raise ElectricalValidationError("Gespeicherte Zählerplatzierung ist unvollständig")
        effective_location_id = (
            meter.location_id if meter is not None else None
        ) or (asset.location_id if asset else None)
        location = (
            self.session.get(Location, effective_location_id)
            if effective_location_id
            else None
        )
        location_path = None
        if location is not None:
            projection = LocationRepository(self.session).get_projection(
                location.id, include_deleted=True
            )
            location_path = projection.path if projection else location.name
        latest = None
        if meter is not None:
            latest = self.session.exec(
                select(ConsumptionReading)
                .where(
                    ConsumptionReading.meter_id == meter.id,
                    col(ConsumptionReading.deleted_at).is_(None),
                )
                .order_by(col(ConsumptionReading.measured_at).desc())
            ).first()
            source_kind = "consumption_meter"
            meter_id = meter.id
            meter_name = meter.name
            meter_type = meter.meter_type
            unit = meter.unit
            serial_number = meter.serial_number or (asset.serial_number if asset else None)
        else:
            assert asset is not None
            source_kind = "asset"
            meter_id = None
            meter_name = asset.name
            meter_type = "asset"
            unit = ""
            serial_number = asset.serial_number
        return ElectricalMeterPlacementRead(
            id=placement.id,
            distribution_id=placement.distribution_id,
            area_id=placement.area_id,
            area_name=area.name,
            position=placement.position,
            source_kind=source_kind,
            meter_id=meter_id,
            meter_name=meter_name,
            meter_type=meter_type,
            unit=unit,
            serial_number=serial_number,
            asset_id=asset.id if asset else None,
            asset_name=asset.name if asset else None,
            asset_code=asset.jarvis_code if asset else None,
            location_path=location_path,
            latest_value=latest.value if latest else None,
            latest_measured_at=latest.measured_at if latest else None,
            created_at=placement.created_at,
            updated_at=placement.updated_at,
        )

    def _section_read(
        self,
        section: ElectricalDistributionSection,
        areas: list[ElectricalDistributionArea],
    ) -> DistributionSectionRead:
        return DistributionSectionRead(
            id=section.id,
            distribution_id=section.distribution_id,
            name=section.name,
            position=section.position,
            description=section.description,
            created_at=section.created_at,
            updated_at=section.updated_at,
            deleted_at=section.deleted_at,
            areas=[
                self._area_read(area)
                for area in sorted(
                    areas,
                    key=lambda item: (
                        item.position,
                        0 if item.side == "left" else 1 if item.side == "right" else 2,
                        item.name.casefold(),
                    ),
                )
            ],
        )

    def _commit(self, conflict_message: str | None = None) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ElectricalConflictError(
                conflict_message or "The layout change conflicts with existing data"
            ) from exc
        except Exception:
            self.session.rollback()
            raise
