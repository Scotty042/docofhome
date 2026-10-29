import http.client
import json
import runpy
import sqlite3
import subprocess
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlmodel import Session, select

from app.connectors import docker_ssh
from app.core.settings import settings
from app.main import app
from app.models.asset_engine import Asset, AssetType
from app.models.release import ServiceWorkload
from app.schemas.release import DockerHostWrite
from app.services.docker_sync import DockerSyncService


def _asset(session: Session, name: str, code: str) -> Asset:
    asset_type = AssetType(name=f"Type {name}", code_prefix=code)
    session.add(asset_type)
    session.commit()
    asset = Asset(name=name, jarvis_code=f"{code}-0001", asset_type_id=asset_type.id)
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def _payload(asset: Asset, name: str, connection_type: str = "ssh") -> DockerHostWrite:
    return DockerHostWrite(
        name=name,
        enabled=True,
        connection_type=connection_type,
        host_asset_id=asset.id,
        socket_path="/var/run/docker.sock" if connection_type == "socket" else None,
        ssh_host="192.0.2.10" if connection_type == "ssh" else None,
        ssh_user="docofhome-monitor" if connection_type == "ssh" else None,
        ssh_host_key=("[192.0.2.10]:22 ssh-ed25519 " + "AQID")
        if connection_type == "ssh"
        else None,
        refresh_interval_seconds=300,
    )


def test_multiple_hosts_keep_equal_container_names_separate(session, monkeypatch):
    paths = {route.path for route in app.routes}
    assert "/api/v1/workloads/docker/hosts" in paths
    assert "/api/v1/workloads/docker/hosts/{host_id}/host-key/scan" in paths
    assert "/api/v1/workloads/docker/hosts/{host_id}/sync" in paths
    first_asset = _asset(session, "NUC", "NUC")
    second_asset = _asset(session, "NAS", "NAS")
    monkeypatch.setattr("app.services.docker_sync.ensure_key_pair", lambda _id: "ssh-ed25519 test")
    service = DockerSyncService(session)
    first = service.create_host(_payload(first_asset, "Docker NUC"))
    second = service.create_host(_payload(second_asset, "Docker NAS", "socket"))
    changed = _payload(first_asset, "Docker NUC")
    changed.ssh_host = "192.0.2.11"
    assert service.update_host(first.id, changed).ssh_host_key is None

    class Connector:
        def version(self):
            return "28.4.0"

        def containers(self, *, all_containers=True):
            assert all_containers
            return [
                {
                    "Id": "same-id",
                    "Names": ["/paperless"],
                    "Image": "paperless:latest",
                    "State": "running",
                    "Status": "Up",
                    "Labels": {},
                    "Ports": [],
                    "NetworkSettings": {"Networks": {}},
                    "Mounts": [],
                }
            ]

    monkeypatch.setattr(service, "_connector_for", lambda _host: Connector())
    assert service.sync_host(first.id).imported == 1
    assert service.sync_host(second.id).imported == 1
    records = list(session.exec(select(ServiceWorkload)).all())
    assert len(records) == 2
    assert {record.host_asset_id for record in records} == {first_asset.id, second_asset.id}


def test_ssh_connector_pins_host_key_and_uses_restricted_command(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    host_id = uuid4()
    private_key, public_key, _ = docker_ssh.key_paths(host_id)
    private_key.write_text("private", encoding="utf-8")
    public_key.write_text("ssh-ed25519 public", encoding="utf-8")
    calls = []

    def run(arguments, **kwargs):
        calls.append((arguments, kwargs))
        return subprocess.CompletedProcess(
            arguments, 0, json.dumps({"docker_version": "28.4", "containers": []}), ""
        )

    monkeypatch.setattr(docker_ssh.subprocess, "run", run)
    connector = docker_ssh.SshDockerEngineConnector(
        host_id, "nuc.example", 2222, "monitor", "[nuc.example]:2222 ssh-ed25519 AQID"
    )
    assert connector.version() == "28.4"
    assert connector.containers() == []
    command_line = calls[0][0]
    assert command_line[-2:] == ["monitor@nuc.example", "docofhome-docker-snapshot"]
    assert "StrictHostKeyChecking=yes" in command_line
    assert "BatchMode=yes" in command_line
    assert len(calls) == 1


def test_ed25519_key_pair_is_private_and_unique(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    first_id, second_id = uuid4(), uuid4()
    first = docker_ssh.ensure_key_pair(first_id)
    second = docker_ssh.ensure_key_pair(second_id)
    first_private, _, _ = docker_ssh.key_paths(first_id)
    assert first.startswith("ssh-ed25519 ")
    assert second.startswith("ssh-ed25519 ")
    assert first != second
    assert first_private.stat().st_mode & 0o777 == 0o600
    assert first_private.parent.stat().st_mode & 0o777 == 0o700


def test_migration_copies_legacy_socket_configuration(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    backend = Path(__file__).parents[1]
    config = Config(str(backend / "alembic.ini"))
    config.set_main_option("script_location", str(backend / "migrations"))
    command.upgrade(config, "0057")
    with sqlite3.connect(settings.database_path) as connection:
        asset_type_id = "11111111111111111111111111111111"
        asset_id = "22222222222222222222222222222222"
        connection.execute(
            "INSERT INTO asset_types "
            "(id,name,code_prefix,created_at,updated_at,image_source,is_meter,switch_port_layout) "
            "VALUES (?, 'Server', 'SRV', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, "
            "'url', 0, 'odd_even')",
            (asset_type_id,),
        )
        connection.execute(
            "INSERT INTO assets "
            "(id,name,jarvis_code,asset_type_id,created_at,updated_at,image_source,status) "
            "VALUES (?, 'NUC', 'SRV-0001', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, "
            "'url', 'active')",
            (asset_id, asset_type_id),
        )
        connection.execute(
            "INSERT INTO docker_sync_settings "
            "(id,enabled,socket_path,host_asset_id,refresh_interval_seconds,created_at,updated_at) "
            "VALUES (1,1,'/custom/docker.sock',?,60,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)",
            (asset_id,),
        )
    command.upgrade(config, "head")
    with sqlite3.connect(settings.database_path) as connection:
        row = connection.execute(
            "SELECT connection_type,socket_path,host_asset_id,refresh_interval_seconds "
            "FROM docker_hosts"
        ).fetchone()
        assert row == ("socket", "/custom/docker.sock", asset_id, 60)
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == ("0061",)


def test_forced_command_only_returns_docker_snapshot(monkeypatch, capsys):
    payloads = iter([
        {"Version": "28.4.0"},
        [{"Id": "container-1", "Names": ["/example"]}],
    ])
    requested = []

    class Response:
        status = 200

        def __init__(self):
            self.payload = next(payloads)

        def read(self):
            return json.dumps(self.payload).encode()

    monkeypatch.setattr(
        http.client.HTTPConnection,
        "request",
        lambda _self, method, path, headers: requested.append((method, path, headers)),
    )
    monkeypatch.setattr(http.client.HTTPConnection, "getresponse", lambda _self: Response())
    monkeypatch.setattr(http.client.HTTPConnection, "close", lambda _self: None)
    helper = Path(__file__).parents[2] / "scripts/docofhome-docker-snapshot"
    runpy.run_path(str(helper), run_name="__main__")
    output = json.loads(capsys.readouterr().out)
    assert requested == [
        ("GET", "/version", {"Host": "docker"}),
        ("GET", "/containers/json?all=1", {"Host": "docker"}),
    ]
    assert output == {
        "docker_version": "28.4.0",
        "containers": [{"Id": "container-1", "Names": ["/example"]}],
    }
