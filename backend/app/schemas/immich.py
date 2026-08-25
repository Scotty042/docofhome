from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ImmichImageRead(BaseModel):
    immich_asset_id: UUID
    original_file_name: str
    file_created_at: datetime | None = None
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    is_favorite: bool
    thumbnail_url: str


class ImmichImagePageRead(BaseModel):
    items: list[ImmichImageRead]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    pages: int = Field(ge=0)


class ImmichAlbumRead(BaseModel):
    immich_album_id: UUID
    album_name: str
    asset_count: int = Field(ge=0)
    thumbnail_asset_id: UUID | None = None
    thumbnail_url: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class ImmichAlbumListRead(BaseModel):
    items: list[ImmichAlbumRead]


class ImmichLinkWrite(BaseModel):
    asset_id: UUID
    immich_asset_id: UUID


class ImmichLinkRead(BaseModel):
    id: UUID
    asset_id: UUID
    immich_asset_id: UUID
    original_file_name: str
    file_created_at: datetime | None = None
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    is_favorite: bool
    thumbnail_url: str
    created_at: datetime
    updated_at: datetime


class ImmichLinkListRead(BaseModel):
    items: list[ImmichLinkRead]
