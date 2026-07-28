import json
from datetime import UTC, datetime
from ipaddress import ip_address, ip_network
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.models.integration_setting import IntegrationSetting
from app.models.asset_engine import Asset, AssetType, Location, Product
from app.models.network import (
    NetworkAddress,
    NetworkConnection,
    NetworkDevice,
    NetworkInterface,
    NetworkObservedAddress,
    NetworkAddressChange,
    NetworkSegment,
)
from app.repositories.network import NetworkRepository
from app.schemas.network import (
    NetworkAddressRead,
    NetworkAddressWrite,
    NetworkAssignmentType,
    NetworkConnectionRead,
    NetworkConnectionStatus,
    NetworkConnectionType,
    NetworkConnectionWrite,
    NetworkDeviceCandidateRead,
    NetworkDeviceRead,
    NetworkDeviceWrite,
    NetworkInterfaceRead,
    NetworkInterfaceType,
    NetworkInterfaceWrite,
    NetworkIpActionRead,
    NetworkIpOverviewRead,
    NetworkIpStatus,
    NetworkPoeMode,
    NetworkRole,
    NetworkSegmentRead,
    NetworkSegmentWrite,
    NetworkSummaryRead,
    NetworkTopologyEdgeRead,
    NetworkTopologyNodeRead,
    NetworkTopologyRead,
)

from app.schemas.release import FritzBoxDeviceRead


class NetworkError(RuntimeError):
    """Base class for safe network module domain failures."""


class NetworkNotFoundError(NetworkError):
    pass


class NetworkValidationError(NetworkError):
    pass


class NetworkConflictError(NetworkError):
    pass


class NetworkService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = NetworkRepository(session)

    # Devices
    def list_devices(
        self,
        *,
        search: str | None = None,
        role: NetworkRole | None = None,
        include_archived: bool = False,
    ) -> list[NetworkDeviceRead]:
        normalized = (search or "").strip().casefold()
        items: list[NetworkDeviceRead] = []
        for record in self.repository.list_devices(include_deleted=include_archived):
            read = self._device_read(record)
            if read.archived and not include_archived:
                continue
            if role is not None and read.role != role:
                continue
            if (
                normalized
                and normalized
                not in " ".join(
                    filter(
                        None,
                        (
                            read.asset_name,
                            read.asset_code,
                            read.asset_type,
                            read.product_name,
                            read.location_name,
                            read.hostname,
                            read.role.value,
                            read.notes,
                        ),
                    )
                ).casefold()
            ):
                continue
            items.append(read)
        return sorted(items, key=lambda item: (item.asset_name.casefold(), str(item.id)))

    def get_device(self, record_id: UUID, *, include_archived: bool = False) -> NetworkDeviceRead:
        record = self.repository.get_device(record_id, include_deleted=include_archived)
        if record is None:
            raise NetworkNotFoundError("Netzwerkgerät wurde nicht gefunden")
        read = self._device_read(record)
        if read.archived and not include_archived:
            raise NetworkNotFoundError("Netzwerkgerät wurde nicht gefunden")
        return read

    def device_candidates(self) -> list[NetworkDeviceCandidateRead]:
        active_device_assets = {
            item.asset_id for item in self.repository.list_devices(include_deleted=False)
        }
        asset_types = {item.id: item for item in self.session.exec(select(AssetType)).all()}
        products = {item.id: item for item in self.session.exec(select(Product)).all()}
        locations = {item.id: item for item in self.session.exec(select(Location)).all()}
        result: list[NetworkDeviceCandidateRead] = []
        for asset in self.session.exec(
            select(Asset).where(col(Asset.deleted_at).is_(None)).order_by(Asset.name)
        ).all():
            if asset.id in active_device_assets:
                continue
            asset_type = asset_types.get(asset.asset_type_id)
            product = products.get(asset.product_id) if asset.product_id else None
            location = locations.get(asset.location_id) if asset.location_id else None
            result.append(
                NetworkDeviceCandidateRead(
                    asset_id=asset.id,
                    name=asset.name,
                    jarvis_code=asset.jarvis_code,
                    asset_type=asset_type.name if asset_type else "Asset",
                    product_name=product.name if product else None,
                    location_name=location.name if location else None,
                )
            )
        return result

    def create_device(self, payload: NetworkDeviceWrite) -> NetworkDeviceRead:
        self._require_active_asset(payload.asset_id)
        if self.repository.active_device_for_asset(payload.asset_id) is not None:
            raise NetworkConflictError("Für dieses Asset existiert bereits ein Netzwerkgerät")
        record = NetworkDevice(
            asset_id=payload.asset_id,
            role=payload.role.value,
            hostname=payload.hostname,
            management_url=payload.management_url,
            notes=payload.notes,
        )
        self.session.add(record)
        self._commit()
        return self._device_read(record)

    def update_device(self, record_id: UUID, payload: NetworkDeviceWrite) -> NetworkDeviceRead:
        record = self._require_device(record_id)
        if payload.asset_id != record.asset_id:
            raise NetworkValidationError("Das zugrunde liegende Asset kann nicht geändert werden")
        self._require_active_asset(payload.asset_id)
        record.role = payload.role.value
        record.hostname = payload.hostname
        record.management_url = payload.management_url
        record.notes = payload.notes
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        self._commit()
        return self._device_read(record)

    def delete_device(self, record_id: UUID) -> None:
        record = self._require_device(record_id)
        now = datetime.now(UTC)
        interfaces = self.repository.list_interfaces(device_id=record.id)
        interface_ids = {item.id for item in interfaces}
        for address in self.repository.list_addresses(device_id=record.id):
            address.deleted_at = now
            address.updated_at = now
            self.session.add(address)
        for connection in self.repository.list_connections():
            if (
                connection.source_interface_id in interface_ids
                or connection.target_interface_id in interface_ids
            ):
                connection.deleted_at = now
                connection.updated_at = now
                self.session.add(connection)
        for interface in interfaces:
            interface.deleted_at = now
            interface.updated_at = now
            self.session.add(interface)
        record.deleted_at = now
        record.updated_at = now
        self.session.add(record)
        self._commit()

    # Segments
    def list_segments(self) -> list[NetworkSegmentRead]:
        return [self._segment_read(item) for item in self.repository.list_segments()]

    def create_segment(self, payload: NetworkSegmentWrite) -> NetworkSegmentRead:
        self._validate_segment_unique(payload)
        record = NetworkSegment(
            name=payload.name,
            cidr=payload.cidr,
            vlan_id=payload.vlan_id,
            gateway=payload.gateway,
            dns_servers_json=json.dumps(payload.dns_servers, separators=(",", ":")),
            description=payload.description,
        )
        self.session.add(record)
        self._commit()
        return self._segment_read(record)

    def update_segment(self, record_id: UUID, payload: NetworkSegmentWrite) -> NetworkSegmentRead:
        record = self._require_segment(record_id)
        self._validate_segment_unique(payload, exclude_id=record.id)
        for address in self.repository.list_addresses(segment_id=record.id):
            if ip_address(address.address) not in ip_network(payload.cidr):
                raise NetworkConflictError(
                    f"Die vorhandene Adresse {address.address} liegt nicht im neuen Netz"
                )
        record.name = payload.name
        record.cidr = payload.cidr
        record.vlan_id = payload.vlan_id
        record.gateway = payload.gateway
        record.dns_servers_json = json.dumps(payload.dns_servers, separators=(",", ":"))
        record.description = payload.description
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        self._commit()
        return self._segment_read(record)

    def delete_segment(self, record_id: UUID) -> None:
        record = self._require_segment(record_id)
        if self.repository.list_addresses(segment_id=record.id):
            raise NetworkConflictError(
                "Das Netz kann erst archiviert werden, wenn keine IP-Adressen mehr zugeordnet sind"
            )
        record.deleted_at = datetime.now(UTC)
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        self._commit()

    # Interfaces
    def list_interfaces(self, *, device_id: UUID | None = None) -> list[NetworkInterfaceRead]:
        if device_id is not None:
            self._require_device(device_id)
        return [
            self._interface_read(item)
            for item in self.repository.list_interfaces(device_id=device_id)
        ]

    def create_interface(self, payload: NetworkInterfaceWrite) -> NetworkInterfaceRead:
        self._require_device(payload.network_device_id)
        self._validate_interface_unique(payload)
        self._validate_logical_interface(payload)
        if payload.is_primary:
            for item in self.repository.list_interfaces(device_id=payload.network_device_id):
                item.is_primary = False
                self.session.add(item)
        record = NetworkInterface(
            network_device_id=payload.network_device_id,
            name=payload.name,
            interface_type=payload.interface_type.value,
            mac_address=payload.mac_address,
            speed_mbps=payload.speed_mbps,
            poe_mode=payload.poe_mode.value,
            enabled=payload.enabled,
            is_primary=payload.is_primary,
            logical_interface_id=payload.logical_interface_id,
            description=payload.description,
        )
        self.session.add(record)
        self._commit()
        return self._interface_read(record)

    def update_interface(
        self, record_id: UUID, payload: NetworkInterfaceWrite
    ) -> NetworkInterfaceRead:
        record = self._require_interface(record_id)
        if payload.network_device_id != record.network_device_id:
            raise NetworkValidationError(
                "Eine Schnittstelle kann nicht auf ein anderes Gerät verschoben werden"
            )
        self._validate_interface_unique(payload, exclude_id=record.id)
        self._validate_logical_interface(payload, record_id=record.id)
        if payload.is_primary:
            for item in self.repository.list_interfaces(device_id=record.network_device_id):
                if item.id != record.id:
                    item.is_primary = False
                    self.session.add(item)
        if (
            record.interface_type == NetworkInterfaceType.VIRTUAL.value
            and payload.interface_type != NetworkInterfaceType.VIRTUAL
            and any(
                item.logical_interface_id == record.id
                for item in self.repository.list_interfaces(
                    device_id=record.network_device_id
                )
            )
        ):
            raise NetworkConflictError(
                "Eine logische Schnittstelle mit zugeordneten Ports muss virtuell bleiben"
            )
        record.name = payload.name
        record.interface_type = payload.interface_type.value
        record.mac_address = payload.mac_address
        record.speed_mbps = payload.speed_mbps
        record.poe_mode = payload.poe_mode.value
        record.enabled = payload.enabled
        record.is_primary = payload.is_primary
        record.logical_interface_id = payload.logical_interface_id
        record.description = payload.description
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        self._commit()
        return self._interface_read(record)

    def delete_interface(self, record_id: UUID) -> None:
        record = self._require_interface(record_id)
        now = datetime.now(UTC)
        for member in self.repository.list_interfaces(device_id=record.network_device_id):
            if member.logical_interface_id == record.id:
                member.logical_interface_id = None
                member.updated_at = now
                self.session.add(member)
        for address in self.repository.list_addresses(interface_id=record.id):
            address.deleted_at = now
            address.updated_at = now
            self.session.add(address)
        for connection in self.repository.list_connections():
            if record.id in {connection.source_interface_id, connection.target_interface_id}:
                connection.deleted_at = now
                connection.updated_at = now
                self.session.add(connection)
        record.deleted_at = now
        record.updated_at = now
        self.session.add(record)
        self._commit()

    # Addresses
    def list_addresses(
        self,
        *,
        interface_id: UUID | None = None,
        device_id: UUID | None = None,
        segment_id: UUID | None = None,
    ) -> list[NetworkAddressRead]:
        if interface_id is not None:
            self._require_interface(interface_id)
        if device_id is not None:
            self._require_device(device_id)
        if segment_id is not None:
            self._require_segment(segment_id)
        return [
            self._address_read(item)
            for item in self.repository.list_addresses(
                interface_id=interface_id,
                device_id=device_id,
                segment_id=segment_id,
            )
        ]

    def create_address(self, payload: NetworkAddressWrite) -> NetworkAddressRead:
        interface = self._require_interface(payload.interface_id)
        self._validate_address(payload)
        record = NetworkAddress(
            interface_id=payload.interface_id,
            segment_id=payload.segment_id,
            address=payload.address,
            assignment_type=payload.assignment_type.value,
            hostname=payload.hostname,
            is_primary=payload.is_primary,
            notes=payload.notes,
        )
        if payload.is_primary:
            self._clear_primary_addresses(interface.network_device_id)
        self.session.add(record)
        self._commit()
        return self._address_read(record)

    def update_address(self, record_id: UUID, payload: NetworkAddressWrite) -> NetworkAddressRead:
        record = self._require_address(record_id)
        if payload.interface_id != record.interface_id:
            raise NetworkValidationError(
                "Eine IP-Adresse kann nicht auf eine andere Schnittstelle verschoben werden"
            )
        interface = self._require_interface(record.interface_id)
        self._validate_address(payload, exclude_id=record.id)
        if payload.is_primary:
            self._clear_primary_addresses(interface.network_device_id, exclude_id=record.id)
        record.segment_id = payload.segment_id
        record.address = payload.address
        record.assignment_type = payload.assignment_type.value
        record.hostname = payload.hostname
        record.is_primary = payload.is_primary
        record.notes = payload.notes
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        self._commit()
        return self._address_read(record)

    def delete_address(self, record_id: UUID) -> None:
        record = self._require_address(record_id)
        record.deleted_at = datetime.now(UTC)
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        self._commit()

    # Observed IP addresses / integration reconciliation
    @staticmethod
    def _normalized_mac(value: str | None) -> str | None:
        if not value:
            return None
        compact = "".join(char for char in value if char in "0123456789abcdefABCDEF")
        if len(compact) != 12:
            return None
        return ":".join(compact[index:index + 2] for index in range(0, 12, 2)).upper()

    def sync_observed_addresses(
        self, devices: list[FritzBoxDeviceRead], *, source: str = "fritzbox"
    ) -> None:
        now = datetime.now(UTC)
        existing = list(self.session.exec(
            select(NetworkObservedAddress).where(
                NetworkObservedAddress.source == source,
                col(NetworkObservedAddress.deleted_at).is_(None),
            )
        ).all())
        for item in existing:
            item.active = False
            item.updated_at = now
            self.session.add(item)
        interfaces = self.repository.list_interfaces()
        by_mac = {
            self._normalized_mac(item.mac_address): item
            for item in interfaces
            if self._normalized_mac(item.mac_address)
        }
        for device in devices:
            if not device.ipv4:
                continue
            try:
                address = str(ip_address(device.ipv4))
            except ValueError:
                continue
            mac = self._normalized_mac(device.mac_address)
            interface = by_mac.get(mac) if mac else None
            record = next((
                item for item in existing
                if item.address == address
                and item.mac_address == mac
                and item.source == source
            ), None)
            assignment = (
                NetworkAssignmentType.RESERVATION.value
                if device.dhcp_reservation
                else NetworkAssignmentType.DHCP.value
            )
            if record is None:
                record = NetworkObservedAddress(
                    interface_id=interface.id if interface else None,
                    mac_address=mac,
                    address=address,
                    hostname=device.name,
                    assignment_type=assignment,
                    source=source,
                    active=True,
                    last_seen_at=device.last_seen or now,
                )
            else:
                record.interface_id = interface.id if interface else None
                record.hostname = device.name
                record.assignment_type = assignment
                record.active = True
                record.last_seen_at = device.last_seen or now
                record.updated_at = now
            self.session.add(record)
        self._commit()

    def list_ip_overview(
        self, *, device_id: UUID | None = None, status: NetworkIpStatus | None = None
    ) -> list[NetworkIpOverviewRead]:
        interfaces = self.repository.list_interfaces(device_id=device_id)
        interface_by_id = {item.id: item for item in interfaces}
        devices = {item.id: item for item in self.repository.list_devices()}
        assets = {item.id: item for item in self.session.exec(select(Asset)).all()}
        documented = [
            item for item in self.repository.list_addresses()
            if item.interface_id in interface_by_id
        ]
        all_observed = list(self.session.exec(
            select(NetworkObservedAddress).where(
                NetworkObservedAddress.active == True,  # noqa: E712
                col(NetworkObservedAddress.deleted_at).is_(None),
            )
        ).all())
        observed = [
            item for item in all_observed
            if device_id is None
            or (item.interface_id is not None and item.interface_id in interface_by_id)
        ]
        integration_active = self.session.exec(
            select(IntegrationSetting).where(
                IntegrationSetting.kind == "fritzbox",
                IntegrationSetting.enabled == True,  # noqa: E712
            )
        ).first() is not None
        observed_by_interface: dict[UUID, list[NetworkObservedAddress]] = {}
        for item in observed:
            if item.interface_id is not None:
                observed_by_interface.setdefault(item.interface_id, []).append(item)
        conflicting_addresses = {
            address for address in {item.address for item in all_observed}
            if len({item.mac_address for item in all_observed if item.address == address and item.mac_address}) > 1
        }
        rows: list[NetworkIpOverviewRead] = []
        used_observed: set[UUID] = set()
        for address in documented:
            interface = interface_by_id[address.interface_id]
            device = devices.get(interface.network_device_id)
            asset = assets.get(device.asset_id) if device else None
            candidates = observed_by_interface.get(interface.id, [])
            same = next((item for item in candidates if item.address == address.address), None)
            chosen = same or (max(candidates, key=lambda item: item.last_seen_at) if candidates else None)
            if chosen:
                used_observed.add(chosen.id)
            row_status = (
                NetworkIpStatus.CONFLICT
                if (chosen and chosen.address in conflicting_addresses) or address.address in conflicting_addresses
                else NetworkIpStatus.MATCH
                if same
                else NetworkIpStatus.MISMATCH
                if chosen
                else NetworkIpStatus.NOT_DETECTED
                if integration_active
                else NetworkIpStatus.NO_INTEGRATION
            )
            row = NetworkIpOverviewRead(
                key=f"documented:{address.id}",
                status=row_status,
                device_id=device.id if device else None,
                device_name=asset.name if asset else "Unbekanntes Gerät",
                interface_id=interface.id,
                interface_name=interface.name,
                documented_address_id=address.id,
                documented_address=address.address,
                mac_address=interface.mac_address,
                assignment_type=self._assignment_type(address.assignment_type),
                observed_address_id=chosen.id if chosen else None,
                observed_address=chosen.address if chosen else None,
                source=chosen.source if chosen else None,
                last_seen_at=chosen.last_seen_at if chosen else None,
                ignored=chosen.ignored if chosen else False,
            )
            if status is None or row.status == status:
                rows.append(row)
        for item in observed:
            if item.id in used_observed:
                continue
            interface = interface_by_id.get(item.interface_id) if item.interface_id else None
            device = devices.get(interface.network_device_id) if interface else None
            asset = assets.get(device.asset_id) if device else None
            row_status = NetworkIpStatus.CONFLICT if item.address in conflicting_addresses else NetworkIpStatus.OBSERVED_ONLY
            row = NetworkIpOverviewRead(
                key=f"observed:{item.id}",
                status=row_status,
                device_id=device.id if device else None,
                device_name=asset.name if asset else (item.hostname or "Nur erkannt"),
                interface_id=interface.id if interface else None,
                interface_name=interface.name if interface else None,
                documented_address_id=None,
                documented_address=None,
                mac_address=item.mac_address,
                assignment_type=self._assignment_type(item.assignment_type),
                observed_address_id=item.id,
                observed_address=item.address,
                source=item.source,
                last_seen_at=item.last_seen_at,
                ignored=item.ignored,
            )
            if status is None or row.status == status:
                rows.append(row)
        def sort_key(row: NetworkIpOverviewRead) -> tuple[int, int, str]:
            candidate = row.documented_address or row.observed_address or ""
            try:
                parsed = ip_address(candidate)
                return (0, int(parsed), row.device_name.casefold())
            except ValueError:
                return (1, 0, row.device_name.casefold())
        return sorted(rows, key=sort_key)

    def accept_observed_address(self, observed_id: UUID) -> NetworkIpActionRead:
        observed = self.session.get(NetworkObservedAddress, observed_id)
        if observed is None or observed.deleted_at is not None or not observed.active:
            raise NetworkNotFoundError("Die erkannte IP-Adresse wurde nicht gefunden")
        if observed.interface_id is None:
            raise NetworkValidationError(
                "Die erkannte Adresse ist keiner dokumentierten Schnittstelle zugeordnet"
            )
        existing = self.repository.list_addresses(interface_id=observed.interface_id)
        documented = next(
            (item for item in existing if item.is_primary),
            existing[0] if existing else None,
        )
        old_address = documented.address if documented else None
        segment_id = self._matching_segment_id(
            observed.address,
            preferred_id=documented.segment_id if documented else None,
        )
        payload = NetworkAddressWrite(
            interface_id=observed.interface_id,
            segment_id=segment_id,
            address=observed.address,
            assignment_type=self._assignment_type(observed.assignment_type),
            hostname=observed.hostname,
            is_primary=documented.is_primary if documented else True,
            notes=documented.notes if documented else "Aus FRITZ!Box übernommen",
        )
        self._validate_address(payload, exclude_id=documented.id if documented else None)
        interface = self._require_interface(observed.interface_id)
        if payload.is_primary:
            self._clear_primary_addresses(
                interface.network_device_id,
                exclude_id=documented.id if documented else None,
            )
        now = datetime.now(UTC)
        if documented is None:
            documented = NetworkAddress(
                interface_id=payload.interface_id,
                segment_id=payload.segment_id,
                address=payload.address,
                assignment_type=payload.assignment_type.value,
                hostname=payload.hostname,
                is_primary=payload.is_primary,
                notes=payload.notes,
            )
        else:
            documented.segment_id = payload.segment_id
            documented.address = payload.address
            documented.assignment_type = payload.assignment_type.value
            documented.hostname = payload.hostname
            documented.is_primary = payload.is_primary
            documented.notes = payload.notes
            documented.updated_at = now
        observed.ignored = False
        observed.updated_at = now
        self.session.add(documented)
        self.session.add(observed)
        self.session.add(
            NetworkAddressChange(
                observed_address_id=observed.id,
                documented_address_id=documented.id,
                action="accept",
                old_address=old_address,
                new_address=observed.address,
            )
        )
        self._commit()
        return NetworkIpActionRead(documented_address_id=documented.id, status="accepted")

    def _matching_segment_id(
        self, address: str, *, preferred_id: UUID | None
    ) -> UUID | None:
        parsed = ip_address(address)
        if preferred_id is not None:
            preferred = self.repository.get_segment(preferred_id)
            if preferred is not None and parsed in ip_network(preferred.cidr):
                return preferred.id
        matching = [
            segment
            for segment in self.repository.list_segments()
            if parsed in ip_network(segment.cidr)
        ]
        matching.sort(
            key=lambda segment: (
                -ip_network(segment.cidr).prefixlen,
                segment.name.casefold(),
                str(segment.id),
            )
        )
        return matching[0].id if matching else None

    def ignore_observed_address(self, observed_id: UUID) -> NetworkIpActionRead:
        observed = self.session.get(NetworkObservedAddress, observed_id)
        if observed is None or observed.deleted_at is not None:
            raise NetworkNotFoundError("Die erkannte IP-Adresse wurde nicht gefunden")
        observed.ignored = True
        observed.updated_at = datetime.now(UTC)
        self.session.add(observed)
        self.session.add(NetworkAddressChange(
            observed_address_id=observed.id,
            documented_address_id=None,
            action="ignore",
            old_address=None,
            new_address=observed.address,
        ))
        self._commit()
        return NetworkIpActionRead(documented_address_id=None, status="ignored")

    # Connections
    def list_connections(self, *, device_id: UUID | None = None) -> list[NetworkConnectionRead]:
        if device_id is not None:
            self._require_device(device_id)
        return [
            self._connection_read(item)
            for item in self.repository.list_connections(device_id=device_id)
        ]

    def create_connection(self, payload: NetworkConnectionWrite) -> NetworkConnectionRead:
        source_id, target_id = self._normalize_endpoints(
            payload.source_interface_id,
            payload.target_interface_id,
        )
        self._require_interface(source_id)
        self._require_interface(target_id)
        if self.repository.active_connection_for_endpoints(source_id, target_id) is not None:
            raise NetworkConflictError(
                "Zwischen diesen Schnittstellen besteht bereits eine Verbindung"
            )
        record = NetworkConnection(
            source_interface_id=source_id,
            target_interface_id=target_id,
            connection_type=payload.connection_type.value,
            status=payload.status.value,
            cable_type=payload.cable_type,
            cable_label=payload.cable_label,
            description=payload.description,
        )
        self.session.add(record)
        self._commit()
        return self._connection_read(record)

    def update_connection(
        self, record_id: UUID, payload: NetworkConnectionWrite
    ) -> NetworkConnectionRead:
        record = self._require_connection(record_id)
        source_id, target_id = self._normalize_endpoints(
            payload.source_interface_id,
            payload.target_interface_id,
        )
        self._require_interface(source_id)
        self._require_interface(target_id)
        if (
            self.repository.active_connection_for_endpoints(
                source_id,
                target_id,
                exclude_id=record.id,
            )
            is not None
        ):
            raise NetworkConflictError(
                "Zwischen diesen Schnittstellen besteht bereits eine Verbindung"
            )
        record.source_interface_id = source_id
        record.target_interface_id = target_id
        record.connection_type = payload.connection_type.value
        record.status = payload.status.value
        record.cable_type = payload.cable_type
        record.cable_label = payload.cable_label
        record.description = payload.description
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        self._commit()
        return self._connection_read(record)

    def delete_connection(self, record_id: UUID) -> None:
        record = self._require_connection(record_id)
        record.deleted_at = datetime.now(UTC)
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        self._commit()

    def summary(self) -> NetworkSummaryRead:
        devices = self.list_devices()
        interfaces = self.repository.list_interfaces()
        addresses = self.repository.list_addresses()
        connections = self.repository.list_connections()
        connected_ids = {
            endpoint
            for connection in connections
            if connection.status == NetworkConnectionStatus.ACTIVE.value
            for endpoint in (connection.source_interface_id, connection.target_interface_id)
        }
        physical_types = {
            NetworkInterfaceType.ETHERNET.value,
            NetworkInterfaceType.FIBER.value,
            NetworkInterfaceType.OTHER.value,
        }
        free_interfaces = [
            item for item in interfaces
            if (
                item.enabled
                and item.interface_type in physical_types
                and item.id not in connected_ids
            )
        ]
        by_device: dict[UUID, list[NetworkInterface]] = {}
        for item in interfaces:
            by_device.setdefault(item.network_device_id, []).append(item)
        devices_without_connection = 0
        for device in devices:
            device_interfaces = [item for item in by_device.get(device.id, []) if item.enabled]
            if not device_interfaces:
                continue
            has_connection = any(item.id in connected_ids for item in device_interfaces)
            has_wireless_uplink = any(
                item.interface_type
                in {
                    NetworkInterfaceType.WIFI.value,
                    NetworkInterfaceType.CELLULAR.value,
                }
                for item in device_interfaces
            )
            if not has_connection and not has_wireless_uplink:
                devices_without_connection += 1
        return NetworkSummaryRead(
            device_count=len(devices),
            segment_count=len(self.repository.list_segments()),
            interface_count=len(interfaces),
            address_count=len(addresses),
            connection_count=len(connections),
            free_interface_count=len(free_interfaces),
            device_without_connection_count=devices_without_connection,
            unconnected_interface_count=len(free_interfaces),
        )

    def topology(self) -> NetworkTopologyRead:
        devices = self.list_devices()
        interfaces = {item.id: item for item in self.repository.list_interfaces()}
        nodes = [
            NetworkTopologyNodeRead(
                id=item.id,
                asset_id=item.asset_id,
                name=item.asset_name,
                role=item.role,
                hostname=item.hostname,
                location_name=item.location_name,
                interface_count=item.interface_count,
            )
            for item in devices
        ]
        active_device_ids = {item.id for item in devices}
        edges: list[NetworkTopologyEdgeRead] = []
        for connection in self.repository.list_connections():
            source = interfaces.get(connection.source_interface_id)
            target = interfaces.get(connection.target_interface_id)
            if source is None or target is None:
                continue
            if (
                source.network_device_id not in active_device_ids
                or target.network_device_id not in active_device_ids
            ):
                continue
            edges.append(
                NetworkTopologyEdgeRead(
                    id=connection.id,
                    source_device_id=source.network_device_id,
                    target_device_id=target.network_device_id,
                    source_label=source.name,
                    target_label=target.name,
                    connection_type=self._connection_type(connection.connection_type),
                    status=self._connection_status(connection.status),
                    cable_label=connection.cable_label,
                )
            )
        return NetworkTopologyRead(nodes=nodes, edges=edges)

    # Validation and projections
    def _require_active_asset(self, asset_id: UUID) -> Asset:
        asset = self.session.get(Asset, asset_id)
        if asset is None or asset.deleted_at is not None:
            raise NetworkValidationError(
                "Das ausgewählte Asset existiert nicht oder ist archiviert"
            )
        return asset

    def _require_device(self, record_id: UUID) -> NetworkDevice:
        record = self.repository.get_device(record_id)
        if record is None:
            raise NetworkNotFoundError("Netzwerkgerät wurde nicht gefunden")
        asset = self.session.get(Asset, record.asset_id)
        if asset is None or asset.deleted_at is not None:
            raise NetworkConflictError("Das zugehörige Asset ist archiviert")
        return record

    def _require_segment(self, record_id: UUID) -> NetworkSegment:
        record = self.repository.get_segment(record_id)
        if record is None:
            raise NetworkNotFoundError("IP-Netz wurde nicht gefunden")
        return record

    def _require_interface(self, record_id: UUID) -> NetworkInterface:
        record = self.repository.get_interface(record_id)
        if record is None:
            raise NetworkNotFoundError("Netzwerkschnittstelle wurde nicht gefunden")
        self._require_device(record.network_device_id)
        return record

    def _require_address(self, record_id: UUID) -> NetworkAddress:
        record = self.repository.get_address(record_id)
        if record is None:
            raise NetworkNotFoundError("IP-Adresse wurde nicht gefunden")
        self._require_interface(record.interface_id)
        return record

    def _require_connection(self, record_id: UUID) -> NetworkConnection:
        record = self.repository.get_connection(record_id)
        if record is None:
            raise NetworkNotFoundError("Netzwerkverbindung wurde nicht gefunden")
        return record

    def _validate_segment_unique(
        self,
        payload: NetworkSegmentWrite,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        if self.repository.active_segment_by_name(payload.name, exclude_id=exclude_id):
            raise NetworkConflictError("Ein aktives Netz mit diesem Namen existiert bereits")
        if payload.vlan_id is not None and self.repository.active_segment_by_vlan(
            payload.vlan_id, exclude_id=exclude_id
        ):
            raise NetworkConflictError("Diese VLAN-ID ist bereits vergeben")

    def _validate_interface_unique(
        self,
        payload: NetworkInterfaceWrite,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        if self.repository.active_interface_by_name(
            payload.network_device_id,
            payload.name,
            exclude_id=exclude_id,
        ):
            raise NetworkConflictError(
                "An diesem Gerät existiert bereits eine Schnittstelle mit diesem Namen"
            )
        if payload.mac_address is not None and self.repository.active_interface_by_mac(
            payload.mac_address, exclude_id=exclude_id
        ):
            raise NetworkConflictError(
                "Diese MAC-Adresse ist bereits einer aktiven Schnittstelle zugeordnet"
            )

    def _validate_logical_interface(
        self,
        payload: NetworkInterfaceWrite,
        *,
        record_id: UUID | None = None,
    ) -> None:
        if payload.logical_interface_id is None:
            return
        if payload.interface_type == NetworkInterfaceType.VIRTUAL:
            raise NetworkValidationError(
                "Eine virtuelle Schnittstelle kann nicht Mitglied einer anderen "
                "logischen Schnittstelle sein"
            )
        if payload.logical_interface_id == record_id:
            raise NetworkValidationError(
                "Eine Schnittstelle kann nicht sich selbst zugeordnet werden"
            )
        logical = self.repository.get_interface(payload.logical_interface_id)
        if logical is None or logical.network_device_id != payload.network_device_id:
            raise NetworkValidationError(
                "Die logische Schnittstelle muss zum selben Gerät gehören"
            )
        if logical.interface_type != NetworkInterfaceType.VIRTUAL.value:
            raise NetworkValidationError(
                "Als logische Schnittstelle kann nur ein virtueller Port bzw. "
                "eine Bridge gewählt werden"
            )

    def _validate_address(
        self,
        payload: NetworkAddressWrite,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        self._require_interface(payload.interface_id)
        if payload.segment_id is not None:
            segment = self._require_segment(payload.segment_id)
            if ip_address(payload.address) not in ip_network(segment.cidr):
                raise NetworkValidationError("Die IP-Adresse liegt nicht im ausgewählten Netz")
        if self.repository.active_address_conflict(
            interface_id=payload.interface_id,
            segment_id=payload.segment_id,
            address=payload.address,
            exclude_id=exclude_id,
        ):
            raise NetworkConflictError(
                "Diese IP-Adresse ist an der Schnittstelle oder im Netz bereits vergeben"
            )

    def _clear_primary_addresses(
        self,
        device_id: UUID,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        for address in self.repository.list_addresses(device_id=device_id):
            if address.id != exclude_id and address.is_primary:
                address.is_primary = False
                address.updated_at = datetime.now(UTC)
                self.session.add(address)

    @staticmethod
    def _normalize_endpoints(source_id: UUID, target_id: UUID) -> tuple[UUID, UUID]:
        if source_id == target_id:
            raise NetworkValidationError(
                "Eine Schnittstelle kann nicht mit sich selbst verbunden werden"
            )
        return (source_id, target_id) if source_id.int < target_id.int else (target_id, source_id)

    def _device_read(self, record: NetworkDevice) -> NetworkDeviceRead:
        asset = self.session.get(Asset, record.asset_id)
        asset_type = self.session.get(AssetType, asset.asset_type_id) if asset else None
        product = (
            self.session.get(Product, asset.product_id) if asset and asset.product_id else None
        )
        location = (
            self.session.get(Location, asset.location_id) if asset and asset.location_id else None
        )
        interfaces = self.repository.list_interfaces(device_id=record.id)
        addresses = self.repository.list_addresses(device_id=record.id)
        connections = self.repository.list_connections(device_id=record.id)
        archived = record.deleted_at is not None or asset is None or asset.deleted_at is not None
        primary = next((item for item in addresses if item.is_primary), None)
        if primary is None and addresses:
            primary = sorted(addresses, key=lambda item: (item.address, str(item.id)))[0]
        return NetworkDeviceRead(
            id=record.id,
            asset_id=record.asset_id,
            asset_name=asset.name if asset else "Unbekanntes Asset",
            asset_code=asset.jarvis_code if asset else "–",
            asset_type=asset_type.name if asset_type else "Asset",
            switch_port_layout=(asset_type.switch_port_layout if asset_type else "odd_even"),
            product_name=product.name if product else None,
            location_name=location.name if location else None,
            role=self._network_role(record.role),
            hostname=record.hostname,
            management_url=record.management_url,
            notes=record.notes,
            primary_address=primary.address if primary else None,
            interface_count=len(interfaces),
            address_count=len(addresses),
            connection_count=len(connections),
            archived=archived,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _segment_read(self, record: NetworkSegment) -> NetworkSegmentRead:
        try:
            dns_servers = json.loads(record.dns_servers_json)
        except (TypeError, json.JSONDecodeError):
            dns_servers = []
        if not isinstance(dns_servers, list):
            dns_servers = []
        return NetworkSegmentRead(
            id=record.id,
            name=record.name,
            cidr=record.cidr,
            vlan_id=record.vlan_id,
            gateway=record.gateway,
            dns_servers=[str(item) for item in dns_servers],
            description=record.description,
            address_count=len(self.repository.list_addresses(segment_id=record.id)),
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _interface_read(self, record: NetworkInterface) -> NetworkInterfaceRead:
        device = self.repository.get_device(record.network_device_id, include_deleted=True)
        asset = self.session.get(Asset, device.asset_id) if device else None
        connections = self.repository.list_connections(device_id=record.network_device_id)
        logical = (
            self.repository.get_interface(record.logical_interface_id, include_deleted=True)
            if record.logical_interface_id else None
        )
        members = [
            item for item in self.repository.list_interfaces(device_id=record.network_device_id)
            if item.logical_interface_id == record.id
        ]
        return NetworkInterfaceRead(
            id=record.id,
            network_device_id=record.network_device_id,
            device_name=asset.name if asset else "Unbekanntes Gerät",
            name=record.name,
            interface_type=self._interface_type(record.interface_type),
            mac_address=record.mac_address,
            speed_mbps=record.speed_mbps,
            poe_mode=self._poe_mode(record.poe_mode),
            enabled=record.enabled,
            is_primary=record.is_primary,
            logical_interface_id=record.logical_interface_id,
            logical_interface_name=logical.name if logical else None,
            member_count=len(members),
            description=record.description,
            address_count=len(self.repository.list_addresses(interface_id=record.id)),
            connection_count=sum(
                record.id in {item.source_interface_id, item.target_interface_id}
                for item in connections
            ),
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _address_read(self, record: NetworkAddress) -> NetworkAddressRead:
        interface = self.repository.get_interface(record.interface_id, include_deleted=True)
        device = (
            self.repository.get_device(interface.network_device_id, include_deleted=True)
            if interface
            else None
        )
        asset = self.session.get(Asset, device.asset_id) if device else None
        segment = (
            self.repository.get_segment(record.segment_id, include_deleted=True)
            if record.segment_id
            else None
        )
        return NetworkAddressRead(
            id=record.id,
            interface_id=record.interface_id,
            interface_name=interface.name if interface else "Unbekannte Schnittstelle",
            network_device_id=interface.network_device_id if interface else UUID(int=0),
            device_name=asset.name if asset else "Unbekanntes Gerät",
            segment_id=record.segment_id,
            segment_name=segment.name if segment else None,
            address=record.address,
            assignment_type=self._assignment_type(record.assignment_type),
            hostname=record.hostname,
            is_primary=record.is_primary,
            notes=record.notes,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _connection_read(self, record: NetworkConnection) -> NetworkConnectionRead:
        source = self.repository.get_interface(record.source_interface_id, include_deleted=True)
        target = self.repository.get_interface(record.target_interface_id, include_deleted=True)
        source_device = (
            self.repository.get_device(source.network_device_id, include_deleted=True)
            if source
            else None
        )
        target_device = (
            self.repository.get_device(target.network_device_id, include_deleted=True)
            if target
            else None
        )
        source_asset = self.session.get(Asset, source_device.asset_id) if source_device else None
        target_asset = self.session.get(Asset, target_device.asset_id) if target_device else None
        return NetworkConnectionRead(
            id=record.id,
            source_interface_id=record.source_interface_id,
            source_interface_name=source.name if source else "Unbekannt",
            source_device_id=source.network_device_id if source else UUID(int=0),
            source_device_name=source_asset.name if source_asset else "Unbekanntes Gerät",
            target_interface_id=record.target_interface_id,
            target_interface_name=target.name if target else "Unbekannt",
            target_device_id=target.network_device_id if target else UUID(int=0),
            target_device_name=target_asset.name if target_asset else "Unbekanntes Gerät",
            connection_type=self._connection_type(record.connection_type),
            status=self._connection_status(record.status),
            cable_type=record.cable_type,
            cable_label=record.cable_label,
            description=record.description,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _network_role(value: object) -> NetworkRole:
        if not isinstance(value, str):
            return NetworkRole.OTHER
        try:
            return NetworkRole(value)
        except (TypeError, ValueError):
            return NetworkRole.OTHER

    @staticmethod
    def _interface_type(value: object) -> NetworkInterfaceType:
        if not isinstance(value, str):
            return NetworkInterfaceType.OTHER
        try:
            return NetworkInterfaceType(value)
        except (TypeError, ValueError):
            return NetworkInterfaceType.OTHER

    @staticmethod
    def _poe_mode(value: object) -> NetworkPoeMode:
        if not isinstance(value, str):
            return NetworkPoeMode.UNKNOWN
        try:
            return NetworkPoeMode(value)
        except (TypeError, ValueError):
            return NetworkPoeMode.UNKNOWN

    @staticmethod
    def _assignment_type(value: object) -> NetworkAssignmentType:
        if not isinstance(value, str):
            return NetworkAssignmentType.UNKNOWN
        try:
            return NetworkAssignmentType(value)
        except (TypeError, ValueError):
            return NetworkAssignmentType.UNKNOWN

    @staticmethod
    def _connection_type(value: object) -> NetworkConnectionType:
        if not isinstance(value, str):
            return NetworkConnectionType.PHYSICAL
        try:
            return NetworkConnectionType(value)
        except (TypeError, ValueError):
            return NetworkConnectionType.PHYSICAL

    @staticmethod
    def _connection_status(value: object) -> NetworkConnectionStatus:
        if not isinstance(value, str):
            return NetworkConnectionStatus.INACTIVE
        try:
            return NetworkConnectionStatus(value)
        except (TypeError, ValueError):
            return NetworkConnectionStatus.INACTIVE

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise NetworkConflictError(
                "Die Netzwerkdaten stehen im Konflikt mit bereits vorhandenen Einträgen"
            ) from exc
        except Exception:
            self.session.rollback()
            raise
