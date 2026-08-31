import httpx
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.models.integration_setting import IntegrationSetting
from app.services.paperless import PaperlessService


def test_paperless_uses_internal_url_for_api_and_browser_url_for_links() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "paperless"
        assert request.url.path == "/api/documents/"
        return httpx.Response(
            200,
            json={
                "count": 1,
                "results": [{"id": 42, "title": "Rechnung"}],
            },
        )

    with Session(engine) as session:
        session.add(
            IntegrationSetting(
                kind="paperless",
                enabled=True,
                base_url="http://paperless:8000",
                browser_url="https://paperless.example.test",
                secret="token",
            )
        )
        session.commit()
        service = PaperlessService(session)
        connector = service._connector()
        connector.transport = httpx.MockTransport(handler)
        service._connector = lambda: connector  # type: ignore[method-assign]

        result = service.search("Rechnung")

    assert result[0].source_url == "https://paperless.example.test/documents/42/details"
