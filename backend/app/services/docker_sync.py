from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, col, select

from app.connectors.docker_engine import DockerEngineConnector, DockerEngineError
from app.models.asset_engine import Asset
from app.models.release import DockerSyncSetting, ServiceWorkload
from app.schemas.release import (
    DockerConnectionTestRead,
    DockerSyncResultRead,
    DockerSyncSettingRead,
    DockerSyncSettingWrite,
)


class DockerSyncError(RuntimeError):
    pass


_DOCKER_SYNC_LOCK = Lock()


class DockerSyncService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_settings(self) -> DockerSyncSettingRead:
        record = self.session.get(DockerSyncSetting, 1)
        if record is None:
            record = DockerSyncSetting()
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
        return self._settings_read(record)

    def update_settings(self, payload: DockerSyncSettingWrite) -> DockerSyncSettingRead:
        record = self.session.get(DockerSyncSetting, 1) or DockerSyncSetting()
        if payload.host_asset_id is not None:
            host = self.session.get(Asset, payload.host_asset_id)
            if host is None or host.deleted_at is not None:
                raise DockerSyncError("Das ausgewählte Host-Asset wurde nicht gefunden")
        record.enabled = payload.enabled
        record.socket_path = payload.socket_path
        record.host_asset_id = payload.host_asset_id
        record.refresh_interval_seconds = payload.refresh_interval_seconds
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._settings_read(record)

    def test_connection(self) -> DockerConnectionTestRead:
        setting = self.session.get(DockerSyncSetting, 1) or DockerSyncSetting()
        try:
            version = DockerEngineConnector(setting.socket_path).version()
        except DockerEngineError as exc:
            return DockerConnectionTestRead(success=False, message=str(exc), docker_version=None)
        return DockerConnectionTestRead(
            success=True,
            message="Docker Engine ist erreichbar.",
            docker_version=version,
        )

    def is_due(self) -> bool:
        setting = self.session.get(DockerSyncSetting, 1)
        if (
            setting is None
            or not setting.enabled
            or setting.host_asset_id is None
            or setting.refresh_interval_seconds <= 0
        ):
            return False
        if setting.last_attempt_at is None:
            return True
        last_attempt = self._aware(setting.last_attempt_at)
        return datetime.now(UTC) >= last_attempt + timedelta(seconds=setting.refresh_interval_seconds)

    def sync(self) -> DockerSyncResultRead:
        # The browser-triggered refresh and the background scheduler can fire at the
        # same time. Serialize the import within one DocOfHome process so a container
        # cannot be created twice by concurrent syncs.
        with _DOCKER_SYNC_LOCK:
            return self._sync_locked()

    def _sync_locked(self) -> DockerSyncResultRead:
        setting = self.session.get(DockerSyncSetting, 1)
        if setting is None:
            setting = DockerSyncSetting()
            self.session.add(setting)
            self.session.commit()
            self.session.refresh(setting)
        if setting.host_asset_id is None:
            raise DockerSyncError("Bitte zuerst das UGREEN-NAS als Host-Asset auswählen")
        host = self.session.get(Asset, setting.host_asset_id)
        if host is None or host.deleted_at is not None:
            raise DockerSyncError("Das konfigurierte Host-Asset wurde nicht gefunden")

        now = datetime.now(UTC)
        try:
            setting.last_attempt_at = now
            setting.updated_at = now
            self.session.add(setting)
            self.session.commit()

            connector = DockerEngineConnector(setting.socket_path)
            docker_version = connector.version()
            containers = connector.containers(all_containers=True)
            result = self._apply_containers(setting.host_asset_id, containers, now, docker_version)
            setting = self.session.get(DockerSyncSetting, 1) or setting
            setting.last_success_at = now
            setting.last_error = None
            setting.updated_at = now
            self.session.add(setting)
            self.session.commit()
            return result
        except (DockerEngineError, OSError, ValueError, SQLAlchemyError) as exc:
            # A database exception leaves the SQLAlchemy session in a failed
            # transaction. Roll back before persisting the visible sync error.
            self.session.rollback()
            setting = self.session.get(DockerSyncSetting, 1) or setting
            setting.last_error = str(exc)
            setting.updated_at = datetime.now(UTC)
            self.session.add(setting)
            try:
                self.session.commit()
            except SQLAlchemyError:
                self.session.rollback()
            raise DockerSyncError(str(exc)) from exc

    def _apply_containers(
        self,
        host_asset_id: UUID,
        containers: list[dict[str, Any]],
        synchronized_at: datetime,
        docker_version: str | None,
    ) -> DockerSyncResultRead:
        existing = list(self.session.exec(
            select(ServiceWorkload).where(
                ServiceWorkload.host_asset_id == host_asset_id,
                col(ServiceWorkload.deleted_at).is_(None),
            )
        ).all())
        by_container_id = {
            item.docker_container_id: item
            for item in existing
            if item.docker_container_id
        }
        by_name = {item.name.casefold(): item for item in existing}
        seen_ids: set[str] = set()
        imported = 0
        updated = 0

        for container in containers:
            container_id = str(container.get("Id") or "").strip()
            if not container_id:
                continue
            names = container.get("Names") or []
            raw_name = str(names[0] if names else container_id[:12]).lstrip("/")
            name = raw_name or container_id[:12]
            record = by_container_id.get(container_id) or by_name.get(name.casefold())
            created = record is None
            if record is None:
                record = ServiceWorkload(host_asset_id=host_asset_id, name=name)
                imported += 1
            else:
                updated += 1

            image, image_tag = self._split_image(str(container.get("Image") or ""))
            state = str(container.get("State") or "unknown").lower()
            status = "running" if state == "running" else "stopped" if state in {
                "created", "exited", "dead", "paused"
            } else "unknown"
            labels = container.get("Labels") if isinstance(container.get("Labels"), dict) else {}
            network_settings = container.get("NetworkSettings") if isinstance(container.get("NetworkSettings"), dict) else {}
            networks = network_settings.get("Networks") if isinstance(network_settings.get("Networks"), dict) else {}
            network_names = sorted(str(value) for value in networks.keys())
            network_mode = self._network_mode(container, network_names)
            macvlan_address = None
            if network_mode == "macvlan":
                for data in networks.values():
                    if isinstance(data, dict) and data.get("IPAddress"):
                        macvlan_address = str(data["IPAddress"])
                        break

            record.host_asset_id = host_asset_id
            record.name = name
            record.image = image or None
            record.image_tag = image_tag
            record.compose_project = str(labels.get("com.docker.compose.project") or "").strip() or None
            record.network_mode = network_mode
            record.macvlan_address = macvlan_address
            record.ports_json = json.dumps(self._ports(container.get("Ports")), separators=(",", ":"))
            record.status = status
            record.docker_container_id = container_id
            record.docker_status_text = str(container.get("Status") or state or "unknown")[:500]
            record.docker_networks_json = json.dumps(network_names, separators=(",", ":"))
            record.docker_mounts_json = json.dumps(self._mounts(container.get("Mounts")), separators=(",", ":"))
            record.docker_last_seen_at = synchronized_at
            if created:
                record.created_at = synchronized_at
            record.updated_at = synchronized_at
            self.session.add(record)
            seen_ids.add(container_id)

        missing = 0
        for record in existing:
            if record.docker_container_id and record.docker_container_id not in seen_ids:
                record.status = "unknown"
                record.docker_status_text = "Beim letzten Docker-Abgleich nicht mehr gefunden"
                record.updated_at = synchronized_at
                self.session.add(record)
                missing += 1

        self.session.commit()
        return DockerSyncResultRead(
            imported=imported,
            updated=updated,
            missing=missing,
            total=len(seen_ids),
            docker_version=docker_version,
            synchronized_at=synchronized_at,
        )

    @staticmethod
    def _split_image(value: str) -> tuple[str, str | None]:
        if not value:
            return "", None
        # A registry port contains a colon as well; only split a colon after the final slash.
        slash = value.rfind("/")
        colon = value.rfind(":")
        if colon > slash:
            return value[:colon], value[colon + 1:] or None
        return value, None

    @staticmethod
    def _ports(raw: Any) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        if not isinstance(raw, list):
            return result
        for item in raw:
            if not isinstance(item, dict) or not item.get("PrivatePort"):
                continue
            protocol = str(item.get("Type") or "tcp").lower()
            if protocol not in {"tcp", "udp"}:
                protocol = "tcp"
            result.append({
                "container_port": int(item["PrivatePort"]),
                "host_port": int(item["PublicPort"]) if item.get("PublicPort") else None,
                "protocol": protocol,
            })
        return result

    @staticmethod
    def _mounts(raw: Any) -> list[str]:
        result: list[str] = []
        if not isinstance(raw, list):
            return result
        for item in raw:
            if not isinstance(item, dict):
                continue
            source = str(item.get("Source") or item.get("Name") or "").strip()
            destination = str(item.get("Destination") or "").strip()
            if source or destination:
                result.append(f"{source or 'volume'} → {destination or '–'}")
        return result

    @staticmethod
    def _network_mode(container: dict[str, Any], networks: list[str]) -> str:
        host_config = container.get("HostConfig") if isinstance(container.get("HostConfig"), dict) else {}
        mode = str(host_config.get("NetworkMode") or "").lower()
        if mode == "host":
            return "host"
        if mode in {"bridge", "default", ""} and (not networks or networks == ["bridge"]):
            return "bridge"
        # Docker's list endpoint does not expose the network driver's type reliably.
        # Keep custom networks generic; a documented manual macvlan assignment remains editable.
        return "docker_network"

    def _settings_read(self, record: DockerSyncSetting) -> DockerSyncSettingRead:
        host = self.session.get(Asset, record.host_asset_id) if record.host_asset_id else None
        return DockerSyncSettingRead(
            enabled=record.enabled,
            socket_path=record.socket_path,
            host_asset_id=record.host_asset_id,
            host_name=host.name if host else None,
            refresh_interval_seconds=record.refresh_interval_seconds,
            last_attempt_at=self._aware(record.last_attempt_at) if record.last_attempt_at else None,
            last_success_at=self._aware(record.last_success_at) if record.last_success_at else None,
            last_error=record.last_error,
        )

    @staticmethod
    def _aware(value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=UTC)
