import json
from datetime import UTC, datetime

import httpx

from app.connectors.immich import ImmichConnector


def test_taken_date_filters_are_forwarded_to_immich() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.read()))
        return httpx.Response(
            200,
            json={
                "assets": {
                    "items": [],
                    "total": 0,
                }
            },
        )

    connector = ImmichConnector(
        base_url="http://immich.test",
        api_key="secret",
        transport=httpx.MockTransport(handler),
    )
    connector.search_images(
        page=1,
        page_size=36,
        search="verteiler",
        favorite_only=True,
        taken_after=datetime(2026, 1, 1, tzinfo=UTC),
        taken_before=datetime(2026, 2, 1, tzinfo=UTC),
    )

    assert captured["originalFileName"] == "verteiler"
    assert captured["isFavorite"] is True
    assert captured["takenAfter"] == "2026-01-01T00:00:00+00:00"
    assert captured["takenBefore"] == "2026-02-01T00:00:00+00:00"
    assert captured["type"] == "IMAGE"
    assert captured["withDeleted"] is False


def test_without_dates_uses_existing_search_contract() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"assets": {"items": [], "total": 0}})

    connector = ImmichConnector(
        base_url="http://immich.test/api",
        api_key="secret",
        transport=httpx.MockTransport(handler),
    )
    connector.search_images(page=2, page_size=12)

    assert len(requests) == 1
    assert requests[0].url.path == "/api/search/metadata"
