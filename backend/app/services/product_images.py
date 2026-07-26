from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from fastapi import UploadFile
from sqlmodel import Session

from app.core.settings import settings
from app.repositories.settings import SettingsRepository
from app.schemas.asset_engine import (
    ProductImageSearchItemRead,
    ProductImageSearchRead,
    ProductImageSource,
    ProductImageUploadRead,
)

MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
ALLOWED_REMOTE_IMAGE_HOSTS = frozenset({"upload.wikimedia.org"})
ALLOWED_REMOTE_SOURCE_HOSTS = frozenset({"commons.wikimedia.org"})


class ProductImageError(RuntimeError):
    """Base error for product image workflows."""


class ProductImageValidationError(ProductImageError):
    """Raised when an uploaded or remote file is not an accepted image."""


class ProductImageSearchDisabledError(ProductImageError):
    """Raised when the optional online image lookup is disabled."""


class ProductImageUnavailableError(ProductImageError):
    """Raised when an external image provider is unavailable."""


@dataclass(slots=True)
class StoredProductImage:
    path: Path
    public_url: str
    reference: str


class ProductImageService:
    def __init__(
        self,
        session: Session,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.session = session
        self.settings_repository = SettingsRepository(session)
        self.transport = transport

    @property
    def upload_dir(self) -> Path:
        return settings.data_dir / "uploads" / "product-images"

    async def upload(self, upload: UploadFile) -> ProductImageUploadRead:
        content_type = (upload.content_type or "").lower()
        extension = ALLOWED_IMAGE_TYPES.get(content_type)
        if extension is None:
            raise ProductImageValidationError(
                "Unterstützt werden JPEG-, PNG-, WebP- und GIF-Bilder."
            )
        content = await upload.read(MAX_IMAGE_BYTES + 1)
        if not content:
            raise ProductImageValidationError("Die hochgeladene Bilddatei ist leer.")
        if len(content) > MAX_IMAGE_BYTES:
            raise ProductImageValidationError("Das Produktbild darf höchstens 10 MB groß sein.")
        self._validate_image_signature(content, content_type)
        stored = self._store(content, extension)
        return ProductImageUploadRead(
            image_url=stored.public_url,
            image_source=ProductImageSource.UPLOAD,
            image_reference=stored.reference,
        )

    def resolve(self, reference: str) -> Path:
        safe_name = Path(reference).name
        if safe_name != reference or not safe_name:
            raise ProductImageValidationError("Ungültiger Produktbildpfad.")
        candidate = (self.upload_dir / safe_name).resolve()
        root = self.upload_dir.resolve()
        if root not in candidate.parents or not candidate.is_file():
            raise ProductImageValidationError("Produktbild wurde nicht gefunden.")
        return candidate

    def search_online(self, query: str, *, limit: int = 12) -> ProductImageSearchRead:
        self._require_online_search()
        normalized = query.strip()
        if len(normalized) < 2:
            raise ProductImageValidationError("Bitte mindestens zwei Suchzeichen eingeben.")
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": normalized,
            "gsrnamespace": "6",
            "gsrlimit": str(min(max(limit, 1), 24)),
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "iiurlwidth": "360",
            "format": "json",
            "formatversion": "2",
        }
        try:
            with httpx.Client(
                timeout=httpx.Timeout(12.0),
                follow_redirects=False,
                transport=self.transport,
                headers={"User-Agent": "DocOfHome product image search/1.4.0"},
            ) as client:
                response = client.get(WIKIMEDIA_API, params=params)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProductImageUnavailableError(
                "Der DocOfHome-Container konnte Wikimedia nicht erreichen. "
                "Mögliche Ursachen sind DNS, TLS, Proxy, Firewall oder der externe Dienst."
            ) from exc

        pages = payload.get("query", {}).get("pages", []) if isinstance(payload, dict) else []
        items: list[ProductImageSearchItemRead] = []
        if not isinstance(pages, list):
            pages = []
        for page in pages:
            if not isinstance(page, dict):
                continue
            info_rows = page.get("imageinfo")
            if (
                not isinstance(info_rows, list)
                or not info_rows
                or not isinstance(info_rows[0], dict)
            ):
                continue
            info = info_rows[0]
            image_url = info.get("url")
            thumbnail_url = info.get("thumburl") or image_url
            source_url = info.get("descriptionurl") or image_url
            if not all(isinstance(value, str) and value.startswith("https://") for value in (
                image_url,
                thumbnail_url,
                source_url,
            )):
                continue
            try:
                self._validate_remote_url(
                    image_url, allowed_hosts=ALLOWED_REMOTE_IMAGE_HOSTS
                )
                self._validate_remote_url(
                    thumbnail_url, allowed_hosts=ALLOWED_REMOTE_IMAGE_HOSTS
                )
                self._validate_remote_url(
                    source_url, allowed_hosts=ALLOWED_REMOTE_SOURCE_HOSTS
                )
            except ProductImageValidationError:
                continue
            metadata = info.get("extmetadata") if isinstance(info.get("extmetadata"), dict) else {}
            items.append(
                ProductImageSearchItemRead(
                    title=self._clean_title(str(page.get("title") or "Produktbild")),
                    thumbnail_url=thumbnail_url,
                    source_url=source_url,
                    image_url=image_url,
                    license_name=self._metadata_value(metadata, "LicenseShortName"),
                    author=self._metadata_value(metadata, "Artist"),
                )
            )
        return ProductImageSearchRead(items=items, enabled=True)

    def import_online(
        self, image_url: str, *, source_url: str | None = None
    ) -> ProductImageUploadRead:
        self._require_online_search()
        self._validate_remote_url(image_url, allowed_hosts=ALLOWED_REMOTE_IMAGE_HOSTS)
        if source_url is not None:
            self._validate_remote_url(source_url, allowed_hosts=ALLOWED_REMOTE_SOURCE_HOSTS)
        try:
            with httpx.Client(
                timeout=httpx.Timeout(15.0),
                follow_redirects=False,
                transport=self.transport,
                headers={"User-Agent": "DocOfHome product image import/1.4.0"},
            ) as client:
                with client.stream("GET", image_url) as response:
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                    extension = ALLOWED_IMAGE_TYPES.get(content_type)
                    if extension is None:
                        raise ProductImageValidationError(
                            "Der gewählte Online-Treffer ist kein unterstütztes Bildformat."
                        )
                    chunks: list[bytes] = []
                    size = 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > MAX_IMAGE_BYTES:
                            raise ProductImageValidationError(
                                "Das Online-Produktbild ist größer als 10 MB."
                            )
                        chunks.append(chunk)
        except ProductImageValidationError:
            raise
        except httpx.HTTPError as exc:
            raise ProductImageUnavailableError(
                "Der DocOfHome-Container konnte das gewählte Wikimedia-Bild nicht "
                "herunterladen."
            ) from exc
        content = b"".join(chunks)
        if not content:
            raise ProductImageValidationError("Das Online-Produktbild ist leer.")
        self._validate_image_signature(content, content_type)
        stored = self._store(content, extension)
        return ProductImageUploadRead(
            image_url=stored.public_url,
            image_source=ProductImageSource.ONLINE,
            image_reference=source_url or image_url,
        )

    @staticmethod
    def _validate_image_signature(content: bytes, content_type: str) -> None:
        signatures = {
            "image/jpeg": content.startswith(b"\xff\xd8\xff"),
            "image/png": content.startswith(b"\x89PNG\r\n\x1a\n"),
            "image/gif": content.startswith((b"GIF87a", b"GIF89a")),
            "image/webp": len(content) >= 12
            and content.startswith(b"RIFF")
            and content[8:12] == b"WEBP",
        }
        if not signatures.get(content_type, False):
            raise ProductImageValidationError(
                "Die Datei entspricht nicht dem angegebenen Bildformat."
            )

    @staticmethod
    def _validate_remote_url(value: str, *, allowed_hosts: frozenset[str]) -> None:
        parsed = urlparse(value)
        host = (parsed.hostname or "").casefold()
        if (
            parsed.scheme != "https"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in (None, 443)
            or host not in allowed_hosts
        ):
            raise ProductImageValidationError(
                "Das Online-Bild stammt nicht vom freigegebenen Bildanbieter."
            )

    def _require_online_search(self) -> None:
        application = self.settings_repository.get_application()
        if application is None or not application.online_product_image_search_enabled:
            raise ProductImageSearchDisabledError(
                "Die Online-Produktbildsuche ist in den Einstellungen deaktiviert."
            )

    def _store(self, content: bytes, extension: str) -> StoredProductImage:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(content).hexdigest()[:16]
        reference = f"{digest}-{uuid4().hex[:12]}{extension}"
        path = self.upload_dir / reference
        path.write_bytes(content)
        return StoredProductImage(
            path=path,
            public_url=f"/api/v1/products/images/{reference}",
            reference=reference,
        )

    @staticmethod
    def _metadata_value(metadata: dict[str, Any], key: str) -> str | None:
        entry = metadata.get(key)
        if not isinstance(entry, dict):
            return None
        value = entry.get("value")
        if not isinstance(value, str):
            return None
        cleaned = re.sub(r"<[^>]+>", " ", html.unescape(value))
        cleaned = " ".join(cleaned.split())
        return cleaned[:300] or None

    @staticmethod
    def _clean_title(value: str) -> str:
        title = value.removeprefix("File:")
        return title.rsplit(".", 1)[0].replace("_", " ")[:200]
