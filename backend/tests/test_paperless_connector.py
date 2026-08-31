import httpx

from app.connectors.paperless import PaperlessConnector


def test_paperless_search_uses_token_and_fulltext_query() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/documents/"
        assert request.url.params["text"] == "Tierarzt"
        assert request.headers["authorization"] == "Token paperless-secret"
        return httpx.Response(
            200,
            json={
                "count": 1,
                "results": [
                    {
                        "id": 42,
                        "title": "Tierarztrechnung",
                        "created": "2026-04-22",
                        "added": "2026-04-22T12:00:00+02:00",
                        "original_file_name": "rechnung.pdf",
                    }
                ],
            },
        )

    connector = PaperlessConnector(
        base_url="https://paperless.example.test",
        token="paperless-secret",
        transport=httpx.MockTransport(handler),
    )

    documents = connector.search("Tierarzt")

    assert documents[0].document_id == 42
    assert documents[0].title == "Tierarztrechnung"
    assert connector.document_url(42).endswith("/documents/42/details")
