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


class WorkItemWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_type: WorkItemType
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    target_type: KnowledgeTargetType | None = None
    target_id: UUID | None = None
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
        if self.recurrence_days is not None and self.recurrence_mode == RecurrenceMode.NONE:
            self.recurrence_mode = RecurrenceMode.INTERVAL
        if self.item_type == WorkItemType.TASK and self.recurrence_mode != RecurrenceMode.NONE:
            raise ValueError("Wiederholungen sind nur für Wartungen zulässig")
        if self.recurrence_mode != RecurrenceMode.NONE and self.due_at is None:
            raise ValueError("Wiederkehrende Wartungen benötigen einen Fälligkeitstermin")
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
            if self.calendar_months not in {1, 2, 3, 6, 12}:
                raise ValueError("Kalenderintervall muss 1, 2, 3, 6 oder 12 Monate betragen")
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
    target_label: str | None
    target_route: str | None
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
    created_at: datetime
    updated_at: datetime


class WorkItemEventRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    work_item_id: UUID
    event_type: str
    note: str | None
    due_at_before: datetime | None
    due_at_after: datetime | None
    created_at: datetime


class WorkCompletionWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str | None = Field(default=None, max_length=2000)

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()


class WorkSummaryRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    open_total: int = Field(ge=0)
    overdue: int = Field(ge=0)
    due_next_7_days: int = Field(ge=0)
    due_next_3_days: int = Field(ge=0)
    due_today: int = Field(ge=0)
    completed_total: int = Field(ge=0)
