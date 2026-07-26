from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Condition, Lock
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx
from sqlmodel import Session
from websockets.exceptions import WebSocketException
from websockets.sync.client import connect
from websockets.sync.connection import Connection

from app.repositories.home_assistant_selection import (
    HomeAssistantSelectionRepository,
    HomeAssistantSelectionState,
)
from app.repositories.settings import SettingsRepository
from app.schemas.home_assistant import (
    HomeAssistantAreaRead,
    HomeAssistantDeviceListRead,
    HomeAssistantDeviceRead,
    HomeAssistantEntityListRead,
    HomeAssistantEntityRead,
    HomeAssistantOverviewRead,
    HomeAssistantSelectionMode,
    HomeAssistantSelectionScope,
    HomeAssistantSummaryRead,
)

CACHE_TTL = timedelta(seconds=30)
REGISTRY_CACHE_TTL = timedelta(minutes=15)
WEBSOCKET_MAX_MESSAGE_SIZE = 16 * 1024 * 1024
WebSocketConnector = Callable[[str], Connection]


class HomeAssistantError(RuntimeError):
    """Base error for read-only Home Assistant access."""


class HomeAssistantConfigurationError(HomeAssistantError):
    """Raised when the stored integration is unavailable or incomplete."""


class HomeAssistantConnectionError(HomeAssistantError):
    """Raised when Home Assistant cannot return its read-only state data."""


@dataclass(slots=True)
class HomeAssistantSnapshot:
    overview: HomeAssistantOverviewRead
    devices: list[HomeAssistantDeviceRead]
    entities: list[HomeAssistantEntityRead]


@dataclass(slots=True)
class RegistrySnapshot:
    devices: list[dict[str, Any]]
    entities: list[dict[str, Any]]
    areas: list[dict[str, Any]]


class HomeAssistantService:
    _cache_lock = Lock()
    _cache_condition = Condition(_cache_lock)
    _cache_key: str | None = None
    _cache_expires_at: datetime | None = None
    _cache_snapshot: HomeAssistantSnapshot | None = None
    _registry_expires_at: datetime | None = None
    _registry_snapshot: RegistrySnapshot | None = None
    _registry_available: bool = True
    _registry_warning: str | None = None
    _sync_in_progress: bool = False

    def __init__(
        self,
        session: Session,
        *,
        transport: httpx.BaseTransport | None = None,
        websocket_connector: WebSocketConnector | None = None,
    ) -> None:
        self.repository = SettingsRepository(session)
        self.selection_repository = HomeAssistantSelectionRepository(session)
        self.transport = transport
        self.websocket_connector = websocket_connector or self._connect_websocket

    def overview(self, *, refresh: bool = False) -> HomeAssistantOverviewRead:
        snapshot = self._snapshot(refresh=refresh)
        selection = self.selection_repository.read()
        visible_entities = self._visible_entities(snapshot.entities, selection)
        visible_devices = self._visible_devices(snapshot.devices, visible_entities, selection)
        summary = snapshot.overview.summary.model_copy(
            update={
                "selection_mode": HomeAssistantSelectionMode(selection.mode),
                "selected_entity_count": len(selection.entity_ids),
                "visible_device_count": len(visible_devices),
                "visible_entity_count": len(visible_entities),
            }
        )
        return snapshot.overview.model_copy(update={"summary": summary})

    def devices(
        self,
        *,
        search: str | None = None,
        area_id: str | None = None,
        offset: int = 0,
        limit: int = 100,
        refresh: bool = False,
        selection_scope: HomeAssistantSelectionScope = HomeAssistantSelectionScope.VISIBLE,
    ) -> HomeAssistantDeviceListRead:
        snapshot = self._snapshot(refresh=refresh)
        selection = self.selection_repository.read()
        items = snapshot.devices
        if selection_scope == HomeAssistantSelectionScope.VISIBLE:
            visible_entities = self._visible_entities(snapshot.entities, selection)
            items = self._visible_devices(items, visible_entities, selection)
        normalized_search = search.strip().casefold() if search else None
        if normalized_search:
            items = [item for item in items if self._device_matches(item, normalized_search)]
        if area_id:
            items = [item for item in items if item.area_id == area_id]
        total = len(items)
        return HomeAssistantDeviceListRead(
            items=items[offset : offset + limit], total=total, offset=offset, limit=limit
        )

    def entities(
        self,
        *,
        search: str | None = None,
        domain: str | None = None,
        device_id: str | None = None,
        area_id: str | None = None,
        available: bool | None = None,
        device_class: str | None = None,
        unit: str | None = None,
        offset: int = 0,
        limit: int = 250,
        refresh: bool = False,
        selection_scope: HomeAssistantSelectionScope = HomeAssistantSelectionScope.VISIBLE,
    ) -> HomeAssistantEntityListRead:
        items = self._snapshot(refresh=refresh).entities
        if selection_scope == HomeAssistantSelectionScope.VISIBLE:
            items = self._visible_entities(items, self.selection_repository.read())
        normalized_search = search.strip().casefold() if search else None
        if normalized_search:
            items = [item for item in items if self._entity_matches(item, normalized_search)]
        if domain:
            items = [item for item in items if item.domain == domain]
        if device_id:
            items = [item for item in items if item.device_id == device_id]
        if area_id:
            items = [item for item in items if item.area_id == area_id]
        if available is not None:
            items = [item for item in items if item.available is available]
        if device_class:
            items = [item for item in items if item.device_class == device_class]
        if unit:
            items = [item for item in items if item.unit == unit]
        total = len(items)
        return HomeAssistantEntityListRead(
            items=items[offset : offset + limit], total=total, offset=offset, limit=limit
        )

    def linked_objects(
        self,
        *,
        device_ids: set[str],
        entity_ids: set[str],
        refresh: bool = False,
    ) -> tuple[
        list[HomeAssistantDeviceRead],
        list[HomeAssistantEntityRead],
        list[str],
        list[str],
        datetime,
    ]:
        """Resolve locally linked Home Assistant objects from one cached snapshot."""

        snapshot = self._snapshot(refresh=refresh)
        device_by_id = {item.device_id: item for item in snapshot.devices}
        entity_by_id = {item.entity_id: item for item in snapshot.entities}
        devices = [
            device_by_id[item_id] for item_id in sorted(device_ids) if item_id in device_by_id
        ]
        entities = [
            entity_by_id[item_id] for item_id in sorted(entity_ids) if item_id in entity_by_id
        ]
        missing_devices = sorted(device_ids - set(device_by_id))
        missing_entities = sorted(entity_ids - set(entity_by_id))
        return (
            devices,
            entities,
            missing_devices,
            missing_entities,
            snapshot.overview.summary.refreshed_at,
        )

    def _snapshot(self, *, refresh: bool) -> HomeAssistantSnapshot:
        base_url, secret = self._configuration()
        cache_key = self._cache_identifier(base_url, secret)
        now = datetime.now(UTC)
        cls = self.__class__
        with cls._cache_condition:
            if cls._cache_key != cache_key:
                cls._cache_key = cache_key
                cls._cache_expires_at = None
                cls._cache_snapshot = None
                cls._registry_expires_at = None
                cls._registry_snapshot = None
                cls._registry_available = True
                cls._registry_warning = None
            if (
                not refresh
                and cls._cache_expires_at is not None
                and cls._cache_expires_at > now
                and cls._cache_snapshot is not None
            ):
                return cls._cache_snapshot
            if cls._sync_in_progress:
                cls._cache_condition.wait_for(lambda: not cls._sync_in_progress)
                if cls._cache_snapshot is not None:
                    return cls._cache_snapshot
            cls._sync_in_progress = True

        try:
            registry, registry_available, warning = self._registry(
                base_url, secret, refresh=refresh
            )
            config, states = self._load_rest_data(base_url, secret)
            snapshot = self._build_snapshot(
                config,
                states,
                registry,
                registry_available=registry_available,
                warning=warning,
            )
        except Exception:
            with cls._cache_condition:
                cls._sync_in_progress = False
                cls._cache_condition.notify_all()
            raise

        with cls._cache_condition:
            cls._cache_expires_at = datetime.now(UTC) + CACHE_TTL
            cls._cache_snapshot = snapshot
            cls._sync_in_progress = False
            cls._cache_condition.notify_all()
        return snapshot

    def _registry(
        self,
        base_url: str,
        secret: str,
        *,
        refresh: bool,
    ) -> tuple[RegistrySnapshot, bool, str | None]:
        cls = self.__class__
        now = datetime.now(UTC)
        with cls._cache_lock:
            if (
                not refresh
                and cls._registry_snapshot is not None
                and cls._registry_expires_at is not None
                and cls._registry_expires_at > now
            ):
                return (
                    cls._registry_snapshot,
                    cls._registry_available,
                    cls._registry_warning,
                )
        try:
            registry = self._load_registry(base_url, secret)
            available = True
            warning = None
        except (HomeAssistantConnectionError, OSError, TimeoutError, WebSocketException):
            registry = RegistrySnapshot(devices=[], entities=[], areas=[])
            available = False
            warning = (
                "Die Geräte- und Bereichsregister konnten nicht gelesen werden. "
                "Entitätszustände sind weiterhin verfügbar."
            )
        with cls._cache_lock:
            cls._registry_snapshot = registry
            cls._registry_available = available
            cls._registry_warning = warning
            cls._registry_expires_at = now + REGISTRY_CACHE_TTL
        return registry, available, warning

    def _configuration(self) -> tuple[str, str]:
        setting = self.repository.get_integration("home_assistant")
        if setting is None or not setting.enabled:
            raise HomeAssistantConfigurationError(
                "Die Home-Assistant-Integration ist nicht aktiviert."
            )
        if not setting.base_url or not setting.secret:
            raise HomeAssistantConfigurationError(
                "Home-Assistant-URL oder Long-Lived Access Token fehlen."
            )
        return setting.base_url.rstrip("/"), setting.secret

    def _load_rest_data(
        self,
        base_url: str,
        secret: str,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        api_base = self._api_base(base_url)
        headers = {"Authorization": f"Bearer {secret}", "Accept": "application/json"}
        try:
            with httpx.Client(
                timeout=httpx.Timeout(10.0),
                follow_redirects=False,
                transport=self.transport,
                headers={"User-Agent": "DocOfHome Home Assistant read-only"},
            ) as client:
                config_response = client.get(f"{api_base}/config", headers=headers)
                states_response = client.get(f"{api_base}/states", headers=headers)
        except httpx.TimeoutException as exc:
            raise HomeAssistantConnectionError(
                "Zeitüberschreitung beim Lesen von Home Assistant."
            ) from exc
        except httpx.RequestError as exc:
            raise HomeAssistantConnectionError("Home Assistant ist nicht erreichbar.") from exc

        self._require_status(config_response)
        self._require_status(states_response)
        config = self._json_object(config_response)
        states = self._json_object_list(states_response)
        return config, states

    def _load_registry(self, base_url: str, secret: str) -> RegistrySnapshot:
        connection = self.websocket_connector(self._websocket_url(base_url))
        with connection as socket:
            auth_required = self._socket_json(socket.recv(timeout=5.0))
            if auth_required.get("type") != "auth_required":
                raise HomeAssistantConnectionError(
                    "Home Assistant hat den WebSocket-Login nicht angefordert."
                )
            socket.send(json.dumps({"type": "auth", "access_token": secret}))
            auth_result = self._socket_json(socket.recv(timeout=5.0))
            if auth_result.get("type") != "auth_ok":
                raise HomeAssistantConnectionError(
                    "Home Assistant hat den WebSocket-Zugriff abgelehnt."
                )
            devices = self._registry_command(socket, 1, "config/device_registry/list")
            entities = self._registry_command(socket, 2, "config/entity_registry/list")
            areas = self._registry_command(socket, 3, "config/area_registry/list")
        return RegistrySnapshot(devices=devices, entities=entities, areas=areas)

    @staticmethod
    def _connect_websocket(url: str) -> Connection:
        return connect(
            url,
            open_timeout=5.0,
            close_timeout=2.0,
            max_size=WEBSOCKET_MAX_MESSAGE_SIZE,
        )

    @staticmethod
    def _registry_command(
        socket: Connection,
        command_id: int,
        command_type: str,
    ) -> list[dict[str, Any]]:
        socket.send(json.dumps({"id": command_id, "type": command_type}))
        payload = HomeAssistantService._socket_json(socket.recv(timeout=5.0))
        if payload.get("id") != command_id or payload.get("success") is not True:
            raise HomeAssistantConnectionError(
                f"Home Assistant konnte {command_type} nicht liefern."
            )
        result = payload.get("result")
        if not isinstance(result, list) or not all(isinstance(item, dict) for item in result):
            raise HomeAssistantConnectionError(
                f"Home Assistant liefert für {command_type} ein unerwartetes Format."
            )
        return result

    @staticmethod
    def _socket_json(message: str | bytes) -> dict[str, Any]:
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        try:
            payload = json.loads(message)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HomeAssistantConnectionError(
                "Home Assistant liefert eine ungültige WebSocket-Antwort."
            ) from exc
        if not isinstance(payload, dict):
            raise HomeAssistantConnectionError(
                "Home Assistant liefert ein unerwartetes WebSocket-Format."
            )
        return payload

    def _build_snapshot(
        self,
        config: dict[str, Any],
        states: list[dict[str, Any]],
        registry: RegistrySnapshot,
        *,
        registry_available: bool,
        warning: str | None,
    ) -> HomeAssistantSnapshot:
        areas = self._areas(registry.areas)
        areas_by_id = {area.area_id: area for area in areas}
        device_rows = {
            str(item.get("id")): item
            for item in registry.devices
            if isinstance(item.get("id"), str)
        }
        entity_rows = {
            str(item.get("entity_id")): item
            for item in registry.entities
            if isinstance(item.get("entity_id"), str)
        }
        state_rows = {
            str(item.get("entity_id")): item
            for item in states
            if isinstance(item.get("entity_id"), str)
        }
        entity_ids = sorted(set(state_rows) | set(entity_rows))
        entity_items = [
            self._entity(
                entity_id,
                state_rows.get(entity_id),
                entity_rows.get(entity_id),
                device_rows,
                areas_by_id,
            )
            for entity_id in entity_ids
        ]
        entity_counts: dict[str, int] = {}
        for entity in entity_items:
            if entity.device_id:
                entity_counts[entity.device_id] = entity_counts.get(entity.device_id, 0) + 1
        device_items = [
            self._device(device_id, row, entity_counts, areas_by_id)
            for device_id, row in sorted(device_rows.items(), key=self._device_sort_key)
        ]
        domains = sorted({entity.domain for entity in entity_items})
        device_classes = sorted({
            entity.device_class for entity in entity_items if entity.device_class
        })
        units = sorted({entity.unit for entity in entity_items if entity.unit})
        summary = HomeAssistantSummaryRead(
            location_name=self._optional_string(config.get("location_name")),
            version=self._optional_string(config.get("version")),
            time_zone=self._optional_string(config.get("time_zone")),
            device_count=len(device_items),
            entity_count=len(entity_items),
            area_count=len(areas),
            unavailable_entity_count=sum(not entity.available for entity in entity_items),
            selection_mode=HomeAssistantSelectionMode.ALL,
            selected_entity_count=0,
            visible_device_count=len(device_items),
            visible_entity_count=len(entity_items),
            registry_available=registry_available,
            warning=warning,
            refreshed_at=datetime.now(UTC),
        )
        return HomeAssistantSnapshot(
            overview=HomeAssistantOverviewRead(
                summary=summary,
                areas=areas,
                domains=domains,
                device_classes=device_classes,
                units=units,
            ),
            devices=device_items,
            entities=entity_items,
        )

    @staticmethod
    def _visible_entities(
        items: list[HomeAssistantEntityRead],
        selection: HomeAssistantSelectionState,
    ) -> list[HomeAssistantEntityRead]:
        if selection.mode == HomeAssistantSelectionMode.ALL.value:
            return items
        selected_ids = set(selection.entity_ids)
        return [item for item in items if item.entity_id in selected_ids]

    @staticmethod
    def _visible_devices(
        items: list[HomeAssistantDeviceRead],
        visible_entities: list[HomeAssistantEntityRead],
        selection: HomeAssistantSelectionState,
    ) -> list[HomeAssistantDeviceRead]:
        if selection.mode == HomeAssistantSelectionMode.ALL.value:
            return items
        entity_counts: dict[str, int] = {}
        for entity in visible_entities:
            if entity.device_id:
                entity_counts[entity.device_id] = entity_counts.get(entity.device_id, 0) + 1
        return [
            item.model_copy(update={"entity_count": entity_counts[item.device_id]})
            for item in items
            if item.device_id in entity_counts
        ]

    @staticmethod
    def _areas(rows: list[dict[str, Any]]) -> list[HomeAssistantAreaRead]:
        items = [
            HomeAssistantAreaRead(
                area_id=str(row["area_id"]),
                name=str(row.get("name") or row["area_id"]),
                floor_id=HomeAssistantService._optional_string(row.get("floor_id")),
            )
            for row in rows
            if isinstance(row.get("area_id"), str)
        ]
        return sorted(items, key=lambda item: item.name.casefold())

    def _device(
        self,
        device_id: str,
        row: dict[str, Any],
        entity_counts: dict[str, int],
        areas_by_id: dict[str, HomeAssistantAreaRead],
    ) -> HomeAssistantDeviceRead:
        area_id = self._optional_string(row.get("area_id"))
        area = areas_by_id.get(area_id or "")
        name = self._first_string(row.get("name_by_user"), row.get("name"), device_id)
        return HomeAssistantDeviceRead(
            device_id=device_id,
            name=name,
            manufacturer=self._optional_string(row.get("manufacturer")),
            model=self._optional_string(row.get("model")),
            model_id=self._optional_string(row.get("model_id")),
            sw_version=self._optional_string(row.get("sw_version")),
            hw_version=self._optional_string(row.get("hw_version")),
            serial_number=self._optional_string(row.get("serial_number")),
            area_id=area_id,
            area_name=area.name if area else None,
            entity_count=entity_counts.get(device_id, 0),
            disabled=row.get("disabled_by") is not None,
        )

    def _entity(
        self,
        entity_id: str,
        state_row: dict[str, Any] | None,
        registry_row: dict[str, Any] | None,
        device_rows: dict[str, dict[str, Any]],
        areas_by_id: dict[str, HomeAssistantAreaRead],
    ) -> HomeAssistantEntityRead:
        state_row = state_row or {}
        registry_row = registry_row or {}
        attributes_raw = state_row.get("attributes")
        attributes = attributes_raw if isinstance(attributes_raw, dict) else {}
        device_id = self._optional_string(registry_row.get("device_id"))
        device_row = device_rows.get(device_id or "", {})
        area_id = self._first_optional_string(
            registry_row.get("area_id"), device_row.get("area_id")
        )
        area = areas_by_id.get(area_id or "")
        state = self._optional_string(state_row.get("state")) or "not_loaded"
        name = self._first_string(
            registry_row.get("name"),
            attributes.get("friendly_name"),
            registry_row.get("original_name"),
            entity_id,
        )
        domain = entity_id.partition(".")[0]
        device_name = None
        if device_id:
            device_name = self._first_string(
                device_row.get("name_by_user"), device_row.get("name"), device_id
            )
        return HomeAssistantEntityRead(
            entity_id=entity_id,
            name=name,
            domain=domain,
            state=state,
            unit=self._optional_string(attributes.get("unit_of_measurement")),
            device_class=self._first_optional_string(
                attributes.get("device_class"), registry_row.get("original_device_class")
            ),
            icon=self._optional_string(attributes.get("icon")),
            device_id=device_id,
            device_name=device_name,
            area_id=area_id,
            area_name=area.name if area else None,
            platform=self._optional_string(registry_row.get("platform")),
            entity_category=self._optional_string(registry_row.get("entity_category")),
            last_changed=self._optional_datetime(state_row.get("last_changed")),
            last_updated=self._optional_datetime(state_row.get("last_updated")),
            available=state != "unavailable" and state != "not_loaded",
            disabled=registry_row.get("disabled_by") is not None,
        )

    @staticmethod
    def _device_sort_key(item: tuple[str, dict[str, Any]]) -> tuple[str, str]:
        device_id, row = item
        name = HomeAssistantService._first_string(
            row.get("name_by_user"), row.get("name"), device_id
        )
        return name.casefold(), device_id

    @staticmethod
    def _device_matches(item: HomeAssistantDeviceRead, search: str) -> bool:
        values = (
            item.name,
            item.manufacturer,
            item.model,
            item.model_id,
            item.serial_number,
            item.area_name,
            item.device_id,
        )
        return any(search in value.casefold() for value in values if value)

    @staticmethod
    def _entity_matches(item: HomeAssistantEntityRead, search: str) -> bool:
        values = (
            item.name,
            item.entity_id,
            item.state,
            item.device_name,
            item.area_name,
            item.platform,
            item.device_class,
        )
        return any(search in value.casefold() for value in values if value)

    @staticmethod
    def _api_base(base_url: str) -> str:
        normalized = base_url.rstrip("/")
        return normalized if urlparse(normalized).path.endswith("/api") else f"{normalized}/api"

    @staticmethod
    def _websocket_url(base_url: str) -> str:
        parsed = urlparse(base_url.rstrip("/"))
        scheme = "wss" if parsed.scheme == "https" else "ws"
        path = parsed.path.rstrip("/")
        if path.endswith("/api"):
            path = path[:-4]
        path = f"{path}/api/websocket"
        return urlunparse((scheme, parsed.netloc, path, "", "", ""))

    @staticmethod
    def _cache_identifier(base_url: str, secret: str) -> str:
        token_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()
        return f"{base_url}:{token_hash}"

    @staticmethod
    def _require_status(response: httpx.Response) -> None:
        if response.status_code == 200:
            return
        if response.status_code in {401, 403}:
            raise HomeAssistantConnectionError("Das Home-Assistant-Token wurde abgelehnt.")
        if 300 <= response.status_code < 400:
            raise HomeAssistantConnectionError(
                "Home Assistant antwortet mit einer Umleitung. Nutze die direkte interne URL."
            )
        raise HomeAssistantConnectionError(
            f"Home Assistant antwortet unerwartet mit HTTP {response.status_code}."
        )

    @staticmethod
    def _json_object(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise HomeAssistantConnectionError(
                "Home Assistant liefert keine gültige JSON-Konfiguration."
            ) from exc
        if not isinstance(payload, dict):
            raise HomeAssistantConnectionError(
                "Home Assistant liefert ein unerwartetes Konfigurationsformat."
            )
        return payload

    @staticmethod
    def _json_object_list(response: httpx.Response) -> list[dict[str, Any]]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise HomeAssistantConnectionError(
                "Home Assistant liefert keine gültige Zustandsliste."
            ) from exc
        if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
            raise HomeAssistantConnectionError(
                "Home Assistant liefert ein unerwartetes Zustandsformat."
            )
        return payload

    @staticmethod
    def _optional_string(value: object) -> str | None:
        return str(value) if value is not None and str(value).strip() else None

    @staticmethod
    def _first_optional_string(*values: object) -> str | None:
        for value in values:
            normalized = HomeAssistantService._optional_string(value)
            if normalized is not None:
                return normalized
        return None

    @staticmethod
    def _first_string(*values: object) -> str:
        return HomeAssistantService._first_optional_string(*values) or "Unbenannt"

    @staticmethod
    def _optional_datetime(value: object) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
