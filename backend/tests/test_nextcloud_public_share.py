import httpx

from app.connectors.nextcloud_public_share import NextcloudPublicShareUploader


def test_public_share_url_and_upload_headers() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["body"] = request.content
        return httpx.Response(201)

    uploader = NextcloudPublicShareUploader(
        share_url="https://cloud.example.test/index.php/s/AbcDef123456",
        transport=httpx.MockTransport(handler),
    )
    result = uploader.upload(
        "docofhome-feedback-test.zip",
        content=b"PK-test",
        content_type="application/zip",
    )

    assert result == 201
    assert captured["url"] == (
        "https://cloud.example.test/public.php/dav/files/AbcDef123456/"
        "docofhome-feedback-test.zip"
    )
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["x-requested-with"] == "XMLHttpRequest"
    assert headers["if-none-match"] == "*"
    assert captured["body"] == b"PK-test"
