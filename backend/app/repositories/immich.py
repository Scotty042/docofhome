from uuid import UUID

from sqlmodel import Session, col, select

from app.models.immich import ImmichAssetLink


class ImmichLinkRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_asset(self, asset_id: UUID) -> list[ImmichAssetLink]:
        statement = (
            select(ImmichAssetLink)
            .where(ImmichAssetLink.asset_id == asset_id)
            .order_by(
                col(ImmichAssetLink.file_created_at).desc(),
                col(ImmichAssetLink.created_at).desc(),
            )
        )
        return list(self.session.exec(statement).all())

    def get(self, link_id: UUID) -> ImmichAssetLink | None:
        return self.session.get(ImmichAssetLink, link_id)

    def find(self, *, asset_id: UUID, immich_asset_id: str) -> ImmichAssetLink | None:
        statement = select(ImmichAssetLink).where(
            ImmichAssetLink.asset_id == asset_id,
            ImmichAssetLink.immich_asset_id == immich_asset_id,
        )
        return self.session.exec(statement).one_or_none()

    def add(self, link: ImmichAssetLink) -> None:
        self.session.add(link)

    def delete(self, link: ImmichAssetLink) -> None:
        self.session.delete(link)
