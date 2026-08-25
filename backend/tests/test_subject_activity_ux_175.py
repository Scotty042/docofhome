from datetime import UTC, datetime

from app.schemas.work import RecurrenceMode, WorkCompletionWrite, WorkHistoryEntryWrite, WorkItemType, WorkItemWrite, WorkPriority, WorkSubjectType, WorkSubjectWrite
from app.services.work import WorkService


def test_recurring_subject_activity_needs_no_initial_due_date(session):
    service = WorkService(session)
    subject = service.create_subject(WorkSubjectWrite(name="Penny", subject_type=WorkSubjectType.ANIMAL))
    activity = service.create(WorkItemWrite(
        item_type=WorkItemType.MAINTENANCE, title="Zeckentablette", subject_id=subject.id,
        recurrence_mode=RecurrenceMode.INTERVAL, recurrence_days=90, priority=WorkPriority.NORMAL,
    ))
    assert activity.due_at is None
    completed = service.complete(activity.id, WorkCompletionWrite(occurred_at=datetime(2026, 5, 30, 12, tzinfo=UTC)))
    assert completed.due_at == datetime(2026, 8, 28, 12, tzinfo=UTC)


def test_history_is_sorted_by_calendar_date_and_uses_day_intervals(session):
    service = WorkService(session)
    activity = service.create(WorkItemWrite(item_type=WorkItemType.MAINTENANCE, title="Impfung", recurrence_mode=RecurrenceMode.NONE))
    for value in (datetime(2026, 5, 20, 23, tzinfo=UTC), datetime(2026, 5, 1, 1, tzinfo=UTC)):
        service.add_history(activity.id, WorkHistoryEntryWrite(occurred_at=value))
    history = service.history(activity.id)
    assert [entry.occurred_at.date().isoformat() for entry in history.entries] == ["2026-05-20", "2026-05-01"]
    assert history.entries[0].interval_days == 19
