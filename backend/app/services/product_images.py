from __future__ import annotations

import hashlib
import html
import ipaddress
import re
import socket
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from fastapi import UploadFile
from sqlmodel import Session

from app.core.settings import settings
from app.models.application_setting import ApplicationSetting
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
DUCKDUCKGO_SEARCH = "https://duckduckgo.com/"
DUCKDUCKGO_IMAGES = "https://duckduckgo.com/i.js"
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
        application = self._require_online_search()
        normalized = query.strip()
        if len(normalized) < 2:
            raise ProductImageValidationError("Bitte mindestens zwei Suchzeichen eingeben.")
        bounded_limit = min(max(limit, 1), 24)
        providers: list[
            Callable[[str, int], list[ProductImageSearchItemRead]]
        ] = []
        if application.product_image_source_duckduckgo_enabled:
            providers.append(self._search_duckduckgo)
        if application.product_image_source_wikimedia_enabled:
            providers.append(self._search_wikimedia)
        items: list[ProductImageSearchItemRead] = []
        errors: list[Exception] = []
        for provider in providers:
            try:
                items.extend(provider(normalized, bounded_limit))
            except (httpx.HTTPError, ValueError, ProductImageUnavailableError) as exc:
                errors.append(exc)
        relevant = [
            item
            for item in items
            if self._relevance_score(normalized, item.title, item.source_url) >= 12
        ]
        unique: dict[str, ProductImageSearchItemRead] = {}
        for item in relevant:
            unique.setdefault(item.image_url.split("?", 1)[0].casefold(), item)
        ranked = sorted(
            unique.values(),
            key=lambda item: (
                -self._relevance_score(normalized, item.title, item.source_url),
                item.title.casefold(),
            ),
        )
        if ranked or not errors:
            return ProductImageSearchRead(items=ranked[:bounded_limit], enabled=True)
        if errors:
            raise ProductImageUnavailableError(
                "Keine der aktivierten Online-Bildquellen ist erreichbar. "
                "Mögliche Ursachen sind DNS, TLS, Proxy, Firewall oder der externe Dienst."
            ) from errors[-1]
        return ProductImageSearchRead(items=[], enabled=True)

    def _search_duckduckgo(
        self,
        query: str,
        limit: int,
    ) -> list[ProductImageSearchItemRead]:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; DocOfHome/1.6.1; product image search)",
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
        }
        with httpx.Client(
            timeout=httpx.Timeout(12.0),
            follow_redirects=False,
            transport=self.transport,
            headers=headers,
        ) as client:
            token_response = client.get(
                DUCKDUCKGO_SEARCH,
                params={"q": query, "iax": "images", "ia": "images"},
            )
            token_response.raise_for_status()
            match = re.search(r"vqd=['\"]?([0-9-]+)", token_response.text)
            if match is None:
                return []
            response = client.get(
                DUCKDUCKGO_IMAGES,
                params={"q": query, "o": "json", "vqd": match.group(1), "f": ",,,", "p": "1"},
                headers={**headers, "Referer": str(token_response.request.url)},
            )
            response.raise_for_status()
            payload = response.json()
        rows = payload.get("results", []) if isinstance(payload, dict) else []
        if not isinstance(rows, list):
            return []
        scored: list[tuple[int, ProductImageSearchItemRead]] = []
        seen: set[str] = set()
        for row in rows:
            if not isinstance(row, dict):
                continue
            image_url = row.get("image")
            thumbnail_url = row.get("thumbnail") or image_url
            source_url = row.get("url") or image_url
            if not all(isinstance(value, str) for value in (image_url, thumbnail_url, source_url)):
                continue
            try:
                self._validate_remote_url(image_url, allowed_hosts=None, resolve_host=False)
                self._validate_remote_url(thumbnail_url, allowed_hosts=None, resolve_host=False)
                self._validate_remote_url(source_url, allowed_hosts=None, resolve_host=False)
            except ProductImageValidationError:
                continue
            canonical = image_url.split("?", 1)[0].casefold()
            if canonical in seen:
                continue
            seen.add(canonical)
            title = self._clean_title(str(row.get("title") or row.get("source") or "Produktbild"))
            item = ProductImageSearchItemRead(
                title=title,
                thumbnail_url=thumbnail_url,
                source_url=source_url,
                image_url=image_url,
                license_name=None,
                author=str(row.get("source") or "").strip()[:300] or None,
                provider="DuckDuckGo Images",
            )
            score = self._relevance_score(query, title, source_url)
            scored.append((score, item))
        scored.sort(key=lambda pair: (-pair[0], pair[1].title.casefold()))
        return [item for _, item in scored[:limit]]

    def _search_wikimedia(
        self,
        query: str,
        limit: int,
    ) -> list[ProductImageSearchItemRead]:
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": "6",
            "gsrlimit": str(limit),
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "iiurlwidth": "360",
            "format": "json",
            "formatversion": "2",
        }
        with httpx.Client(
            timeout=httpx.Timeout(12.0),
            follow_redirects=False,
            transport=self.transport,
            headers={"User-Agent": "DocOfHome product image search/1.6.1"},
        ) as client:
            response = client.get(WIKIMEDIA_API, params=params)
            response.raise_for_status()
            payload = response.json()
        pages = payload.get("query", {}).get("pages", []) if isinstance(payload, dict) else []
        if not isinstance(pages, list):
            return []
        items: list[tuple[int, ProductImageSearchItemRead]] = []
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
                image_url, thumbnail_url, source_url,
            )):
                continue
            try:
                self._validate_remote_url(image_url, allowed_hosts=ALLOWED_REMOTE_IMAGE_HOSTS)
                self._validate_remote_url(thumbnail_url, allowed_hosts=ALLOWED_REMOTE_IMAGE_HOSTS)
                self._validate_remote_url(source_url, allowed_hosts=ALLOWED_REMOTE_SOURCE_HOSTS)
            except ProductImageValidationError:
                continue
            metadata = info.get("extmetadata") if isinstance(info.get("extmetadata"), dict) else {}
            title = self._clean_title(str(page.get("title") or "Produktbild"))
            item = ProductImageSearchItemRead(
                title=title,
                thumbnail_url=thumbnail_url,
                source_url=source_url,
                image_url=image_url,
                license_name=self._metadata_value(metadata, "LicenseShortName"),
                author=self._metadata_value(metadata, "Artist"),
                provider="Wikimedia Commons",
            )
            items.append((self._relevance_score(query, title, source_url), item))
        items.sort(key=lambda pair: (-pair[0], pair[1].title.casefold()))
        return [item for _, item in items[:limit]]

    def import_online(
        self, image_url: str, *, source_url: str | None = None
    ) -> ProductImageUploadRead:
        self._require_online_search()
        self._validate_remote_url(image_url, allowed_hosts=None, resolve_host=True)
        if source_url is not None:
            self._validate_remote_url(source_url, allowed_hosts=None, resolve_host=True)
        try:
            with httpx.Client(
                timeout=httpx.Timeout(15.0),
                follow_redirects=False,
                transport=self.transport,
                headers={"User-Agent": "DocOfHome product image import/1.6.1"},
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
                "Der DocOfHome-Container konnte das gewählte Online-Bild nicht herunterladen."
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
    def _validate_remote_url(
        value: str,
        *,
        allowed_hosts: frozenset[str] | None,
        resolve_host: bool = False,
    ) -> None:
        parsed = urlparse(value)
        host = (parsed.hostname or "").casefold().rstrip(".")
        if (
            parsed.scheme != "https"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in (None, 443)
            or not host
            or host == "localhost"
            or host.endswith(".local")
            or (allowed_hosts is not None and host not in allowed_hosts)
        ):
            raise ProductImageValidationError(
                "Das Online-Bild stammt nicht von einer zulässigen öffentlichen HTTPS-Adresse."
            )
        try:
            literal = ipaddress.ip_address(host)
        except ValueError:
            literal = None
        if literal is not None and not literal.is_global:
            raise ProductImageValidationError(
                "Private oder lokale Bildadressen sind nicht zulässig."
            )
        if resolve_host and literal is None:
            try:
                addresses = {
                    ipaddress.ip_address(item[4][0])
                    for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
                }
            except (OSError, ValueError) as exc:
                raise ProductImageValidationError(
                    "Der Bildhost konnte nicht sicher aufgelöst werden."
                ) from exc
            if not addresses or any(not address.is_global for address in addresses):
                raise ProductImageValidationError(
                    "Private oder lokale Bildziele sind nicht zulässig."
                )

    @staticmethod
    def _relevance_score(query: str, title: str, source_url: str) -> int:
        def normalize(value: str) -> str:
            decomposed = unicodedata.normalize("NFKD", value.casefold())
            return " ".join(
                re.findall(
                    r"[a-z0-9]+",
                    "".join(
                        char
                        for char in decomposed
                        if not unicodedata.combining(char)
                    ),
                )
            )

        query_tokens = [token for token in normalize(query).split() if len(token) > 1]
        haystack = normalize(f"{title} {source_url}")
        score = sum(12 for token in query_tokens if token in haystack)
        if query_tokens and all(token in haystack for token in query_tokens):
            score += 35
        penalties = {
            "logo": 24,
            "icon": 20,
            "symbol": 16,
            "manual": 14,
            "datasheet": 14,
            "diagram": 12,
            "schematic": 12,
            "wiring": 10,
            "vector": 10,
        }
        for token, penalty in penalties.items():
            if token in haystack:
                score -= penalty
        return score

    def _require_online_search(self) -> ApplicationSetting:
        application = self.settings_repository.get_application()
        if application is None or not application.online_product_image_search_enabled:
            raise ProductImageSearchDisabledError(
                "Die Online-Produktbildsuche ist in den Einstellungen deaktiviert."
            )
        if not (
            application.product_image_source_duckduckgo_enabled
            or application.product_image_source_wikimedia_enabled
        ):
            raise ProductImageSearchDisabledError(
                "Für die Online-Produktbildsuche ist keine Quelle aktiviert."
            )
        return application

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
