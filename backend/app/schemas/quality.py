from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class QualitySeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class QualityIssueRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    category: str
    severity: QualitySeverity
    code: str
    title: str
    description: str
    target_type: str | None
    target_id: UUID | None
    route: str | None
    created_at: datetime


class QualityReportRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    trigger: str
    score: int = Field(ge=0, le=100)
    issue_count: int = Field(ge=0)
    error_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    info_count: int = Field(ge=0)
    started_at: datetime
    completed_at: datetime
    issues: list[QualityIssueRead]
