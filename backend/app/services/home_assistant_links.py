from datetime import UTC, datetime
from uuid import UUID

from sqlmodel import Session, col, select

from app.models.asset_engine import Asset
from app.models.home_assistant import HomeAssistantAssetLink
from app.schemas.home_assistant import (
    HomeAssistantAssetBindingsWrite,
    HomeAssistantAssetLinkListRead,
    HomeAssistantAssetLinkRead,
    HomeAssistantEntityRole,
    HomeAssistantObjectType,
)


class HomeAssistantLinkError(RuntimeError):
    """Base error for Home Assistant-to-asset links."""


class HomeAssistantLinkNotFoundError(HomeAssistantLinkError):
    """Raised when a requested link does not exist."""


class HomeAssistantLinkAssetError(HomeAssistantLinkError):
    """Raised when a link target is missing or archived."""


class HomeAssistantLinkConflictError(HomeAssistantLinkError):
    """Raised when a Home Assistant object already belongs to another asset."""


class HomeAssistantLinkService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_links(
        self,
        *,
        object_type: HomeAssistantObjectType | None = None,
        asset_id: UUID | None = None,
    ) -> HomeAssistantAssetLinkListRead:
        statement = select(HomeAssistantAssetLink)
        if object_type is not None:
            statement = statement.where(HomeAssistantAssetLink.object_type == object_type.value)
        if asset_id is not None:
            statement = statement.where(HomeAssistantAssetLink.asset_id == asset_id)
        statement = statement.order_by(
            col(HomeAssistantAssetLink.object_type),
            col(HomeAssistantAssetLink.role),
            col(HomeAssistantAssetLink.external_id),
        )
        links = list(self.session.exec(statement).all())
        return HomeAssistantAssetLinkListRead(items=[self._to_read(link) for link in links])

    def upsert(
        self,
        *,
        object_type: HomeAssistantObjectType,
        external_id: str,
        asset_id: UUID,
        role: HomeAssistantEntityRole = HomeAssistantEntityRole.ADDITIONAL,
    ) -> HomeAssistantAssetLinkRead:
        normalized_id = self._normalize_external_id(external_id)
        asset = self._active_asset(asset_id)
        effective_role = (
            role
            if object_type == HomeAssistantObjectType.ENTITY
            else HomeAssistantEntityRole.ADDITIONAL
        )
        if effective_role == HomeAssistantEntityRole.PRIMARY_LIVE:
            self._remove_other_primary(asset.id, excluding_external_id=normalized_id)

        statement = select(HomeAssistantAssetLink).where(
            HomeAssistantAssetLink.object_type == object_type.value,
            HomeAssistantAssetLink.external_id == normalized_id,
        )
        link = self.session.exec(statement).one_or_none()
        now = datetime.now(UTC)
        if link is None:
            link = HomeAssistantAssetLink(
                object_type=object_type.value,
                external_id=normalized_id,
                asset_id=asset.id,
                role=effective_role.value,
                created_at=now,
                updated_at=now,
            )
            self.session.add(link)
        else:
            link.asset_id = asset.id
            link.role = effective_role.value
            link.updated_at = now
            self.session.add(link)
        self.session.commit()
        self.session.refresh(link)
        return self._to_read(link, asset=asset)

    def replace_asset_bindings(
        self,
        asset_id: UUID,
        payload: HomeAssistantAssetBindingsWrite,
    ) -> HomeAssistantAssetLinkListRead:
        asset = self._active_asset(asset_id)
        desired: dict[tuple[str, str], HomeAssistantEntityRole] = {
            (HomeAssistantObjectType.DEVICE.value, self._normalize_external_id(device_id)):
                HomeAssistantEntityRole.ADDITIONAL
            for device_id in payload.device_ids
        }
        desired.update(
            {
                (
                    HomeAssistantObjectType.ENTITY.value,
                    self._normalize_external_id(item.external_id),
                ):
                    item.role
                for item in payload.entities
            }
        )

        if desired:
            object_ids = [external_id for _, external_id in desired]
            existing_external = list(
                self.session.exec(
                    select(HomeAssistantAssetLink).where(
                        col(HomeAssistantAssetLink.external_id).in_(object_ids)
                    )
                ).all()
            )
            conflicts = [
                link
                for link in existing_external
                if (link.object_type, link.external_id) in desired and link.asset_id != asset.id
            ]
            if conflicts:
                first = conflicts[0]
                linked_asset = self.session.get(Asset, first.asset_id)
                target = (
                    f"{linked_asset.jarvis_code} · {linked_asset.name}"
                    if linked_asset is not None
                    else str(first.asset_id)
                )
                raise HomeAssistantLinkConflictError(
                    f"{first.external_id} ist bereits dem Asset {target} zugeordnet. "
                    "Trenne diese Zuordnung zuerst bewusst."
                )

        current = list(
            self.session.exec(
                select(HomeAssistantAssetLink).where(HomeAssistantAssetLink.asset_id == asset.id)
            ).all()
        )
        current_by_key = {(link.object_type, link.external_id): link for link in current}
        now = datetime.now(UTC)
        for key, link in current_by_key.items():
            if key not in desired:
                self.session.delete(link)
        for (object_type, external_id), role in desired.items():
            link = current_by_key.get((object_type, external_id))
            if link is None:
                link = HomeAssistantAssetLink(
                    object_type=object_type,
                    external_id=external_id,
                    asset_id=asset.id,
                    role=role.value,
                    created_at=now,
                    updated_at=now,
                )
            else:
                link.role = role.value
                link.updated_at = now
            self.session.add(link)
        self.session.commit()
        return self.list_links(asset_id=asset.id)

    def delete(
        self,
        *,
        object_type: HomeAssistantObjectType,
        external_id: str,
    ) -> None:
        normalized_id = self._normalize_external_id(external_id)
        statement = select(HomeAssistantAssetLink).where(
            HomeAssistantAssetLink.object_type == object_type.value,
            HomeAssistantAssetLink.external_id == normalized_id,
        )
        link = self.session.exec(statement).one_or_none()
        if link is None:
            raise HomeAssistantLinkNotFoundError(
                "Für dieses Home-Assistant-Objekt besteht keine Asset-Zuordnung."
            )
        self.session.delete(link)
        self.session.commit()

    def _active_asset(self, asset_id: UUID) -> Asset:
        asset = self.session.get(Asset, asset_id)
        if asset is None:
            raise HomeAssistantLinkAssetError("Das ausgewählte Asset wurde nicht gefunden.")
        if asset.deleted_at is not None:
            raise HomeAssistantLinkAssetError(
                "Ein archiviertes Asset kann nicht neu zugeordnet werden."
            )
        return asset

    def _remove_other_primary(self, asset_id: UUID, *, excluding_external_id: str) -> None:
        statement = select(HomeAssistantAssetLink).where(
            HomeAssistantAssetLink.asset_id == asset_id,
            HomeAssistantAssetLink.object_type == HomeAssistantObjectType.ENTITY.value,
            HomeAssistantAssetLink.role == HomeAssistantEntityRole.PRIMARY_LIVE.value,
            HomeAssistantAssetLink.external_id != excluding_external_id,
        )
        for link in self.session.exec(statement).all():
            link.role = HomeAssistantEntityRole.ADDITIONAL.value
            link.updated_at = datetime.now(UTC)
            self.session.add(link)

    def _to_read(
        self,
        link: HomeAssistantAssetLink,
        *,
        asset: Asset | None = None,
    ) -> HomeAssistantAssetLinkRead:
        linked_asset = asset or self.session.get(Asset, link.asset_id)
        if linked_asset is None:
            raise HomeAssistantLinkAssetError(
                "Die gespeicherte Zuordnung verweist auf ein fehlendes Asset."
            )
        return HomeAssistantAssetLinkRead(
            id=link.id,
            object_type=HomeAssistantObjectType(link.object_type),
            external_id=link.external_id,
            asset_id=linked_asset.id,
            role=HomeAssistantEntityRole(link.role),
            asset_name=linked_asset.name,
            asset_code=linked_asset.jarvis_code,
            asset_archived=linked_asset.deleted_at is not None,
            created_at=link.created_at,
            updated_at=link.updated_at,
        )

    @staticmethod
    def _normalize_external_id(external_id: str) -> str:
        normalized = external_id.strip()
        if not normalized:
            raise HomeAssistantLinkError("Die Home-Assistant-Objekt-ID darf nicht leer sein.")
        if len(normalized) > 255:
            raise HomeAssistantLinkError("Die Home-Assistant-Objekt-ID ist zu lang.")
        return normalized
