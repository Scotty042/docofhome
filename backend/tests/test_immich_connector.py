from uuid import UUID

import httpx
import pytest

from app.connectors.immich import (
    MAX_THUMBNAIL_BYTES,
    ImmichConnector,
    ImmichConnectorError,
)

IMAGE_ID = UUID("11111111-1111-4111-8111-111111111111")


def image_payload() -> dict[str, object]:
    return {
        "id": str(IMAGE_ID),
        "type": "IMAGE",
        "originalFileName": "panel.jpg",
        "fileCreatedAt": "2026-07-20T10:30:00Z",
        "width": 1600,
        "height": 1200,
        "isFavorite": True,
    }


def test_search_uses_read_only_metadata_api_key_filters_and_paging() -> None:
    album_id = UUID("22222222-2222-4222-8222-222222222222")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/search/metadata"
        assert request.headers["x-api-key"] == "immich-secret"
        body = request.read().decode()
        assert '"page":2' in body
        assert '"size":24' in body
        assert '"type":"IMAGE"' in body
        assert '"originalFileName":"panel"' in body
        assert str(album_id) in body
        return httpx.Response(
            200,
            json={"assets": {"items": [image_payload()], "total": 25}},
        )

    connector = ImmichConnector(
        base_url="http://immich.local/api",
        api_key="immich-secret",
        transport=httpx.MockTransport(handler),
    )

    result = connector.search_images(
        page=2,
        page_size=24,
        search="panel",
        album_id=album_id,
    )

    assert result.total == 25
    assert result.pages == 2
    assert result.items[0].original_file_name == "panel.jpg"
    assert result.items[0].width == 1600


def test_asset_detail_and_thumbnail_are_read_only_and_bounded() -> None:
    methods: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        methods.append(request.method)
        assert request.headers["x-api-key"] == "immich-secret"
        if request.url.path.endswith("/thumbnail"):
            return httpx.Response(200, content=b"jpeg", headers={"content-type": "image/jpeg"})
        return httpx.Response(200, json=image_payload())

    connector = ImmichConnector(
        base_url="http://immich.local",
        api_key="immich-secret",
        transport=httpx.MockTransport(handler),
    )

    assert connector.get_image(IMAGE_ID).immich_asset_id == str(IMAGE_ID)
    assert connector.get_thumbnail(IMAGE_ID).content == b"jpeg"
    assert methods == ["GET", "GET"]


@pytest.mark.parametrize(
    ("status", "headers", "content", "message"),
    [
        (302, {"location": "http://other.local"}, b"", "Umleitung"),
        (200, {"content-type": "image/svg+xml"}, b"<svg/>", "unterstütztes"),
        (
            200,
            {"content-type": "image/jpeg"},
            b"x" * (MAX_THUMBNAIL_BYTES + 1),
            "unerwartet groß",
        ),
    ],
    ids=["redirect", "unsafe-media", "oversize"],
)
def test_thumbnail_rejects_redirects_unsafe_media_and_oversize(
    status: int,
    headers: dict[str, str],
    content: bytes,
    message: str,
) -> None:
    connector = ImmichConnector(
        base_url="http://immich.local",
        api_key="secret",
        transport=httpx.MockTransport(
            lambda _: httpx.Response(status, headers=headers, content=content)
        ),
    )

    with pytest.raises(ImmichConnectorError, match=message):
        connector.get_thumbnail(IMAGE_ID)


def test_connector_errors_never_include_remote_secret_body() -> None:
    connector = ImmichConnector(
        base_url="http://immich.local",
        api_key="top-secret",
        transport=httpx.MockTransport(
            lambda _: httpx.Response(403, json={"detail": "top-secret remote body"})
        ),
    )

    with pytest.raises(ImmichConnectorError) as captured:
        connector.get_image(IMAGE_ID)

    assert "top-secret" not in str(captured.value)
    assert "remote body" not in str(captured.value)
