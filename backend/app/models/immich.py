from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field, SQLModel


class ImmichAssetLink(SQLModel, table=True):
    __tablename__ = "immich_asset_links"
    __table_args__ = (
        CheckConstraint(
            "length(trim(immich_asset_id)) = 36",
            name="ck_immich_asset_links_external_id",
        ),
        CheckConstraint(
            "width IS NULL OR width > 0",
            name="ck_immich_asset_links_width",
        ),
        CheckConstraint(
            "height IS NULL OR height > 0",
            name="ck_immich_asset_links_height",
        ),
        UniqueConstraint(
            "asset_id",
            "immich_asset_id",
            name="uq_immich_asset_links_asset_external",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    asset_id: UUID = Field(foreign_key="assets.id", index=True)
    immich_asset_id: str = Field(index=True, max_length=36)
    original_file_name: str = Field(max_length=255)
    file_created_at: datetime | None = None
    width: int | None = None
    height: int | None = None
    is_favorite: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
