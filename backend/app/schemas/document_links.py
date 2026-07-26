from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentTargetType(StrEnum):
    ASSET = "asset"
    LOCATION = "location"
    DISTRIBUTION = "distribution"
    PROTECTIVE_DEVICE = "protective_device"
    CIRCUIT = "circuit"


class DocumentLinkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_type: DocumentTargetType
    target_id: UUID
    document_path: str = Field(min_length=1, max_length=1000)


class DocumentLinkRead(BaseModel):
    id: UUID
    target_type: DocumentTargetType
    target_id: UUID
    document_path: str
    document_name: str
    document_etag: str | None
    available: bool
    created_at: datetime
    updated_at: datetime
