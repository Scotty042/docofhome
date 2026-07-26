from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class DocumentEntryType(StrEnum):
    FILE = "file"
    FOLDER = "folder"


class DocumentEntry(BaseModel):
    name: str
    path: str
    entry_type: DocumentEntryType
    size_bytes: int = Field(ge=0)
    modified_at: datetime | None = None
    content_type: str | None = None
    etag: str | None = None


class DocumentListRead(BaseModel):
    path: str
    root_path: str
    root_exists: bool
    items: list[DocumentEntry]


class DocumentFolderCreate(BaseModel):
    parent_path: str = Field(default="", max_length=1000)
    name: str = Field(min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Folder name must not be empty")
        return normalized


class DocumentMoveRequest(BaseModel):
    source_path: str = Field(min_length=1, max_length=1000)
    target_parent_path: str = Field(default="", max_length=1000)
    name: str = Field(min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Target name must not be empty")
        return normalized


class DocumentMutationRead(BaseModel):
    item: DocumentEntry
    created: bool = False
    overwritten: bool = False


class DocumentDownload(BaseModel):
    filename: str
    content: bytes
    content_type: str
    etag: str | None = None
