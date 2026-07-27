from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, Text, text
from sqlmodel import Field, SQLModel


class WorkItem(SQLModel, table=True):
    __tablename__ = "work_items"
    __table_args__ = (
        CheckConstraint(
            "item_type IN ('task', 'maintenance')",
            name="ck_work_items_item_type",
        ),
        CheckConstraint(
            "status IN ('open', 'completed', 'cancelled')",
            name="ck_work_items_status",
        ),
        CheckConstraint(
            "priority IN ('low', 'normal', 'high')",
            name="ck_work_items_priority",
        ),
        CheckConstraint(
            "target_type IS NULL OR target_type IN ('asset', 'location', 'distribution', "
            "'protective_device', 'circuit')",
            name="ck_work_items_target_type",
        ),
        CheckConstraint(
            "(target_type IS NULL AND target_id IS NULL) OR "
            "(target_type IS NOT NULL AND target_id IS NOT NULL)",
            name="ck_work_items_target_pair",
        ),
        CheckConstraint(
            "recurrence_days IS NULL OR (recurrence_days >= 1 AND recurrence_days <= 3650)",
            name="ck_work_items_recurrence_days",
        ),
        CheckConstraint(
            "recurrence_days IS NULL OR item_type = 'maintenance'",
            name="ck_work_items_recurrence_type",
        ),
        CheckConstraint(
            "recurrence_days IS NULL OR due_at IS NOT NULL",
            name="ck_work_items_recurrence_due",
        ),
        CheckConstraint(
            "recurrence_mode IN ('none', 'interval', 'calendar')",
            name="ck_work_items_recurrence_mode",
        ),
        CheckConstraint(
            "calendar_months IS NULL OR calendar_months IN (1, 2, 3, 6, 12)",
            name="ck_work_items_calendar_months",
        ),
        CheckConstraint(
            "calendar_day IS NULL OR (calendar_day >= 1 AND calendar_day <= 31)",
            name="ck_work_items_calendar_day",
        ),
        CheckConstraint(
            "calendar_month IS NULL OR (calendar_month >= 1 AND calendar_month <= 12)",
            name="ck_work_items_calendar_month",
        ),
        Index(
            "ix_work_items_open_due",
            "status",
            "due_at",
            sqlite_where=text("deleted_at IS NULL"),
        ),
        Index(
            "uq_work_items_automation_key",
            "automation_key",
            unique=True,
            sqlite_where=text("automation_key IS NOT NULL AND deleted_at IS NULL"),
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    item_type: str = Field(index=True, max_length=20)
    title: str = Field(index=True, max_length=200)
    description: str | None = Field(default=None, sa_type=Text)
    target_type: str | None = Field(default=None, index=True, max_length=30)
    target_id: UUID | None = Field(default=None, index=True)
    due_at: datetime | None = Field(default=None, index=True)
    recurrence_days: int | None = Field(default=None, ge=1, le=3650)
    recurrence_mode: str = Field(default="none", index=True, max_length=20)
    calendar_months: int | None = Field(default=None)
    calendar_day: int | None = Field(default=None, ge=1, le=31)
    calendar_month: int | None = Field(default=None, ge=1, le=12)
    calendar_last_day: bool = False
    priority: str = Field(default="normal", index=True, max_length=20)
    automation_key: str | None = Field(default=None, max_length=255)
    status: str = Field(default="open", index=True, max_length=20)
    completed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)


class WorkItemEvent(SQLModel, table=True):
    __tablename__ = "work_item_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('completed', 'reopened', 'cancelled')",
            name="ck_work_item_events_type",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    work_item_id: UUID = Field(foreign_key="work_items.id", index=True)
    event_type: str = Field(index=True, max_length=20)
    note: str | None = Field(default=None, sa_type=Text)
    due_at_before: datetime | None = None
    due_at_after: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
