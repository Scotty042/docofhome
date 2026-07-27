from collections.abc import Callable

import httpx
import pytest
from sqlmodel import Session

from app.models.application_setting import ApplicationSetting
from app.services.product_images import (
    ProductImageService,
    ProductImageUnavailableError,
    ProductImageValidationError,
)


def test_product_image_signature_validation_accepts_supported_formats() -> None:
    ProductImageService._validate_image_signature(b"\xff\xd8\xfftest", "image/jpeg")
    ProductImageService._validate_image_signature(b"\x89PNG\r\n\x1a\ntest", "image/png")
    ProductImageService._validate_image_signature(b"GIF89atest", "image/gif")
    ProductImageService._validate_image_signature(b"RIFF\x04\x00\x00\x00WEBPtest", "image/webp")


def test_product_image_signature_validation_rejects_mismatched_content() -> None:
    with pytest.raises(ProductImageValidationError):
        ProductImageService._validate_image_signature(b"not an image", "image/png")


def test_online_product_image_import_allows_only_wikimedia_hosts() -> None:
    ProductImageService._validate_remote_url(
        "https://upload.wikimedia.org/example/product.jpg",
        allowed_hosts=frozenset({"upload.wikimedia.org"}),
    )
    with pytest.raises(ProductImageValidationError):
        ProductImageService._validate_remote_url(
            "https://127.0.0.1/internal.png",
            allowed_hosts=frozenset({"upload.wikimedia.org"}),
        )


def _online_service(
    session: Session,
    handler: Callable[[httpx.Request], httpx.Response],
) -> ProductImageService:
    session.add(
        ApplicationSetting(
            installation_name="Test House",
            timezone="Europe/Berlin",
            online_product_image_search_enabled=True,
        )
    )
    session.commit()
    return ProductImageService(session, transport=httpx.MockTransport(handler))


def test_online_product_search_reports_timeout(session: Session) -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("offline", request=request)

    service = _online_service(session, timeout)

    with pytest.raises(ProductImageUnavailableError):
        service.search_online("ABB S201")


def test_online_product_search_reports_provider_error(session: Session) -> None:
    service = _online_service(
        session,
        lambda request: httpx.Response(503, request=request, json={"error": "unavailable"}),
    )

    with pytest.raises(ProductImageUnavailableError):
        service.search_online("ABB S201")


def test_online_product_search_ignores_unapproved_result_hosts(session: Session) -> None:
    service = _online_service(
        session,
        lambda request: httpx.Response(
            200,
            request=request,
            json={
                "query": {
                    "pages": [
                        {
                            "title": "File:Unsafe.jpg",
                            "imageinfo": [
                                {
                                    "url": "https://example.org/unsafe.jpg",
                                    "thumburl": "https://example.org/thumb.jpg",
                                    "descriptionurl": "https://example.org/source",
                                }
                            ],
                        }
                    ]
                }
            },
        ),
    )

    assert service.search_online("ABB S201").items == []


def test_duckduckgo_image_search_scores_specific_product_results_first(
    session: Session,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "commons.wikimedia.org":
            return httpx.Response(200, request=request, json={"query": {"pages": []}})
        if request.url.host == "duckduckgo.com" and request.url.path == "/":
            return httpx.Response(200, request=request, text="vqd='123-456'")
        if request.url.host == "duckduckgo.com" and request.url.path == "/i.js":
            return httpx.Response(
                200,
                request=request,
                json={
                    "results": [
                        {
                            "title": "Generic electrical company logo",
                            "image": "https://images.example.org/logo.png",
                            "thumbnail": "https://images.example.org/logo-thumb.png",
                            "url": "https://example.org/logo",
                            "source": "Example",
                        },
                        {
                            "title": "ABB S201 B16 Sicherungsautomat Produktfoto",
                            "image": "https://cdn.example.org/abb-s201-b16.jpg",
                            "thumbnail": "https://cdn.example.org/abb-s201-b16-thumb.jpg",
                            "url": "https://example.org/abb-s201-b16",
                            "source": "Example Shop",
                        },
                    ]
                },
            )
        raise AssertionError(f"Unexpected request: {request.url}")

    result = _online_service(session, handler).search_online("ABB S201 B16")

    assert result.items[0].title == "ABB S201 B16 Sicherungsautomat Produktfoto"
    assert result.items[0].provider == "DuckDuckGo Images"


def test_remote_image_validation_blocks_private_hosts_for_generic_search_results() -> None:
    with pytest.raises(ProductImageValidationError):
        ProductImageService._validate_remote_url(
            "https://192.168.1.10/product.jpg",
            allowed_hosts=None,
            resolve_host=False,
        )
    with pytest.raises(ProductImageValidationError):
        ProductImageService._validate_remote_url(
            "https://localhost/product.jpg",
            allowed_hosts=None,
            resolve_host=False,
        )
