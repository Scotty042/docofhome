from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class KnowledgeTargetType(StrEnum):
    ASSET = "asset"
    LOCATION = "location"
    DISTRIBUTION = "distribution"
    PROTECTIVE_DEVICE = "protective_device"
    CIRCUIT = "circuit"


class WikiPageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(default="", max_length=200000)
    parent_id: UUID | None = None
    sort_order: int = Field(default=0, ge=0, le=100000)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Der Seitentitel darf nicht leer sein")
        return normalized


class WikiPageUpdate(WikiPageCreate):
    pass


class WikiPageRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    parent_id: UUID | None
    title: str
    slug: str
    content: str
    path: str
    depth: int = Field(ge=0)
    sort_order: int = Field(ge=0)
    archived: bool
    created_at: datetime
    updated_at: datetime


class NoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_type: KnowledgeTargetType
    target_id: UUID
    content: str = Field(min_length=1, max_length=20000)

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Die Notiz darf nicht leer sein")
        return normalized


class NoteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=20000)

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Die Notiz darf nicht leer sein")
        return normalized


class NoteRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    target_type: KnowledgeTargetType
    target_id: UUID
    content: str
    created_at: datetime
    updated_at: datetime
