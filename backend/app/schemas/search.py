from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SearchResultType(StrEnum):
    ASSET = "asset"
    LOCATION = "location"
    ELECTRICAL_DISTRIBUTION = "electrical_distribution"
    ELECTRICAL_PROTECTIVE_DEVICE = "electrical_protective_device"
    ELECTRICAL_CIRCUIT = "electrical_circuit"
    WIKI_PAGE = "wiki_page"
    NETWORK_DEVICE = "network_device"
    NETWORK_SEGMENT = "network_segment"
    CONSUMPTION_METER = "consumption_meter"
    DOCUMENT = "document"


class SearchResultRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_type: SearchResultType
    id: UUID
    title: str
    subtitle: str
    description: str | None = None
    route: str
    archived: bool
    matched_fields: list[str] = Field(default_factory=list)


class SearchGroupRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_type: SearchResultType
    label: str
    total: int = Field(ge=0)
    results: list[SearchResultRead] = Field(default_factory=list)


class SearchResponseRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    total: int = Field(ge=0)
    groups: list[SearchGroupRead]
