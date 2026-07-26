import httpx
import pytest

from app.connectors.nextcloud import (
    MAX_PROPFIND_BYTES,
    NextcloudConnectorError,
    NextcloudResponseError,
    NextcloudWebDavConnector,
)


def connector(*, transport: httpx.BaseTransport | None = None) -> NextcloudWebDavConnector:
    return NextcloudWebDavConnector(
        base_url="https://nextcloud.example.test",
        account="document user",
        secret="test-only-secret",
        transport=transport,
    )


def test_webdav_urls_and_hrefs_are_encoded_and_account_scoped() -> None:
    client = connector()

    assert client.url(["Haus", "Rechnung 2026.pdf"]).endswith(
        "/remote.php/dav/files/document%20user/Haus/Rechnung%202026.pdf"
    )
    assert client.parts_from_href(
        "/remote.php/dav/files/document%20user/Haus/Rechnung%202026.pdf"
    ) == ["Haus", "Rechnung 2026.pdf"]

    for unsafe_href in (
        "/remote.php/dav/files/other/Haus/Rechnung.pdf",
        "/remote.php/dav/files/document%20user/Haus/%2E%2E/secret",
        "/remote.php/dav/files/document%20user/Haus/folder%5Cfile.pdf",
    ):
        with pytest.raises(NextcloudConnectorError):
            client.parts_from_href(unsafe_href)


def test_propfind_stream_is_bounded_by_content_length() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            207,
            headers={"Content-Length": str(MAX_PROPFIND_BYTES + 1)},
            content=b"",
        )
    )

    with pytest.raises(NextcloudResponseError) as exc_info:
        connector(transport=transport).propfind(["docofhome", "Documents"], depth=1)

    assert exc_info.value.status_code == 413


def test_propfind_stream_is_bounded_when_length_header_is_missing() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(207, content=b"x" * (MAX_PROPFIND_BYTES + 1))
    )

    with pytest.raises(NextcloudResponseError) as exc_info:
        connector(transport=transport).propfind(["docofhome", "Documents"], depth=1)

    assert exc_info.value.status_code == 413


def test_delete_sends_optional_etag_precondition() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.method == "DELETE"
        assert request.headers["if-match"] == '"folder-etag"'
        return httpx.Response(204)

    connector(transport=httpx.MockTransport(handler)).delete(
        ["docofhome", "Documents", "Empty"], etag='"folder-etag"'
    )

    assert len(requests) == 1
