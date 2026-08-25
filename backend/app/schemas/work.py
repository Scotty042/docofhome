from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.knowledge import KnowledgeTargetType


class WorkItemType(StrEnum):
    TASK = "task"
    MAINTENANCE = "maintenance"


class WorkStatus(StrEnum):
    OPEN = "open"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class RecurrenceMode(StrEnum):
    NONE = "none"
    INTERVAL = "interval"
    CALENDAR = "calendar"


class WorkSubjectType(StrEnum):
    DEVICE = "device"
    ANIMAL = "animal"
    VEHICLE = "vehicle"
    BUILDING = "building"
    ROOM = "room"
    INSTALLATION = "installation"
    GENERAL = "general"
    OTHER = "other"


class WorkSubjectWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    subject_type: WorkSubjectType = WorkSubjectType.GENERAL
    description: str | None = Field(default=None, max_length=20000)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Der Name darf nicht leer sein")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()


class WorkSubjectRead(WorkSubjectWrite):
    id: UUID
    created_at: datetime
    updated_at: datetime
    activity_count: int = Field(default=0, ge=0)


class WorkItemWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_type: WorkItemType
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    target_type: KnowledgeTargetType | None = None
    target_id: UUID | None = None
    subject_id: UUID | None = None
    due_at: datetime | None = None
    recurrence_days: int | None = Field(default=None, ge=1, le=3650)
    recurrence_mode: RecurrenceMode = RecurrenceMode.NONE
    calendar_months: int | None = None
    calendar_day: int | None = Field(default=None, ge=1, le=31)
    calendar_month: int | None = Field(default=None, ge=1, le=12)
    calendar_last_day: bool = False
    priority: WorkPriority = WorkPriority.NORMAL

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Der Titel darf nicht leer sein")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()

    @model_validator(mode="after")
    def validate_target_and_recurrence(self) -> "WorkItemWrite":
        if (self.target_type is None) != (self.target_id is None):
            raise ValueError("Zieltyp und Ziel-ID müssen gemeinsam angegeben werden")
        if self.subject_id is not None and self.target_id is not None:
            raise ValueError(
                "Ein Eintrag kann entweder einem Bezugsobjekt oder einem bestehenden Objekt "
                "zugeordnet werden"
            )
        if self.recurrence_days is not None and self.recurrence_mode == RecurrenceMode.NONE:
            self.recurrence_mode = RecurrenceMode.INTERVAL
        if self.item_type == WorkItemType.TASK and self.recurrence_mode != RecurrenceMode.NONE:
            raise ValueError("Wiederholungen sind nur für Wartungen zulässig")
        if self.recurrence_mode == RecurrenceMode.INTERVAL:
            if self.recurrence_days is None:
                raise ValueError("Intervallwiederholungen benötigen eine Anzahl Tage")
            if (
                any(
                    value is not None
                    for value in (self.calendar_months, self.calendar_day, self.calendar_month)
                )
                or self.calendar_last_day
            ):
                raise ValueError("Intervall- und Kalenderwiederholung dürfen nicht gemischt werden")
        if self.recurrence_mode == RecurrenceMode.CALENDAR:
            if self.recurrence_days is not None:
                raise ValueError("Kalenderwiederholungen verwenden kein Tagesintervall")
            if self.calendar_months is None or not 1 <= self.calendar_months <= 120:
                raise ValueError("Das Monatsintervall muss zwischen 1 und 120 liegen")
            if (self.calendar_day is None) == (not self.calendar_last_day):
                raise ValueError("Kalenderwiederholung benötigt Kalendertag oder Monatsende")
        if self.recurrence_mode == RecurrenceMode.NONE:
            self.recurrence_days = None
            self.calendar_months = None
            self.calendar_day = None
            self.calendar_month = None
            self.calendar_last_day = False
        return self


class WorkItemRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    item_type: WorkItemType
    title: str
    description: str | None
    target_type: KnowledgeTargetType | None
    target_id: UUID | None
    subject_id: UUID | None
    subject_name: str | None
    subject_type: WorkSubjectType | None
    target_label: str | None
    target_route: str | None
    automation_key: str | None = None
    generated: bool = False
    due_at: datetime | None
    recurrence_days: int | None
    recurrence_mode: RecurrenceMode
    calendar_months: int | None
    calendar_day: int | None
    calendar_month: int | None
    calendar_last_day: bool
    priority: WorkPriority
    status: WorkStatus
    overdue: bool
    due_status: str | None
    days_remaining: int | None
    completed_at: datetime | None
    history_count: int = Field(default=0, ge=0)
    last_performed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class WorkEventAttachmentRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    event_id: UUID
    file_name: str
    content_type: str
    size_bytes: int = Field(ge=0)
    created_at: datetime


class WorkItemEventRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    work_item_id: UUID
    event_type: str
    note: str | None
    due_at_before: datetime | None
    due_at_after: datetime | None
    occurred_at: datetime
    cost_amount: float | None
    cost_currency: str | None
    reading_value: float | None
    reading_unit: str | None
    interval_days: int | None = None
    attachments: list[WorkEventAttachmentRead] = Field(default_factory=list)
    created_at: datetime


class WorkCompletionWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str | None = Field(default=None, max_length=2000)
    occurred_at: datetime | None = None
    cost_amount: float | None = Field(default=None, ge=0, le=1_000_000_000)
    cost_currency: str | None = Field(default="EUR", min_length=3, max_length=3)
    reading_value: float | None = None
    reading_unit: str | None = Field(default=None, max_length=30)

    @field_validator("note", "reading_unit")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()

    @field_validator("cost_currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip().upper()


class WorkHistoryEntryWrite(WorkCompletionWrite):
    occurred_at: datetime


class WorkHistoryStatsRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int = Field(ge=0)
    last_performed_at: datetime | None
    previous_performed_at: datetime | None
    last_interval_days: int | None
    average_interval_days: float | None
    shortest_interval_days: int | None
    longest_interval_days: int | None


class WorkHistoryRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: UUID
    stats: WorkHistoryStatsRead
    entries: list[WorkItemEventRead]


class WorkSummaryRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    open_total: int = Field(ge=0)
    overdue: int = Field(ge=0)
    due_next_7_days: int = Field(ge=0)
    due_next_3_days: int = Field(ge=0)
    due_today: int = Field(ge=0)
    completed_total: int = Field(ge=0)
