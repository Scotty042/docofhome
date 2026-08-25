"""Shared, dependency-free date rules for consumption reading reminders."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo


DEFAULT_MONTHLY_LEAD_DAYS = 3


@dataclass(frozen=True)
class MonthlyReadingWindow:
    """One monthly due date and the period in which a reading satisfies it."""

    due_date: date
    starts_on: date
    ends_before: date


def shift_month(year: int, month: int, offset: int) -> tuple[int, int]:
    absolute = year * 12 + month - 1 + offset
    return absolute // 12, absolute % 12 + 1


def monthly_due_date(
    *, year: int, month: int, schedule_day: int | None, last_day: bool
) -> date:
    """Resolve a monthly schedule, clipping day 29-31 to the calendar month."""

    maximum = monthrange(year, month)[1]
    day = maximum if last_day else min(schedule_day or maximum, maximum)
    return date(year, month, day)


def _window_start(
    due_date: date,
    reminder_days: list[int],
    *,
    lead_days: int = DEFAULT_MONTHLY_LEAD_DAYS,
) -> date:
    """Return the first valid reading day for a due date.

    ``reminder_days`` are calendar days (for example 28 means the 28th), not
    offsets. A configured reminder on or before the due date opens the window.
    """

    maximum = monthrange(due_date.year, due_date.month)[1]
    configured = [
        date(due_date.year, due_date.month, min(max(1, int(day)), maximum))
        for day in reminder_days
    ]
    eligible = [candidate for candidate in configured if candidate <= due_date]
    return min([due_date - timedelta(days=lead_days), *eligible])


def monthly_reading_window(
    *,
    year: int,
    month: int,
    schedule_day: int | None,
    last_day: bool,
    reminder_days: list[int],
    lead_days: int = DEFAULT_MONTHLY_LEAD_DAYS,
) -> MonthlyReadingWindow:
    """Build a non-overlapping validity window for one monthly due date.

    A late reading remains valid until the following month's reading window
    begins. This lets an August reading close an overdue July task without also
    completing the August task early.
    """

    due = monthly_due_date(
        year=year,
        month=month,
        schedule_day=schedule_day,
        last_day=last_day,
    )
    next_year, next_month = shift_month(year, month, 1)
    next_due = monthly_due_date(
        year=next_year,
        month=next_month,
        schedule_day=schedule_day,
        last_day=last_day,
    )
    return MonthlyReadingWindow(
        due_date=due,
        starts_on=_window_start(due, reminder_days, lead_days=lead_days),
        ends_before=_window_start(next_due, reminder_days, lead_days=lead_days),
    )


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
