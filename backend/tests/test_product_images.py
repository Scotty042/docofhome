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
