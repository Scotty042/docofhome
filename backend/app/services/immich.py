from __future__ import annotations

from datetime import datetime
from uuid import UUID

import httpx
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.connectors.immich import (
    ImmichAlbum,
    ImmichConnector,
    ImmichConnectorError,
    ImmichConnectorNotFoundError,
    ImmichImage,
    ImmichThumbnail,
)
from app.models.asset_engine import Asset
from app.models.immich import ImmichAssetLink
from app.repositories.immich import ImmichLinkRepository
from app.repositories.settings import SettingsRepository
from app.schemas.immich import (
    ImmichAlbumListRead,
    ImmichAlbumRead,
    ImmichImagePageRead,
    ImmichImageRead,
    ImmichLinkListRead,
    ImmichLinkRead,
    ImmichLinkWrite,
)


class ImmichConfigurationError(RuntimeError):
    """Raised when the optional Immich integration is not ready."""


class ImmichUnavailableError(RuntimeError):
    """Raised when a configured Immich service cannot satisfy a read."""


class ImmichImageNotFoundError(RuntimeError):
    """Raised when a requested external image no longer exists."""


class ImmichLinkNotFoundError(RuntimeError):
    """Raised when a local Immich link does not exist."""


class ImmichLinkConflictError(RuntimeError):
    """Raised when an Immich link violates a local domain rule."""


class ImmichFilterConflictError(RuntimeError):
    """Raised when a read-only gallery filter is internally inconsistent."""


class ImmichService:
    def __init__(
        self,
        session: Session,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.session = session
        self.settings_repository = SettingsRepository(session)
        self.link_repository = ImmichLinkRepository(session)
        self.transport = transport

    def browse_images(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        album_id: UUID | None = None,
        favorite_only: bool = False,
        taken_after: datetime | None = None,
        taken_before: datetime | None = None,
    ) -> ImmichImagePageRead:
        if taken_after is not None and taken_before is not None and taken_after >= taken_before:
            raise ImmichFilterConflictError("Das Startdatum muss vor dem Enddatum liegen.")
        try:
            result = self._connector().search_images(
                page=page,
                page_size=page_size,
                search=search.strip() if search and search.strip() else None,
                album_id=album_id,
                favorite_only=favorite_only,
                taken_after=taken_after,
                taken_before=taken_before,
            )
        except ImmichConnectorError as exc:
            raise self._translate_connector_error(exc) from exc
        return ImmichImagePageRead(
            items=[self._image_read(item) for item in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            pages=result.pages,
        )

    def list_albums(self) -> ImmichAlbumListRead:
        try:
            albums = self._connector().list_albums()
        except ImmichConnectorError as exc:
            raise self._translate_connector_error(exc) from exc
        return ImmichAlbumListRead(items=[self._album_read(album) for album in albums])

    def thumbnail(self, immich_asset_id: UUID) -> ImmichThumbnail:
        try:
            return self._connector().get_thumbnail(immich_asset_id)
        except ImmichConnectorError as exc:
            raise self._translate_connector_error(exc) from exc

    def list_links(self, *, asset_id: UUID) -> ImmichLinkListRead:
        if self.session.get(Asset, asset_id) is None:
            raise ImmichLinkNotFoundError("Das DocOfHome-Asset wurde nicht gefunden.")
        return ImmichLinkListRead(
            items=[self._link_read(item) for item in self.link_repository.list_for_asset(asset_id)]
        )

    def create_link(self, payload: ImmichLinkWrite) -> ImmichLinkRead:
        asset = self.session.get(Asset, payload.asset_id)
        if asset is None:
            raise ImmichLinkNotFoundError("Das DocOfHome-Asset wurde nicht gefunden.")
        if asset.deleted_at is not None:
            raise ImmichLinkConflictError(
                "Archivierte DocOfHome-Assets können keine neuen Fotos erhalten."
            )
        external_id = str(payload.immich_asset_id)
        if (
            self.link_repository.find(asset_id=payload.asset_id, immich_asset_id=external_id)
            is not None
        ):
            raise ImmichLinkConflictError("Dieses Immich-Foto ist bereits verknüpft.")
        try:
            image = self._connector().get_image(payload.immich_asset_id)
        except ImmichConnectorError as exc:
            raise self._translate_connector_error(exc) from exc
        link = ImmichAssetLink(
            asset_id=payload.asset_id,
            immich_asset_id=image.immich_asset_id,
            original_file_name=image.original_file_name,
            file_created_at=image.file_created_at,
            width=image.width,
            height=image.height,
            is_favorite=image.is_favorite,
        )
        try:
            self.link_repository.add(link)
            self.session.commit()
            self.session.refresh(link)
        except IntegrityError as exc:
            self.session.rollback()
            raise ImmichLinkConflictError("Dieses Immich-Foto ist bereits verknüpft.") from exc
        return self._link_read(link)

    def delete_link(self, link_id: UUID) -> None:
        link = self.link_repository.get(link_id)
        if link is None:
            raise ImmichLinkNotFoundError("Die Immich-Verknüpfung wurde nicht gefunden.")
        self.link_repository.delete(link)
        self.session.commit()

    def _connector(self) -> ImmichConnector:
        setting = self.settings_repository.get_integration("immich")
        if setting is None or not setting.enabled:
            raise ImmichConfigurationError("Die Immich-Integration ist deaktiviert.")
        if not setting.base_url or not setting.secret:
            raise ImmichConfigurationError(
                "Immich-URL oder API-Key sind nicht vollständig konfiguriert."
            )
        return ImmichConnector(
            base_url=setting.base_url,
            api_key=setting.secret,
            transport=self.transport,
        )

    @staticmethod
    def _translate_connector_error(exc: ImmichConnectorError) -> RuntimeError:
        if isinstance(exc, ImmichConnectorNotFoundError):
            return ImmichImageNotFoundError(str(exc))
        return ImmichUnavailableError(str(exc))

    @staticmethod
    def _thumbnail_url(immich_asset_id: str) -> str:
        return f"/api/v1/immich/assets/{immich_asset_id}/thumbnail"

    @classmethod
    def _album_read(cls, album: ImmichAlbum) -> ImmichAlbumRead:
        thumbnail_url = (
            cls._thumbnail_url(album.thumbnail_asset_id)
            if album.thumbnail_asset_id is not None
            else None
        )
        return ImmichAlbumRead(
            immich_album_id=UUID(album.immich_album_id),
            album_name=album.album_name,
            asset_count=album.asset_count,
            thumbnail_asset_id=(
                UUID(album.thumbnail_asset_id) if album.thumbnail_asset_id is not None else None
            ),
            thumbnail_url=thumbnail_url,
            start_date=album.start_date,
            end_date=album.end_date,
        )

    @classmethod
    def _image_read(cls, image: ImmichImage) -> ImmichImageRead:
        return ImmichImageRead(
            immich_asset_id=UUID(image.immich_asset_id),
            original_file_name=image.original_file_name,
            file_created_at=image.file_created_at,
            width=image.width,
            height=image.height,
            is_favorite=image.is_favorite,
            thumbnail_url=cls._thumbnail_url(image.immich_asset_id),
        )

    def _link_read(self, link: ImmichAssetLink) -> ImmichLinkRead:
        setting = self.settings_repository.get_integration("immich")
        configured_url = setting.browser_url or setting.base_url if setting else None
        browser_url = configured_url.rstrip("/") if configured_url else None
        return ImmichLinkRead(
            id=link.id,
            asset_id=link.asset_id,
            immich_asset_id=UUID(link.immich_asset_id),
            original_file_name=link.original_file_name,
            file_created_at=link.file_created_at,
            width=link.width,
            height=link.height,
            is_favorite=link.is_favorite,
            thumbnail_url=self._thumbnail_url(link.immich_asset_id),
            source_url=f"{browser_url}/photos/{link.immich_asset_id}" if browser_url else None,
            created_at=link.created_at,
            updated_at=link.updated_at,
        )
