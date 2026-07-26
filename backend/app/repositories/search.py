from dataclasses import dataclass
from uuid import UUID

from sqlmodel import Session, select

from app.models.asset_engine import Asset, AssetType, Location, Product
from app.models.consumption import ConsumptionMeter
from app.models.knowledge import WikiPage
from app.models.network import NetworkAddress, NetworkDevice, NetworkInterface, NetworkSegment
from app.repositories.asset_engine import LocationRepository
from app.repositories.electrical import (
    ElectricalDistributionRepository,
    ElectricalProtectiveDeviceRepository,
)
from app.repositories.electrical_circuit import ElectricalCircuitRepository
from app.schemas.asset_engine import SortOrder
from app.schemas.search import SearchResultType


@dataclass(frozen=True)
class SearchCandidate:
    result_type: SearchResultType
    id: UUID
    title: str
    subtitle: str
    description: str | None
    route: str
    archived: bool
    matched_fields: tuple[str, ...]
    rank: int


FieldValues = tuple[tuple[str, str | None], ...]


def _normalized(value: str | None) -> str:
    return (value or "").casefold()


def _matched_fields(query: str, fields: FieldValues) -> tuple[str, ...]:
    return tuple(label for label, value in fields if query in _normalized(value))


def _rank(
    query: str,
    *,
    title: str,
    exact_values: tuple[str | None, ...],
    fields: FieldValues,
) -> int:
    normalized_exact = tuple(_normalized(value) for value in exact_values if value)
    title_value = title.casefold()
    all_values = tuple(_normalized(value) for _, value in fields if value)
    if query in normalized_exact:
        return 0
    if any(value.startswith(query) for value in normalized_exact):
        return 1
    if title_value == query:
        return 2
    if title_value.startswith(query):
        return 3
    if any(value.startswith(query) for value in all_values):
        return 4
    if query in title_value:
        return 5
    return 6


def _sort_and_limit(candidates: list[SearchCandidate], limit: int) -> list[SearchCandidate]:
    candidates.sort(key=lambda item: (item.rank, item.title.casefold(), str(item.id)))
    return candidates[:limit]


class GlobalSearchRepository:
    """Build bounded, local search projections without exposing persistence models."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def search_assets(
        self,
        query: str,
        *,
        limit: int,
        include_archived: bool,
    ) -> list[SearchCandidate]:
        asset_types = {item.id: item for item in self.session.exec(select(AssetType)).all()}
        products = {item.id: item for item in self.session.exec(select(Product)).all()}
        location_paths = {
            projection.record.id: projection.path
            for projection in LocationRepository(self.session).tree_locations(include_deleted=True)
        }
        candidates: list[SearchCandidate] = []
        for asset in self.session.exec(select(Asset)).all():
            archived = asset.deleted_at is not None
            if archived and not include_archived:
                continue
            asset_type = asset_types.get(asset.asset_type_id)
            product = products.get(asset.product_id) if asset.product_id else None
            location_path = location_paths.get(asset.location_id, "") if asset.location_id else ""
            fields: FieldValues = (
                ("Name", asset.name),
                ("DocOfHome-Code", asset.jarvis_code),
                ("Beschreibung", asset.description),
                ("Seriennummer", asset.serial_number),
                ("Inventarnummer", asset.inventory_number),
                ("Asset-Typ", asset_type.name if asset_type else None),
                ("Produkt", product.name if product else None),
                ("Hersteller", product.manufacturer if product else None),
                ("Modellnummer", product.model_number if product else None),
                ("Standort", location_path),
            )
            matched = _matched_fields(query, fields)
            if not matched:
                continue
            subtitle_parts = [asset.jarvis_code]
            if asset_type:
                subtitle_parts.append(asset_type.name)
            if location_path:
                subtitle_parts.append(location_path)
            context_parts: list[str] = []
            if product:
                product_label = product.name
                if product.manufacturer:
                    product_label = f"{product.manufacturer} · {product_label}"
                if product.model_number:
                    product_label = f"{product_label} · {product.model_number}"
                context_parts.append(product_label)
            if asset.description:
                context_parts.append(asset.description)
            route = f"/assets/{asset.id}"
            if archived:
                route += "?archived=1"
            candidates.append(
                SearchCandidate(
                    result_type=SearchResultType.ASSET,
                    id=asset.id,
                    title=asset.name,
                    subtitle=" · ".join(subtitle_parts),
                    description=" — ".join(context_parts) or None,
                    route=route,
                    archived=archived,
                    matched_fields=matched,
                    rank=_rank(
                        query,
                        title=asset.name,
                        exact_values=(asset.jarvis_code,),
                        fields=fields,
                    ),
                )
            )
        return _sort_and_limit(candidates, limit)

    def search_locations(self, query: str, *, limit: int) -> list[SearchCandidate]:
        type_labels = {
            "building": "Gebäude",
            "floor": "Etage",
            "room": "Raum",
            "area": "Bereich",
            "cabinet": "Schrank",
            "installation_point": "Installationspunkt",
            "outdoor": "Außenbereich",
        }
        candidates: list[SearchCandidate] = []
        # Archived locations are deliberately excluded: the current frontend has no
        # explicit historical read route for them.
        for projection in LocationRepository(self.session).tree_locations(include_deleted=False):
            record = projection.record
            fields: FieldValues = (
                ("Name", record.name),
                ("Kurzname", record.short_name),
                ("Beschreibung", record.description),
                ("Notizen", record.notes),
                ("Pfad", projection.path),
            )
            matched = _matched_fields(query, fields)
            if not matched:
                continue
            candidates.append(
                SearchCandidate(
                    result_type=SearchResultType.LOCATION,
                    id=record.id,
                    title=record.name,
                    subtitle=(
                        f"{type_labels.get(record.location_type, record.location_type)} "
                        f"· {projection.path}"
                    ),
                    description=record.description or record.notes,
                    route=f"/locations/{record.id}",
                    archived=False,
                    matched_fields=matched,
                    rank=_rank(query, title=record.name, exact_values=(), fields=fields),
                )
            )
        return _sort_and_limit(candidates, limit)

    def search_distributions(self, query: str, *, limit: int) -> list[SearchCandidate]:
        repository = ElectricalDistributionRepository(self.session)
        candidates: list[SearchCandidate] = []
        for projection in repository.tree(include_deleted=False):
            record = projection.record
            title = repository.display_name(projection)
            fields: FieldValues = (
                ("Bezeichnung", record.designation),
                ("Asset-Name", projection.asset.record.name),
                ("DocOfHome-Code", projection.asset.record.jarvis_code),
                ("Beschreibung", record.description),
                ("Notizen", record.notes),
                ("Standort", projection.asset.location_path),
            )
            matched = _matched_fields(query, fields)
            if not matched:
                continue
            kind = "Hauptverteilung" if record.distribution_type == "main" else "Unterverteilung"
            subtitle = f"{kind} · {projection.asset.record.jarvis_code}"
            if projection.asset.location_path:
                subtitle += f" · {projection.asset.location_path}"
            candidates.append(
                SearchCandidate(
                    result_type=SearchResultType.ELECTRICAL_DISTRIBUTION,
                    id=record.id,
                    title=title,
                    subtitle=subtitle,
                    description=record.description or record.notes,
                    route=f"/electrical/distributions/{record.id}",
                    archived=False,
                    matched_fields=matched,
                    rank=_rank(
                        query,
                        title=title,
                        exact_values=(projection.asset.record.jarvis_code,),
                        fields=fields,
                    ),
                )
            )
        return _sort_and_limit(candidates, limit)

    def search_protective_devices(self, query: str, *, limit: int) -> list[SearchCandidate]:
        page = ElectricalProtectiveDeviceRepository(self.session).list_page(
            page=1,
            page_size=1_000_000,
            search=None,
            sort_by="asset_name",
            sort_order=SortOrder.ASC,
            include_deleted=False,
            distribution_id=None,
            device_type=None,
            location_id=None,
        )
        type_labels = {
            "fuse": "Sicherung",
            "rcd": "RCD/FI",
            "mcb": "Leitungsschutzschalter",
            "rcbo": "FI/LS",
            "spd": "Überspannungsschutz",
        }
        candidates: list[SearchCandidate] = []
        for projection in page.items:
            record = projection.record
            title = projection.asset.record.name
            technical = [type_labels.get(record.device_type, record.device_type)]
            if record.rated_current_a is not None:
                technical.append(f"{record.rated_current_a:g} A")
            if record.characteristic:
                technical.append(record.characteristic)
            fields: FieldValues = (
                ("Asset-Name", projection.asset.record.name),
                ("DocOfHome-Code", projection.asset.record.jarvis_code),
                ("Gerätetyp", type_labels.get(record.device_type, record.device_type)),
                ("Beschreibung", record.description),
                ("Notizen", record.notes),
                ("Verteilung", projection.distribution_name),
                ("Standort", projection.asset.location_path),
                ("RCD-Typ", record.rcd_type),
                ("Sicherungstyp", record.fuse_type),
                ("SPD-Typ", record.spd_type),
                ("Charakteristik", record.characteristic),
            )
            matched = _matched_fields(query, fields)
            if not matched:
                continue
            subtitle = f"{' · '.join(technical)} · {projection.distribution_name}"
            candidates.append(
                SearchCandidate(
                    result_type=SearchResultType.ELECTRICAL_PROTECTIVE_DEVICE,
                    id=record.id,
                    title=title,
                    subtitle=subtitle,
                    description=record.description or record.notes,
                    route=f"/electrical/protective-devices/{record.id}/edit",
                    archived=False,
                    matched_fields=matched,
                    rank=_rank(
                        query,
                        title=title,
                        exact_values=(projection.asset.record.jarvis_code,),
                        fields=fields,
                    ),
                )
            )
        return _sort_and_limit(candidates, limit)

    def search_circuits(self, query: str, *, limit: int) -> list[SearchCandidate]:
        page = ElectricalCircuitRepository(self.session).list_page(
            page=1,
            page_size=1_000_000,
            search=None,
            sort_by="circuit_number",
            sort_order=SortOrder.ASC,
            include_deleted=False,
            distribution_id=None,
            protective_device_id=None,
        )
        candidates: list[SearchCandidate] = []
        for projection in page.items:
            record = projection.record
            fields: FieldValues = (
                ("Name", record.name),
                ("Stromkreisnummer", record.circuit_number),
                ("Beschreibung", record.description),
                ("Notizen", record.notes),
                ("Verteilung", projection.distribution_name),
                ("Schutzgerät", projection.protective_device_name),
                ("Schutzgeräte-Code", projection.protective_device_code),
            )
            matched = _matched_fields(query, fields)
            if not matched:
                continue
            subtitle_parts: list[str] = []
            if record.circuit_number:
                subtitle_parts.append(f"Stromkreis {record.circuit_number}")
            subtitle_parts.append(projection.distribution_name)
            if projection.protective_device_name:
                subtitle_parts.append(projection.protective_device_name)
            candidates.append(
                SearchCandidate(
                    result_type=SearchResultType.ELECTRICAL_CIRCUIT,
                    id=record.id,
                    title=record.name,
                    subtitle=" · ".join(subtitle_parts),
                    description=record.description or record.notes,
                    route=f"/electrical/circuits/{record.id}",
                    archived=False,
                    matched_fields=matched,
                    rank=_rank(
                        query,
                        title=record.name,
                        exact_values=(record.circuit_number,),
                        fields=fields,
                    ),
                )
            )
        return _sort_and_limit(candidates, limit)

    def search_wiki_pages(self, query: str, *, limit: int) -> list[SearchCandidate]:
        pages = self.session.exec(select(WikiPage).where(WikiPage.deleted_at.is_(None))).all()
        candidates: list[SearchCandidate] = []
        for page in pages:
            fields: FieldValues = (
                ("Titel", page.title),
                ("Inhalt", page.content),
                ("Slug", page.slug),
            )
            matched = _matched_fields(query, fields)
            if not matched:
                continue
            excerpt = page.content.strip().replace("\n", " ")[:240] or None
            candidates.append(
                SearchCandidate(
                    result_type=SearchResultType.WIKI_PAGE,
                    id=page.id,
                    title=page.title,
                    subtitle="Wiki-Seite",
                    description=excerpt,
                    route=f"/wiki?page={page.id}",
                    archived=False,
                    matched_fields=matched,
                    rank=_rank(
                        query,
                        title=page.title,
                        exact_values=(page.slug,),
                        fields=fields,
                    ),
                )
            )
        return _sort_and_limit(candidates, limit)

    def search_network_devices(self, query: str, *, limit: int) -> list[SearchCandidate]:
        assets = {item.id: item for item in self.session.exec(select(Asset)).all()}
        asset_types = {item.id: item for item in self.session.exec(select(AssetType)).all()}
        products = {item.id: item for item in self.session.exec(select(Product)).all()}
        locations = {item.id: item for item in self.session.exec(select(Location)).all()}
        interfaces = self.session.exec(select(NetworkInterface)).all()
        addresses = self.session.exec(select(NetworkAddress)).all()
        segments = {item.id: item for item in self.session.exec(select(NetworkSegment)).all()}
        candidates: list[SearchCandidate] = []
        for device in self.session.exec(select(NetworkDevice)).all():
            if device.deleted_at is not None:
                continue
            asset = assets.get(device.asset_id)
            if asset is None or asset.deleted_at is not None:
                continue
            asset_type = asset_types.get(asset.asset_type_id)
            product = products.get(asset.product_id) if asset.product_id else None
            location = locations.get(asset.location_id) if asset.location_id else None
            device_interfaces = [
                item
                for item in interfaces
                if item.network_device_id == device.id and item.deleted_at is None
            ]
            device_interface_ids = {item.id for item in device_interfaces}
            device_addresses = [
                item
                for item in addresses
                if item.interface_id in device_interface_ids and item.deleted_at is None
            ]
            mac_values = ", ".join(item.mac_address or "" for item in device_interfaces)
            ip_values = ", ".join(item.address for item in device_addresses)
            segment_values = ", ".join(
                segments[item.segment_id].name
                for item in device_addresses
                if item.segment_id in segments
            )
            vlan_values = ", ".join(
                str(segments[item.segment_id].vlan_id)
                for item in device_addresses
                if item.segment_id in segments and segments[item.segment_id].vlan_id is not None
            )
            fields: FieldValues = (
                ("Name", asset.name),
                ("DocOfHome-Code", asset.jarvis_code),
                ("Hostname", device.hostname),
                ("Rolle", device.role),
                ("Asset-Typ", asset_type.name if asset_type else None),
                ("Produkt", product.name if product else None),
                ("Standort", location.name if location else None),
                ("MAC-Adresse", mac_values),
                ("IP-Adresse", ip_values),
                ("Netz", segment_values),
                ("VLAN", vlan_values),
                ("Notizen", device.notes),
            )
            matched = _matched_fields(query, fields)
            if not matched:
                continue
            subtitle = " · ".join(
                value
                for value in (device.hostname, device.role, location.name if location else None)
                if value
            )
            candidates.append(
                SearchCandidate(
                    result_type=SearchResultType.NETWORK_DEVICE,
                    id=device.id,
                    title=asset.name,
                    subtitle=subtitle or "Netzwerkgerät",
                    description=ip_values or device.notes,
                    route=f"/network/devices/{device.id}",
                    archived=False,
                    matched_fields=matched,
                    rank=_rank(
                        query,
                        title=asset.name,
                        exact_values=(
                            asset.jarvis_code,
                            device.hostname,
                            *tuple(item.address for item in device_addresses),
                        ),
                        fields=fields,
                    ),
                )
            )
        return _sort_and_limit(candidates, limit)

    def search_network_segments(self, query: str, *, limit: int) -> list[SearchCandidate]:
        candidates: list[SearchCandidate] = []
        for segment in self.session.exec(select(NetworkSegment)).all():
            if segment.deleted_at is not None:
                continue
            fields: FieldValues = (
                ("Name", segment.name),
                ("Netz", segment.cidr),
                ("VLAN", str(segment.vlan_id) if segment.vlan_id is not None else None),
                ("Gateway", segment.gateway),
                ("DNS", segment.dns_servers_json),
                ("Beschreibung", segment.description),
            )
            matched = _matched_fields(query, fields)
            if not matched:
                continue
            vlan = f"VLAN {segment.vlan_id} · " if segment.vlan_id is not None else ""
            candidates.append(
                SearchCandidate(
                    result_type=SearchResultType.NETWORK_SEGMENT,
                    id=segment.id,
                    title=segment.name,
                    subtitle=f"{vlan}{segment.cidr}",
                    description=segment.description
                    or (f"Gateway {segment.gateway}" if segment.gateway else None),
                    route=f"/network?tab=segments&segment={segment.id}",
                    archived=False,
                    matched_fields=matched,
                    rank=_rank(
                        query,
                        title=segment.name,
                        exact_values=(
                            segment.cidr,
                            str(segment.vlan_id) if segment.vlan_id is not None else None,
                        ),
                        fields=fields,
                    ),
                )
            )
        return _sort_and_limit(candidates, limit)

    def search_consumption_meters(self, query: str, *, limit: int) -> list[SearchCandidate]:
        type_labels = {
            "water": "Wasser",
            "electricity_grid": "Strom Netzbezug",
            "electricity_pv": "PV-Erzeugung",
            "electricity_feed_in": "Netzeinspeisung",
            "gas": "Gas",
            "heat": "Wärme",
            "oil": "Heizöl",
            "other": "Sonstiges",
        }
        assets = {item.id: item for item in self.session.exec(select(Asset)).all()}
        location_paths = {
            projection.record.id: projection.path
            for projection in LocationRepository(self.session).tree_locations(include_deleted=True)
        }
        candidates: list[SearchCandidate] = []
        for meter in self.session.exec(select(ConsumptionMeter)).all():
            if meter.deleted_at is not None:
                continue
            asset = assets.get(meter.asset_id) if meter.asset_id else None
            location_path = location_paths.get(meter.location_id, "") if meter.location_id else ""
            type_label = type_labels.get(meter.meter_type, meter.meter_type)
            fields: FieldValues = (
                ("Name", meter.name),
                ("Zählertyp", type_label),
                ("Seriennummer", meter.serial_number),
                ("Einheit", meter.unit),
                ("Asset", asset.name if asset else None),
                ("DocOfHome-Code", asset.jarvis_code if asset else None),
                ("Standort", location_path),
                ("Home Assistant", meter.home_assistant_entity_id),
                ("Notizen", meter.notes),
            )
            matched = _matched_fields(query, fields)
            if not matched:
                continue
            subtitle_parts = [type_label]
            if location_path:
                subtitle_parts.append(location_path)
            elif asset:
                subtitle_parts.append(asset.name)
            candidates.append(
                SearchCandidate(
                    result_type=SearchResultType.CONSUMPTION_METER,
                    id=meter.id,
                    title=meter.name,
                    subtitle=" · ".join(subtitle_parts),
                    description=meter.notes,
                    route=f"/consumption?tab=meters&meter={meter.id}",
                    archived=False,
                    matched_fields=matched,
                    rank=_rank(
                        query,
                        title=meter.name,
                        exact_values=(meter.serial_number, meter.home_assistant_entity_id),
                        fields=fields,
                    ),
                )
            )
        return _sort_and_limit(candidates, limit)
