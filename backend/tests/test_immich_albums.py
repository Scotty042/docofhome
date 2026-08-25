from datetime import UTC, datetime

import httpx

from app.connectors.immich import ImmichConnector


def test_lists_and_sorts_read_only_immich_albums() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json=[
                {
                    "id": "00000000-0000-0000-0000-000000000002",
                    "albumName": "Zählerkasten",
                    "assetCount": 3,
                    "albumThumbnailAssetId": None,
                    "startDate": "2026-02-01T10:00:00Z",
                    "endDate": "2026-02-02T10:00:00Z",
                },
                {
                    "id": "00000000-0000-0000-0000-000000000001",
                    "albumName": "Elektro",
                    "assetCount": 7,
                    "albumThumbnailAssetId": "00000000-0000-0000-0000-000000000010",
                    "startDate": None,
                    "endDate": None,
                },
            ],
        )

    connector = ImmichConnector(
        base_url="http://immich.test",
        api_key="secret",
        transport=httpx.MockTransport(handler),
    )

    albums = connector.list_albums()

    assert requests[0].method == "GET"
    assert requests[0].url.path == "/api/albums"
    assert [album.album_name for album in albums] == ["Elektro", "Zählerkasten"]
    assert albums[0].asset_count == 7
    assert albums[0].thumbnail_asset_id == "00000000-0000-0000-0000-000000000010"
    assert albums[1].start_date == datetime(2026, 2, 1, 10, tzinfo=UTC)


def test_rejects_invalid_immich_album_response() -> None:
    connector = ImmichConnector(
        base_url="http://immich.test/api",
        api_key="secret",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"items": []})),
    )

    try:
        connector.list_albums()
    except RuntimeError as exc:
        assert str(exc) == "Immich liefert keine gültige Albumliste."
    else:
        raise AssertionError("Ungültige Albumantwort wurde akzeptiert.")
