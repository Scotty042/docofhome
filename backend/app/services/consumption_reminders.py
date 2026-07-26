"""Dependency-free date helpers for consumption reading reminders."""

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo


def interval_due_date(
    *,
    today: date,
    latest_measured_at: datetime | None,
    reminder_days: int,
    zone: ZoneInfo,
) -> date:
    """Return the local due date for the legacy interval-based reminder rule."""

    if latest_measured_at is None:
        return today
    measured_at = (
        latest_measured_at.replace(tzinfo=UTC)
        if latest_measured_at.tzinfo is None
        else latest_measured_at.astimezone(UTC)
    )
    return (measured_at + timedelta(days=reminder_days)).astimezone(zone).date()
