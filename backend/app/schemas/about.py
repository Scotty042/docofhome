from datetime import date
from enum import StrEnum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)


class AboutLinkRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    url: str
    icon: str


class ReleaseNoteRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    title: str
    release_date: date | None = None
    markdown: str
    current: bool = False


class AboutRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    slogan: str
    version: str
    project_summary: str
    data_sovereignty: str
    license_notice: str
    links: list[AboutLinkRead]
    releases: list[ReleaseNoteRead]
    feedback_available: bool
    feedback_unavailable_reason: str | None = None


class FeedbackCategory(StrEnum):
    ERROR = "error"
    IMPROVEMENT = "improvement"
    USABILITY = "usability"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class FeedbackTechnicalInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app_version: str | None = Field(default=None, max_length=50)
    route: str | None = Field(default=None, max_length=500)
    user_agent: str | None = Field(default=None, max_length=500)
    viewport: str | None = Field(default=None, max_length=50)

    @field_validator("app_version", "route", "user_agent", "viewport")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class FeedbackWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: FeedbackCategory
    subject: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=10, max_length=10_000)
    current_page: str | None = Field(default=None, max_length=500)
    include_technical_info: bool = False
    technical_info: FeedbackTechnicalInfo | None = None

    @field_validator("subject", "description")
    @classmethod
    def normalize_required_text(cls, value: str, info: ValidationInfo) -> str:
        normalized = value.strip()
        minimum = 3 if info.field_name == "subject" else 10
        if len(normalized) < minimum:
            label = "Betreff" if info.field_name == "subject" else "Beschreibung"
            raise ValueError(f"{label} ist zu kurz")
        return normalized

    @field_validator("current_page")
    @classmethod
    def normalize_current_page(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def technical_info_requires_consent(self) -> "FeedbackWrite":
        if self.technical_info is not None and not self.include_technical_info:
            raise ValueError("Technische Informationen benötigen eine ausdrückliche Zustimmung")
        return self


class FeedbackResultRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted: bool = True
    message: str
    reference: str
