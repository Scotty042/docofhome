from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app import models  # noqa: F401
from app.models.asset_engine import Asset, AssetType
from app.schemas.network import (
    NetworkAddressWrite,
    NetworkAssignmentType,
    NetworkConnectionStatus,
    NetworkConnectionType,
    NetworkConnectionWrite,
    NetworkDeviceWrite,
    NetworkInterfaceType,
    NetworkInterfaceWrite,
    NetworkPoeMode,
    NetworkRole,
    NetworkSegmentWrite,
)
from app.services.asset_engine import AssetService, ResourceConflictError
from app.services.network import NetworkConflictError, NetworkService, NetworkValidationError


@pytest.fixture
def network_session(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'network.sqlite3'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def asset(network_session: Session, name: str, code: str) -> Asset:
    asset_type = network_session.exec(select(AssetType)).first()
    if asset_type is None:
        asset_type = AssetType(name="Network device", code_prefix="NET")
        network_session.add(asset_type)
        network_session.flush()
    record = Asset(name=name, jarvis_code=code, asset_type_id=asset_type.id)
    network_session.add(record)
    network_session.commit()
    return record


def test_network_device_addresses_connections_and_topology(network_session: Session) -> None:
    service = NetworkService(network_session)
    switch_asset = asset(network_session, "Core Switch", "NET-0001")
    nas_asset = asset(network_session, "NAS", "NET-0002")
    switch = service.create_device(
        NetworkDeviceWrite(asset_id=switch_asset.id, role=NetworkRole.SWITCH, hostname="sw-core")
    )
    nas = service.create_device(
        NetworkDeviceWrite(asset_id=nas_asset.id, role=NetworkRole.NAS, hostname="nas")
    )
    switch_port = service.create_interface(
        NetworkInterfaceWrite(
            network_device_id=switch.id, name="Port 1", mac_address="aa-bb-cc-dd-ee-01"
        )
    )
    nas_port = service.create_interface(
        NetworkInterfaceWrite(
            network_device_id=nas.id, name="eth0", mac_address="AA:BB:CC:DD:EE:02"
        )
    )
    lan = service.create_segment(
        NetworkSegmentWrite(
            name="LAN",
            cidr="192.168.10.0/24",
            vlan_id=None,
            gateway="192.168.10.1",
            dns_servers=["192.168.10.1"],
        )
    )
    address = service.create_address(
        NetworkAddressWrite(
            interface_id=nas_port.id,
            segment_id=lan.id,
            address="192.168.10.20",
            assignment_type=NetworkAssignmentType.STATIC,
            is_primary=True,
        )
    )
    connection = service.create_connection(
        NetworkConnectionWrite(
            source_interface_id=nas_port.id,
            target_interface_id=switch_port.id,
            cable_type="Cat 6A",
            cable_label="P01",
        )
    )

    assert address.segment_name == "LAN"
    assert lan.vlan_id is None
    assert connection.source_interface_id.int < connection.target_interface_id.int
    assert service.summary().device_count == 2
    topology = service.topology()
    assert len(topology.nodes) == 2
    assert len(topology.edges) == 1
    assert service.get_device(nas.id).address_count == 1

    with pytest.raises(NetworkConflictError):
        service.create_connection(
            NetworkConnectionWrite(
                source_interface_id=switch_port.id,
                target_interface_id=nas_port.id,
            )
        )
    with pytest.raises(NetworkConflictError):
        service.create_address(
            NetworkAddressWrite(
                interface_id=switch_port.id,
                segment_id=lan.id,
                address="192.168.10.20",
            )
        )


def test_address_must_belong_to_segment_and_device_archive_cascades(
    network_session: Session,
) -> None:
    service = NetworkService(network_session)
    record = asset(network_session, "Access Point", "NET-0003")
    device = service.create_device(
        NetworkDeviceWrite(asset_id=record.id, role=NetworkRole.ACCESS_POINT)
    )
    interface = service.create_interface(
        NetworkInterfaceWrite(network_device_id=device.id, name="LAN")
    )
    segment = service.create_segment(
        NetworkSegmentWrite(name="Management", cidr="10.0.0.0/24", vlan_id=99)
    )
    with pytest.raises(NetworkValidationError):
        service.create_address(
            NetworkAddressWrite(
                interface_id=interface.id,
                segment_id=segment.id,
                address="192.168.1.1",
            )
        )
    service.create_address(
        NetworkAddressWrite(
            interface_id=interface.id,
            segment_id=segment.id,
            address="10.0.0.10",
        )
    )
    service.delete_device(device.id)
    assert service.list_devices() == []
    assert service.repository.list_interfaces(device_id=device.id) == []
    assert service.repository.list_addresses(device_id=device.id) == []


def test_asset_cannot_be_archived_while_network_role_is_active(network_session: Session) -> None:
    service = NetworkService(network_session)
    record = asset(network_session, "Firewall", "NET-0004")
    device = service.create_device(
        NetworkDeviceWrite(asset_id=record.id, role=NetworkRole.FIREWALL)
    )

    with pytest.raises(ResourceConflictError):
        AssetService(network_session).delete(record.id)

    service.delete_device(device.id)
    AssetService(network_session).delete(record.id)
    network_session.refresh(record)
    assert record.deleted_at is not None


def test_logical_bridge_owns_device_ip_and_free_switch_ports_are_neutral(
    network_session: Session,
) -> None:
    service = NetworkService(network_session)
    router_asset = asset(network_session, "Router", "NET-0100")
    switch_asset = asset(network_session, "Switch", "NET-0101")
    router = service.create_device(
        NetworkDeviceWrite(asset_id=router_asset.id, role=NetworkRole.ROUTER)
    )
    switch = service.create_device(
        NetworkDeviceWrite(asset_id=switch_asset.id, role=NetworkRole.SWITCH)
    )
    bridge = service.create_interface(
        NetworkInterfaceWrite(
            network_device_id=router.id,
            name="LAN-Bridge",
            interface_type="virtual",
        )
    )
    router_ports = [
        service.create_interface(
            NetworkInterfaceWrite(
                network_device_id=router.id,
                name=f"LAN {index}",
                logical_interface_id=bridge.id,
            )
        )
        for index in range(1, 5)
    ]
    switch_ports = [
        service.create_interface(
            NetworkInterfaceWrite(network_device_id=switch.id, name=f"Port {index}")
        )
        for index in range(1, 5)
    ]
    service.create_address(
        NetworkAddressWrite(
            interface_id=bridge.id,
            address="192.168.178.1",
            assignment_type=NetworkAssignmentType.STATIC,
            is_primary=True,
        )
    )
    service.create_connection(
        NetworkConnectionWrite(
            source_interface_id=router_ports[0].id,
            target_interface_id=switch_ports[0].id,
        )
    )

    bridge_read = next(
        item
        for item in service.list_interfaces(device_id=router.id)
        if item.id == bridge.id
    )
    assert bridge_read.member_count == 4
    assert service.get_device(router.id).primary_address == "192.168.178.1"
    summary = service.summary()
    assert summary.device_without_connection_count == 0
    assert summary.free_interface_count == 6

    with pytest.raises(NetworkConflictError):
        service.update_interface(
            bridge.id,
            NetworkInterfaceWrite(
                network_device_id=router.id,
                name="LAN-Bridge",
                interface_type="ethernet",
            ),
        )


def test_legacy_enum_values_fall_back_without_crashing(network_session: Session) -> None:
    service = NetworkService(network_session)

    assert service._network_role("legacy-role") == NetworkRole.OTHER
    assert service._interface_type(None) == NetworkInterfaceType.OTHER
    assert service._poe_mode("legacy-poe") == NetworkPoeMode.UNKNOWN
    assert service._assignment_type("legacy-assignment") == NetworkAssignmentType.UNKNOWN
    assert service._connection_type("legacy-connection") == NetworkConnectionType.PHYSICAL
    assert service._connection_status("legacy-status") == NetworkConnectionStatus.INACTIVE
