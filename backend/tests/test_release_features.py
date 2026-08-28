import json

from sqlmodel import Session

from app.models.asset_engine import Asset, AssetType
from app.models.integration_setting import IntegrationSetting
from app.models.network import NetworkDevice
from app.models.release import DashboardSetting
from app.schemas.release import (
    DashboardCardSetting,
    DashboardSettingWrite,
    GuidedSetupDraftWrite,
    PortGenerationWrite,
    PortGroupWrite,
    PortNameScheme,
    ServiceWorkloadWrite,
)
from app.services.release import (
    DashboardService,
    GuidedSetupService,
    NetworkExtensionService,
    PortabilityService,
    WorkloadService,
)


def host_asset(session: Session, *, name: str = "Server") -> Asset:
    asset_type = AssetType(name=f"Typ {name}", code_prefix=name[:3].upper())
    session.add(asset_type)
    session.flush()
    asset = Asset(name=name, jarvis_code=f"{name[:3].upper()}-0001", asset_type_id=asset_type.id)
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def test_dashboard_layout_is_persistent_and_resettable(session: Session) -> None:
    service = DashboardService(session)
    initial = service.get()
    assert initial.cards
    reversed_cards = [
        DashboardCardSetting(id=item.id, visible=item.id != "quality")
        for item in reversed(initial.cards)
    ]
    saved = service.update(DashboardSettingWrite(cards=reversed_cards))
    assert saved.cards[0].id == initial.cards[-1].id
    assert next(item for item in saved.cards if item.id == "quality").visible is False
    assert DashboardService(session).get().cards == saved.cards
    assert service.reset().cards == initial.cards


def test_dashboard_removes_legacy_version_card_without_losing_order(session: Session) -> None:
    record = DashboardSetting(
        layout_json=json.dumps(
            [
                {"id": "system", "visible": True},
                {"id": "network", "visible": False},
                {"id": "documentation", "visible": True},
                {"id": "maintenance", "visible": True},
                {"id": "quality", "visible": True},
                {"id": "consumption_comparison", "visible": True},
            ]
        )
    )
    session.add(record)
    session.commit()

    result = DashboardService(session).get()

    assert [item.id for item in result.cards] == [
        "network",
        "documentation",
        "maintenance",
        "quality",
        "consumption_comparison",
    ]
    assert result.cards[0].visible is False
    stored = session.get(DashboardSetting, 1)
    assert stored is not None
    assert "system" not in stored.layout_json


def test_switch_port_preview_and_generation_are_idempotent(session: Session) -> None:
    asset = host_asset(session, name="Switch")
    switch = NetworkDevice(asset_id=asset.id, role="switch")
    session.add(switch)
    session.commit()
    payload = PortGenerationWrite(
        groups=[
            PortGroupWrite(
                group="copper",
                count=3,
                scheme=PortNameScheme.GIGABIT,
                speed_mbps=1000,
                poe_capable=True,
            )
        ]
    )
    service = NetworkExtensionService(session)
    assert service.preview_ports(switch.id, payload).create_names == [
        "Gi1/0/1",
        "Gi1/0/2",
        "Gi1/0/3",
    ]
    assert service.generate_ports(switch.id, payload).created == 3
    assert service.generate_ports(switch.id, payload).created == 0


def test_workload_is_logical_and_stays_linked_to_host(session: Session) -> None:
    asset = host_asset(session)
    service = WorkloadService(session)
    workload = service.create(
        ServiceWorkloadWrite(
            host_asset_id=asset.id,
            name="reverse-proxy",
            image="caddy",
            image_tag="2",
            ports=[{"container_port": 443, "host_port": 443, "protocol": "tcp"}],
            status="running",
        )
    )
    assert workload.host_asset_id == asset.id
    assert workload.host_name == asset.name
    assert service.list(host_asset_id=asset.id)[0].id == workload.id
    service.archive(workload.id)
    assert service.list() == []


def test_export_redacts_integration_secrets(session: Session) -> None:
    session.add(
        IntegrationSetting(
            kind="home_assistant",
            enabled=True,
            base_url="http://private.invalid",
            account="operator",
            secret="super-secret",
        )
    )
    session.commit()
    serialized = json.dumps(PortabilityService(session).export_payload())
    assert "super-secret" not in serialized
    assert "private.invalid" not in serialized
    assert "operator" not in serialized
    assert '"kind": "home_assistant"' in serialized


def test_csv_export_carries_explicit_module_mapping(session: Session) -> None:
    host_asset(session, name="CSV-Host")
    service = PortabilityService(session)
    content = service.csv_export("assets")
    assert content.startswith("__module,")
    preview = service.preview(content.encode())
    assert preview.format == "DocOfHome CSV"
    assert preview.record_counts == {"assets": 1}
    assert preview.conflicts


def test_guided_setup_reuses_existing_asset_transactionally(session: Session) -> None:
    asset = host_asset(session, name="Wärmepumpe")
    service = GuidedSetupService(session)
    draft = service.create(
        GuidedSetupDraftWrite(
            name="Wärmepumpe ergänzen",
            current_step=10,
            data={"existing_asset_id": str(asset.id), "note": "Leitungsdaten noch prüfen"},
        )
    )
    preview = service.preview(draft.id)
    assert preview.can_apply is True
    result = service.apply(draft.id)
    assert result.asset_id == asset.id
    assert service.list()[0].status == "applied"


def test_audit_events_expose_readable_object_context(session: Session) -> None:
    asset = host_asset(session, name="Lesbarer Verlauf")
    events = PortabilityService(session).audit_events(object_type="assets")
    matching = next(event for event in events if event.object_id == str(asset.id))
    assert matching.object_label == "Lesbarer Verlauf"
    assert matching.object_route == f"/assets/{asset.id}"
    assert matching.display_change is not None
    assert matching.display_change["asset_type_id"]["to"] == "Typ Lesbarer Verlauf"


def test_docker_sync_imports_and_updates_without_duplicates(session: Session, monkeypatch) -> None:
    from app.schemas.release import DockerSyncSettingWrite
    from app.services.docker_sync import DockerSyncService

    asset = host_asset(session, name="UGREEN NAS")
    snapshots = [
        [{
            "Id": "abc123",
            "Names": ["/paperless"],
            "Image": "ghcr.io/paperless-ngx/paperless-ngx:latest",
            "State": "running",
            "Status": "Up 2 hours (healthy)",
            "Labels": {"com.docker.compose.project": "paperless"},
            "HostConfig": {"NetworkMode": "paperless_default"},
            "Ports": [{"PrivatePort": 8000, "PublicPort": 8180, "Type": "tcp"}],
            "NetworkSettings": {"Networks": {"paperless_default": {"IPAddress": "172.20.0.3"}}},
            "Mounts": [{"Source": "/volume2/docker/paperless/data", "Destination": "/usr/src/paperless/data"}],
        }],
        [{
            "Id": "abc123",
            "Names": ["/paperless"],
            "Image": "ghcr.io/paperless-ngx/paperless-ngx:latest",
            "State": "exited",
            "Status": "Exited (0) 2 seconds ago",
            "Labels": {"com.docker.compose.project": "paperless"},
            "HostConfig": {"NetworkMode": "paperless_default"},
            "Ports": [{"PrivatePort": 8000, "PublicPort": 8180, "Type": "tcp"}],
            "NetworkSettings": {"Networks": {"paperless_default": {"IPAddress": ""}}},
            "Mounts": [],
        }],
    ]

    class FakeConnector:
        def __init__(self, _socket_path: str) -> None:
            pass

        def version(self) -> str:
            return "28.3.3"

        def containers(self, *, all_containers: bool = True):
            assert all_containers is True
            return snapshots.pop(0)

    monkeypatch.setattr("app.services.docker_sync.DockerEngineConnector", FakeConnector)
    service = DockerSyncService(session)
    service.update_settings(DockerSyncSettingWrite(
        enabled=True,
        socket_path="/var/run/docker.sock",
        host_asset_id=asset.id,
        refresh_interval_seconds=300,
    ))

    first = service.sync()
    assert first.imported == 1
    assert first.total == 1
    records = WorkloadService(session).list(host_asset_id=asset.id)
    assert len(records) == 1
    assert records[0].docker_container_id == "abc123"
    assert records[0].status == "running"
    assert records[0].ports[0].host_port == 8180
    assert records[0].docker_networks == ["paperless_default"]

    editable = ServiceWorkloadWrite(**{
        key: getattr(records[0], key)
        for key in ServiceWorkloadWrite.model_fields
    })
    editable.notes = "manuell gepflegt"
    WorkloadService(session).update(records[0].id, editable)

    second = service.sync()
    assert second.imported == 0
    assert second.updated == 1
    records = WorkloadService(session).list(host_asset_id=asset.id)
    assert len(records) == 1
    assert records[0].status == "stopped"
    assert records[0].notes == "manuell gepflegt"
