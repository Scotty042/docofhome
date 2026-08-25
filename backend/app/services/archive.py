from uuid import UUID

from sqlmodel import Session

from app.schemas.asset_engine import AssetRead
from app.services.asset_engine import AssetService, ResourceNotFoundError


class ArchivedAssetService(AssetService):
    """Read soft-deleted Assets without enabling normal mutation workflows."""

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_read(self, record_id: UUID) -> AssetRead:
        asset = self.asset_repository.get(record_id, include_deleted=True)
        if asset is None or asset.deleted_at is None:
            raise ResourceNotFoundError
        return self._to_read(asset)
