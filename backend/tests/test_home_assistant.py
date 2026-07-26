import json
from collections.abc import Iterator

import httpx
import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models.integration_setting import IntegrationSetting
from app.schemas.home_assistant import (
    HomeAssistantSelectionMode,
    HomeAssistantSelectionScope,
    HomeAssistantSelectionWrite,
)
from app.services import home_assistant as home_assistant_module
from app.services.home_assistant import (
    WEBSOCKET_MAX_MESSAGE_SIZE,
    HomeAssistantConfigurationError,
    HomeAssistantService,
)
from app.services.home_assistant_selection import HomeAssistantSelectionService


class FakeSocket:
    def __init__(self) -> None:
        self.responses = iter(
            [
                {"type": "auth_required"},
                {"type": "auth_ok", "ha_version": "2026.7.1"},
                {
                    "id": 1,
                    "success": True,
                    "result": [
                        {
                            "id": "device-1",
                            "name": "Shelly 3EM",
                            "manufacturer": "Shelly",
                            "model": "3EM-63 Gen3",
                            "area_id": "utility",
                        }
                    ],
                },
                {
                    "id": 2,
                    "success": True,
                    "result": [
                        {
                            "entity_id": "sensor.grid_power",
                            "device_id": "device-1",
                            "platform": "shelly",
                            "original_name": "Grid power",
                        },
                        {
                            "entity_id": "sensor.offline",
                            "device_id": "device-1",
                            "platform": "shelly",
                            "original_name": "Offline sensor",
                        },
                    ],
                },
                {
                    "id": 3,
                    "success": True,
                    "result": [{"area_id": "utility", "name": "Zählerraum"}],
                },
            ]
        )
        self.sent: list[dict[str, object]] = []

    def __enter__(self) -> "FakeSocket":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def recv(self, timeout: float | None = None) -> str:
        del timeout
        return json.dumps(next(self.responses))

    def send(self, message: str) -> None:
        self.sent.append(json.loads(message))


def session_with_home_assistant(*, enabled: bool = True) -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    session.add(
        IntegrationSetting(
            kind="home_assistant",
            enabled=enabled,
            base_url="http://home-assistant.local:8123",
            secret="long-lived-token",
        )
    )
    session.commit()
    return session


def home_assistant_transport(request: httpx.Request) -> httpx.Response:
    assert request.headers["authorization"] == "Bearer long-lived-token"
    if request.url.path == "/api/config":
        return httpx.Response(
            200,
            json={
                "location_name": "Zuhause",
                "version": "2026.7.1",
                "time_zone": "Europe/Berlin",
            },
        )
    if request.url.path == "/api/states":
        return httpx.Response(
            200,
            json=[
                {
                    "entity_id": "sensor.grid_power",
                    "state": "42.5",
                    "attributes": {
                        "friendly_name": "Netzleistung",
                        "unit_of_measurement": "W",
                        "device_class": "power",
                    },
                    "last_changed": "2026-07-21T17:00:00+00:00",
                    "last_updated": "2026-07-21T17:00:01+00:00",
                },
                {
                    "entity_id": "sensor.offline",
                    "state": "unavailable",
                    "attributes": {"friendly_name": "Nicht erreichbar"},
                    "last_changed": "2026-07-21T16:00:00+00:00",
                    "last_updated": "2026-07-21T16:00:00+00:00",
                },
            ],
        )
    raise AssertionError(f"Unexpected request: {request.url}")


@pytest.fixture(autouse=True)
def clear_home_assistant_cache() -> Iterator[None]:
    HomeAssistantService._cache_key = None
    HomeAssistantService._cache_expires_at = None
    HomeAssistantService._cache_snapshot = None
    HomeAssistantService._registry_expires_at = None
    HomeAssistantService._registry_snapshot = None
    HomeAssistantService._registry_available = True
    HomeAssistantService._registry_warning = None
    HomeAssistantService._sync_in_progress = False
    yield
    HomeAssistantService._cache_key = None
    HomeAssistantService._cache_expires_at = None
    HomeAssistantService._cache_snapshot = None
    HomeAssistantService._registry_expires_at = None
    HomeAssistantService._registry_snapshot = None
    HomeAssistantService._registry_available = True
    HomeAssistantService._registry_warning = None
    HomeAssistantService._sync_in_progress = False


def test_home_assistant_snapshot_merges_registries_and_states() -> None:
    socket = FakeSocket()
    service = HomeAssistantService(
        session_with_home_assistant(),
        transport=httpx.MockTransport(home_assistant_transport),
        websocket_connector=lambda _: socket,
    )

    overview = service.overview(refresh=True)
    devices = service.devices(search="Shelly")
    entities = service.entities(area_id="utility")
    unavailable = service.entities(available=False)

    assert overview.summary.location_name == "Zuhause"
    assert overview.summary.registry_available is True
    assert overview.summary.device_count == 1
    assert overview.summary.entity_count == 2
    assert overview.summary.unavailable_entity_count == 1
    assert overview.areas[0].name == "Zählerraum"
    assert devices.total == 1
    assert devices.items[0].entity_count == 2
    assert entities.total == 2
    assert entities.items[0].device_name == "Shelly 3EM"
    assert entities.items[0].area_name == "Zählerraum"
    assert unavailable.items[0].entity_id == "sensor.offline"
    assert socket.sent[0] == {"type": "auth", "access_token": "long-lived-token"}


def test_home_assistant_falls_back_to_rest_states_when_registry_is_unavailable() -> None:
    def unavailable_socket(_: str) -> FakeSocket:
        raise OSError("websocket blocked")

    service = HomeAssistantService(
        session_with_home_assistant(),
        transport=httpx.MockTransport(home_assistant_transport),
        websocket_connector=unavailable_socket,
    )

    overview = service.overview(refresh=True)
    entities = service.entities()

    assert overview.summary.registry_available is False
    assert overview.summary.warning is not None
    assert overview.summary.device_count == 0
    assert entities.total == 2
    assert entities.items[0].device_id is None


def test_websocket_connection_accepts_large_home_assistant_registries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    expected_socket: object = FakeSocket()

    def fake_connect(url: str, **kwargs: object) -> object:
        captured["url"] = url
        captured.update(kwargs)
        return expected_socket

    monkeypatch.setattr(home_assistant_module, "connect", fake_connect)

    socket = HomeAssistantService._connect_websocket("ws://home-assistant.local:8123/api/websocket")

    assert socket is expected_socket
    assert captured["max_size"] == WEBSOCKET_MAX_MESSAGE_SIZE
    assert WEBSOCKET_MAX_MESSAGE_SIZE > 1_048_576


def test_home_assistant_requires_enabled_integration() -> None:
    service = HomeAssistantService(session_with_home_assistant(enabled=False))

    with pytest.raises(HomeAssistantConfigurationError):
        service.overview(refresh=True)


def test_home_assistant_applies_selected_entities_to_visible_entities_and_devices() -> None:
    session = session_with_home_assistant()
    HomeAssistantSelectionService(session).replace(
        HomeAssistantSelectionWrite(
            mode=HomeAssistantSelectionMode.SELECTED,
            entity_ids=["sensor.grid_power"],
        )
    )
    service = HomeAssistantService(
        session,
        transport=httpx.MockTransport(home_assistant_transport),
        websocket_connector=lambda _: FakeSocket(),
    )

    overview = service.overview(refresh=True)
    visible_entities = service.entities()
    all_entities = service.entities(selection_scope=HomeAssistantSelectionScope.ALL)
    visible_devices = service.devices()

    assert overview.summary.entity_count == 2
    assert overview.summary.device_count == 1
    assert overview.summary.selection_mode == HomeAssistantSelectionMode.SELECTED
    assert overview.summary.selected_entity_count == 1
    assert overview.summary.visible_entity_count == 1
    assert overview.summary.visible_device_count == 1
    assert [item.entity_id for item in visible_entities.items] == ["sensor.grid_power"]
    assert all_entities.total == 2
    assert visible_devices.items[0].entity_count == 1


def test_home_assistant_selected_mode_can_intentionally_show_no_entities() -> None:
    session = session_with_home_assistant()
    HomeAssistantSelectionService(session).replace(
        HomeAssistantSelectionWrite(
            mode=HomeAssistantSelectionMode.SELECTED,
            entity_ids=[],
        )
    )
    service = HomeAssistantService(
        session,
        transport=httpx.MockTransport(home_assistant_transport),
        websocket_connector=lambda _: FakeSocket(),
    )

    overview = service.overview(refresh=True)

    assert service.entities().total == 0
    assert service.devices().total == 0
    assert overview.summary.entity_count == 2
    assert overview.summary.visible_entity_count == 0
    assert overview.summary.visible_device_count == 0


def test_home_assistant_entities_are_server_paginated_and_filtered() -> None:
    def large_transport(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/config":
            return httpx.Response(200, json={"location_name": "Lasttest"})
        if request.url.path == "/api/states":
            return httpx.Response(
                200,
                json=[
                    {
                        "entity_id": f"sensor.power_{index:04}",
                        "state": str(index),
                        "attributes": {
                            "friendly_name": f"Leistung {index:04}",
                            "unit_of_measurement": "W",
                            "device_class": "power",
                        },
                    }
                    for index in range(5000)
                ],
            )
        raise AssertionError(f"Unexpected request: {request.url}")

    service = HomeAssistantService(
        session_with_home_assistant(),
        transport=httpx.MockTransport(large_transport),
        websocket_connector=lambda _: (_ for _ in ()).throw(OSError("no registry")),
    )

    page = service.entities(
        device_class="power",
        unit="W",
        offset=200,
        limit=100,
        refresh=True,
        selection_scope=HomeAssistantSelectionScope.ALL,
    )

    assert page.total == 5000
    assert len(page.items) == 100
    assert page.items[0].entity_id == "sensor.power_0200"
    assert page.items[-1].entity_id == "sensor.power_0299"


def test_parallel_home_assistant_reads_share_one_sync() -> None:
    import threading
    import time

    request_count = 0
    request_lock = threading.Lock()

    def slow_transport(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        with request_lock:
            request_count += 1
        time.sleep(0.05)
        return home_assistant_transport(request)

    first = HomeAssistantService(
        session_with_home_assistant(),
        transport=httpx.MockTransport(slow_transport),
        websocket_connector=lambda _: FakeSocket(),
    )
    second = HomeAssistantService(
        session_with_home_assistant(),
        transport=httpx.MockTransport(slow_transport),
        websocket_connector=lambda _: FakeSocket(),
    )
    barrier = threading.Barrier(2)
    results: list[int] = []

    def run(service: HomeAssistantService) -> None:
        barrier.wait()
        results.append(service.entities(refresh=True).total)

    threads = [threading.Thread(target=run, args=(service,)) for service in (first, second)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert results == [2, 2]
    assert request_count == 2  # one /config and one /states request for the shared sync
