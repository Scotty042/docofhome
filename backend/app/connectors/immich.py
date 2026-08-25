from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import ceil
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

import httpx

IMMICH_TIMEOUT_SECONDS = 10.0
MAX_THUMBNAIL_BYTES = 15_000_000
ALLOWED_THUMBNAIL_MEDIA_TYPES = {
    "image/avif",
    "image/jpeg",
    "image/png",
    "image/webp",
}


class ImmichConnectorError(RuntimeError):
    """Base error for secret-free Immich connector failures."""


class ImmichConnectorNotFoundError(ImmichConnectorError):
    """Raised when an Immich asset no longer exists."""


@dataclass(frozen=True, slots=True)
class ImmichImage:
    immich_asset_id: str
    original_file_name: str
    file_created_at: datetime | None
    width: int | None
    height: int | None
    is_favorite: bool


@dataclass(frozen=True, slots=True)
class ImmichImagePage:
    items: tuple[ImmichImage, ...]
    total: int
    page: int
    page_size: int
    pages: int


@dataclass(frozen=True, slots=True)
class ImmichAlbum:
    immich_album_id: str
    album_name: str
    asset_count: int
    thumbnail_asset_id: str | None
    start_date: datetime | None
    end_date: datetime | None


@dataclass(frozen=True, slots=True)
class ImmichThumbnail:
    content: bytes
    media_type: str


class ImmichConnector:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        normalized = base_url.rstrip("/")
        self.api_base = (
            normalized if urlparse(normalized).path.endswith("/api") else f"{normalized}/api"
        )
        self.api_key = api_key
        self.transport = transport

    def search_images(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        album_id: UUID | None = None,
        favorite_only: bool = False,
        taken_after: datetime | None = None,
        taken_before: datetime | None = None,
    ) -> ImmichImagePage:
        payload: dict[str, object] = {
            "page": page,
            "size": page_size,
            "order": "desc",
            "type": "IMAGE",
            "withDeleted": False,
            "withExif": False,
            "withPeople": False,
            "withStacked": True,
        }
        if search:
            payload["originalFileName"] = search
        if album_id:
            payload["albumIds"] = [str(album_id)]
        if favorite_only:
            payload["isFavorite"] = True
        if taken_after is not None:
            payload["takenAfter"] = taken_after.isoformat()
        if taken_before is not None:
            payload["takenBefore"] = taken_before.isoformat()
        response = self._request("POST", "/search/metadata", json=payload)
        body = self._json_object(response)
        assets = body.get("assets")
        if not isinstance(assets, dict):
            raise ImmichConnectorError("Immich liefert ein unerwartetes Suchergebnis.")
        raw_items = assets.get("items")
        if not isinstance(raw_items, list):
            raise ImmichConnectorError("Immich liefert keine gültige Bilderliste.")
        items = tuple(self._parse_image(item) for item in raw_items)
        raw_total = assets.get("total", assets.get("count", len(items)))
        if not isinstance(raw_total, int) or raw_total < 0:
            raise ImmichConnectorError("Immich liefert eine ungültige Trefferzahl.")
        return ImmichImagePage(
            items=items,
            total=raw_total,
            page=page,
            page_size=page_size,
            pages=ceil(raw_total / page_size) if raw_total else 0,
        )

    def list_albums(self) -> tuple[ImmichAlbum, ...]:
        response = self._request("GET", "/albums")
        albums = tuple(self._parse_album(item) for item in self._json_list(response))
        return tuple(sorted(albums, key=lambda item: item.album_name.casefold()))

    def get_image(self, immich_asset_id: UUID) -> ImmichImage:
        response = self._request("GET", f"/assets/{immich_asset_id}")
        return self._parse_image(self._json_object(response))

    def get_thumbnail(self, immich_asset_id: UUID) -> ImmichThumbnail:
        try:
            with self._client() as client:
                with client.stream(
                    "GET", f"{self.api_base}/assets/{immich_asset_id}/thumbnail"
                ) as response:
                    self._require_status(response)
                    media_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                    if media_type not in ALLOWED_THUMBNAIL_MEDIA_TYPES:
                        raise ImmichConnectorError(
                            "Immich liefert kein unterstütztes Vorschaubild."
                        )
                    raw_length = response.headers.get("content-length")
                    if raw_length and int(raw_length) > MAX_THUMBNAIL_BYTES:
                        raise ImmichConnectorError("Das Immich-Vorschaubild ist unerwartet groß.")
                    content = bytearray()
                    for chunk in response.iter_bytes():
                        content.extend(chunk)
                        if len(content) > MAX_THUMBNAIL_BYTES:
                            raise ImmichConnectorError(
                                "Das Immich-Vorschaubild ist unerwartet groß."
                            )
        except ValueError as exc:
            raise ImmichConnectorError("Immich liefert eine ungültige Vorschaubildgröße.") from exc
        except httpx.TimeoutException as exc:
            raise ImmichConnectorError("Zeitüberschreitung bei der Immich-Verbindung.") from exc
        except httpx.RequestError as exc:
            raise ImmichConnectorError("Immich ist nicht erreichbar.") from exc
        return ImmichThumbnail(content=bytes(content), media_type=media_type)

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            with self._client() as client:
                response = client.request(method, f"{self.api_base}{path}", **kwargs)
        except httpx.TimeoutException as exc:
            raise ImmichConnectorError("Zeitüberschreitung bei der Immich-Verbindung.") from exc
        except httpx.RequestError as exc:
            raise ImmichConnectorError("Immich ist nicht erreichbar.") from exc
        self._require_status(response)
        return response

    def _client(self) -> httpx.Client:
        return httpx.Client(
            timeout=httpx.Timeout(IMMICH_TIMEOUT_SECONDS),
            follow_redirects=False,
            transport=self.transport,
            headers={
                "x-api-key": self.api_key,
                "Accept": "application/json, image/avif, image/webp, image/jpeg, image/png",
                "User-Agent": "DocOfHome Immich connector",
            },
        )

    @staticmethod
    def _require_status(response: httpx.Response) -> None:
        if response.status_code == 404:
            raise ImmichConnectorNotFoundError("Der Immich-Datensatz wurde nicht gefunden.")
        if response.status_code in {401, 403}:
            raise ImmichConnectorError(
                "Immich lehnt den API-Key ab oder die erforderliche Berechtigung fehlt."
            )
        if 300 <= response.status_code < 400:
            raise ImmichConnectorError("Immich antwortet mit einer nicht erlaubten Umleitung.")
        if response.status_code != 200:
            raise ImmichConnectorError(
                f"Immich antwortet unerwartet mit HTTP {response.status_code}."
            )

    @staticmethod
    def _json_object(response: httpx.Response) -> dict[str, object]:
        try:
            body = response.json()
        except ValueError as exc:
            raise ImmichConnectorError("Immich liefert keine gültige JSON-Antwort.") from exc
        if not isinstance(body, dict):
            raise ImmichConnectorError("Immich liefert ein unerwartetes Antwortformat.")
        return body

    @staticmethod
    def _json_list(response: httpx.Response) -> list[object]:
        try:
            body = response.json()
        except ValueError as exc:
            raise ImmichConnectorError("Immich liefert keine gültige JSON-Antwort.") from exc
        if not isinstance(body, list):
            raise ImmichConnectorError("Immich liefert keine gültige Albumliste.")
        return body

    @staticmethod
    def _parse_datetime(raw: object) -> datetime | None:
        if not raw:
            return None
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            return None

    @classmethod
    def _parse_album(cls, raw: object) -> ImmichAlbum:
        if not isinstance(raw, dict):
            raise ImmichConnectorError("Immich liefert einen ungültigen Albumeintrag.")
        try:
            album_id = str(UUID(str(raw["id"])))
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ImmichConnectorError("Immich liefert eine ungültige Album-ID.") from exc
        album_name = raw.get("albumName")
        if not isinstance(album_name, str) or not album_name.strip():
            album_name = "Unbenanntes Album"
        asset_count = raw.get("assetCount")
        if not isinstance(asset_count, int) or asset_count < 0:
            raise ImmichConnectorError("Immich liefert eine ungültige Albumgröße.")
        raw_thumbnail = raw.get("albumThumbnailAssetId")
        try:
            thumbnail_asset_id = str(UUID(str(raw_thumbnail))) if raw_thumbnail else None
        except (TypeError, ValueError, AttributeError) as exc:
            raise ImmichConnectorError("Immich liefert eine ungültige Albumvorschau.") from exc
        return ImmichAlbum(
            immich_album_id=album_id,
            album_name=album_name.strip()[:255],
            asset_count=asset_count,
            thumbnail_asset_id=thumbnail_asset_id,
            start_date=cls._parse_datetime(raw.get("startDate")),
            end_date=cls._parse_datetime(raw.get("endDate")),
        )

    @classmethod
    def _parse_image(cls, raw: object) -> ImmichImage:
        if not isinstance(raw, dict):
            raise ImmichConnectorError("Immich liefert einen ungültigen Bildeintrag.")
        try:
            asset_id = str(UUID(str(raw["id"])))
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ImmichConnectorError("Immich liefert eine ungültige Bild-ID.") from exc
        asset_type = raw.get("type")
        if asset_type != "IMAGE":
            raise ImmichConnectorError("Der Immich-Datensatz ist kein Bild.")
        file_name = raw.get("originalFileName")
        if not isinstance(file_name, str) or not file_name.strip():
            file_name = "Immich-Foto"
        width = raw.get("width") if isinstance(raw.get("width"), int) else None
        height = raw.get("height") if isinstance(raw.get("height"), int) else None
        return ImmichImage(
            immich_asset_id=asset_id,
            original_file_name=file_name.strip()[:255],
            file_created_at=cls._parse_datetime(raw.get("fileCreatedAt")),
            width=width if width is None or width > 0 else None,
            height=height if height is None or height > 0 else None,
            is_favorite=raw.get("isFavorite") is True,
        )
