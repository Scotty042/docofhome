from collections.abc import Iterable
from uuid import UUID

from sqlmodel import Session, col, select

from app.models.network import (
    NetworkAddress,
    NetworkConnection,
    NetworkDevice,
    NetworkInterface,
    NetworkSegment,
)


class NetworkRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _active(statement, model):
        return statement.where(col(model.deleted_at).is_(None))

    def get_device(self, record_id: UUID, *, include_deleted: bool = False) -> NetworkDevice | None:
        record = self.session.get(NetworkDevice, record_id)
        if record is None or (record.deleted_at is not None and not include_deleted):
            return None
        return record

    def active_device_for_asset(self, asset_id: UUID) -> NetworkDevice | None:
        return self.session.exec(
            select(NetworkDevice).where(
                NetworkDevice.asset_id == asset_id,
                col(NetworkDevice.deleted_at).is_(None),
            )
        ).first()

    def list_devices(self, *, include_deleted: bool = False) -> list[NetworkDevice]:
        statement = select(NetworkDevice)
        if not include_deleted:
            statement = self._active(statement, NetworkDevice)
        return list(
            self.session.exec(statement.order_by(NetworkDevice.hostname, NetworkDevice.id)).all()
        )

    def get_segment(
        self, record_id: UUID, *, include_deleted: bool = False
    ) -> NetworkSegment | None:
        record = self.session.get(NetworkSegment, record_id)
        if record is None or (record.deleted_at is not None and not include_deleted):
            return None
        return record

    def list_segments(self, *, include_deleted: bool = False) -> list[NetworkSegment]:
        statement = select(NetworkSegment)
        if not include_deleted:
            statement = self._active(statement, NetworkSegment)
        return list(
            self.session.exec(statement.order_by(NetworkSegment.vlan_id, NetworkSegment.name)).all()
        )

    def active_segment_by_name(
        self, name: str, *, exclude_id: UUID | None = None
    ) -> NetworkSegment | None:
        statement = select(NetworkSegment).where(col(NetworkSegment.deleted_at).is_(None))
        for record in self.session.exec(statement).all():
            if record.name.casefold() == name.casefold() and record.id != exclude_id:
                return record
        return None

    def active_segment_by_vlan(
        self, vlan_id: int, *, exclude_id: UUID | None = None
    ) -> NetworkSegment | None:
        statement = select(NetworkSegment).where(
            NetworkSegment.vlan_id == vlan_id,
            col(NetworkSegment.deleted_at).is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(NetworkSegment.id != exclude_id)
        return self.session.exec(statement).first()

    def get_interface(
        self, record_id: UUID, *, include_deleted: bool = False
    ) -> NetworkInterface | None:
        record = self.session.get(NetworkInterface, record_id)
        if record is None or (record.deleted_at is not None and not include_deleted):
            return None
        return record

    def list_interfaces(
        self,
        *,
        device_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> list[NetworkInterface]:
        statement = select(NetworkInterface)
        if device_id is not None:
            statement = statement.where(NetworkInterface.network_device_id == device_id)
        if not include_deleted:
            statement = self._active(statement, NetworkInterface)
        return list(
            self.session.exec(statement.order_by(NetworkInterface.name, NetworkInterface.id)).all()
        )

    def active_interface_by_name(
        self,
        device_id: UUID,
        name: str,
        *,
        exclude_id: UUID | None = None,
    ) -> NetworkInterface | None:
        statement = select(NetworkInterface).where(
            NetworkInterface.network_device_id == device_id,
            col(NetworkInterface.deleted_at).is_(None),
        )
        for record in self.session.exec(statement).all():
            if record.name.casefold() == name.casefold() and record.id != exclude_id:
                return record
        return None

    def active_interface_by_mac(
        self,
        mac_address: str,
        *,
        exclude_id: UUID | None = None,
    ) -> NetworkInterface | None:
        statement = select(NetworkInterface).where(
            NetworkInterface.mac_address == mac_address,
            col(NetworkInterface.deleted_at).is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(NetworkInterface.id != exclude_id)
        return self.session.exec(statement).first()

    def get_address(
        self, record_id: UUID, *, include_deleted: bool = False
    ) -> NetworkAddress | None:
        record = self.session.get(NetworkAddress, record_id)
        if record is None or (record.deleted_at is not None and not include_deleted):
            return None
        return record

    def list_addresses(
        self,
        *,
        interface_id: UUID | None = None,
        device_id: UUID | None = None,
        segment_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> list[NetworkAddress]:
        statement = select(NetworkAddress)
        if interface_id is not None:
            statement = statement.where(NetworkAddress.interface_id == interface_id)
        if segment_id is not None:
            statement = statement.where(NetworkAddress.segment_id == segment_id)
        if device_id is not None:
            interface_ids = [
                item.id for item in self.list_interfaces(device_id=device_id, include_deleted=True)
            ]
            if not interface_ids:
                return []
            statement = statement.where(col(NetworkAddress.interface_id).in_(interface_ids))
        if not include_deleted:
            statement = self._active(statement, NetworkAddress)
        return list(
            self.session.exec(statement.order_by(NetworkAddress.address, NetworkAddress.id)).all()
        )

    def active_address_conflict(
        self,
        *,
        interface_id: UUID,
        segment_id: UUID | None,
        address: str,
        exclude_id: UUID | None = None,
    ) -> NetworkAddress | None:
        statement = select(NetworkAddress).where(
            NetworkAddress.address == address,
            col(NetworkAddress.deleted_at).is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(NetworkAddress.id != exclude_id)
        records = self.session.exec(statement).all()
        for record in records:
            if record.interface_id == interface_id:
                return record
            if segment_id is not None and record.segment_id == segment_id:
                return record
        return None

    def get_connection(
        self, record_id: UUID, *, include_deleted: bool = False
    ) -> NetworkConnection | None:
        record = self.session.get(NetworkConnection, record_id)
        if record is None or (record.deleted_at is not None and not include_deleted):
            return None
        return record

    def list_connections(
        self,
        *,
        device_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> list[NetworkConnection]:
        statement = select(NetworkConnection)
        if not include_deleted:
            statement = self._active(statement, NetworkConnection)
        records = list(
            self.session.exec(
                statement.order_by(NetworkConnection.created_at, NetworkConnection.id)
            ).all()
        )
        if device_id is None:
            return records
        interface_ids = {
            item.id for item in self.list_interfaces(device_id=device_id, include_deleted=True)
        }
        return [
            item
            for item in records
            if item.source_interface_id in interface_ids
            or item.target_interface_id in interface_ids
        ]

    def active_connection_for_endpoints(
        self,
        source_id: UUID,
        target_id: UUID,
        *,
        exclude_id: UUID | None = None,
    ) -> NetworkConnection | None:
        statement = select(NetworkConnection).where(
            NetworkConnection.source_interface_id == source_id,
            NetworkConnection.target_interface_id == target_id,
            col(NetworkConnection.deleted_at).is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(NetworkConnection.id != exclude_id)
        return self.session.exec(statement).first()

    def add_all(self, records: Iterable[object]) -> None:
        for record in records:
            self.session.add(record)
