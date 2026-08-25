import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401
from app.models.asset_engine import Asset, AssetType
from app.schemas.knowledge import KnowledgeTargetType
from app.schemas.work import (
    WorkCompletionWrite,
    WorkItemType,
    WorkItemWrite,
    WorkPriority,
    WorkStatus,
)
from app.services.work import WorkConflictError, WorkService, WorkValidationError


@pytest.fixture
def work_session(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'work.sqlite3'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_recurring_maintenance_advances_and_keeps_history(work_session: Session) -> None:
    due = datetime.now(UTC) - timedelta(days=10)
    service = WorkService(work_session)
    item = service.create(
        WorkItemWrite(
            item_type=WorkItemType.MAINTENANCE,
            title="Filter wechseln",
            due_at=due,
            recurrence_days=7,
            priority=WorkPriority.HIGH,
        )
    )
    assert item.overdue is True

    completed = service.complete(item.id, WorkCompletionWrite(note="Filter ersetzt"))
    assert completed.status == WorkStatus.OPEN
    assert completed.due_at is not None and completed.due_at > datetime.now(UTC)
    events = service.events(item.id)
    assert events[0].event_type == "completed"
    assert events[0].due_at_after == completed.due_at


def test_one_off_task_is_completed_and_summary_counts_overdue(work_session: Session) -> None:
    service = WorkService(work_session)
    overdue = service.create(
        WorkItemWrite(
            item_type=WorkItemType.TASK,
            title="Prüfprotokoll ergänzen",
            due_at=datetime.now(UTC) - timedelta(days=1),
        )
    )
    assert service.summary().overdue == 1
    completed = service.complete(overdue.id, WorkCompletionWrite())
    assert completed.status == WorkStatus.COMPLETED
    assert service.summary().overdue == 0


def test_archived_target_keeps_existing_work_but_rejects_new_entries(
    work_session: Session,
) -> None:
    asset_type = AssetType(name="Heizung", code_prefix="HZG")
    work_session.add(asset_type)
    work_session.flush()
    asset = Asset(name="Wärmepumpe", jarvis_code="HZG-0001", asset_type_id=asset_type.id)
    work_session.add(asset)
    work_session.commit()

    service = WorkService(work_session)
    item = service.create(
        WorkItemWrite(
            item_type=WorkItemType.MAINTENANCE,
            title="Filter prüfen",
            target_type=KnowledgeTargetType.ASSET,
            target_id=asset.id,
            due_at=datetime.now(UTC) + timedelta(days=30),
        )
    )
    asset.deleted_at = datetime.now(UTC)
    work_session.add(asset)
    work_session.commit()

    updated = service.update(
        item.id,
        WorkItemWrite(
            item_type=WorkItemType.MAINTENANCE,
            title="Filter und Dichtung prüfen",
            target_type=KnowledgeTargetType.ASSET,
            target_id=asset.id,
            due_at=item.due_at,
        ),
    )
    assert updated.title == "Filter und Dichtung prüfen"
    with pytest.raises(WorkValidationError):
        service.create(
            WorkItemWrite(
                item_type=WorkItemType.TASK,
                title="Neue Aufgabe",
                target_type=KnowledgeTargetType.ASSET,
                target_id=asset.id,
            )
        )


def test_monthly_meter_task_is_idempotent_and_completed_by_reading(
    work_session: Session,
) -> None:
    from app.models.consumption import ConsumptionMeter, ConsumptionReading

    now = datetime.now(ZoneInfo("Europe/Berlin"))
    meter = ConsumptionMeter(
        name="Strombezug Haus",
        meter_type="electricity_grid",
        unit="kWh",
        reading_schedule_day=now.day,
    )
    work_session.add(meter)
    work_session.commit()

    service = WorkService(work_session)
    first = [item for item in service.list() if item.generated]
    second = [item for item in service.list() if item.generated]
    assert len(first) == 1
    assert [item.id for item in second] == [first[0].id]
    assert first[0].automation_key == f"meter-reading:{meter.id}:{now:%Y-%m}"
    assert first[0].target_route == f"/consumption?read={meter.id}"
    assert first[0].status == WorkStatus.OPEN

    work_session.add(
        ConsumptionReading(
            meter_id=meter.id,
            measured_at=now,
            value=1234.5,
        )
    )
    work_session.commit()

    completed = next(item for item in service.list() if item.id == first[0].id)
    assert completed.status == WorkStatus.COMPLETED
    assert completed.completed_at is not None
    assert service.events(completed.id)[0].note == (
        "Automatisch durch gespeicherte Zählerablesung erledigt."
    )


def test_disabling_monthly_meter_plan_cancels_open_generated_task(
    work_session: Session,
) -> None:
    from app.models.consumption import ConsumptionMeter

    meter = ConsumptionMeter(
        name="Gaszähler",
        meter_type="gas",
        unit="m³",
        reading_schedule_last_day=True,
        reminder_days_json=json.dumps([datetime.now(ZoneInfo("Europe/Berlin")).day]),
    )
    work_session.add(meter)
    work_session.commit()
    service = WorkService(work_session)
    generated = next(item for item in service.list() if item.generated)

    meter.reading_schedule_last_day = False
    work_session.add(meter)
    work_session.commit()

    cancelled = next(item for item in service.list() if item.id == generated.id)
    assert cancelled.status == WorkStatus.CANCELLED


def test_reenabling_monthly_plan_reopens_generated_task(work_session: Session) -> None:
    from app.models.consumption import ConsumptionMeter

    meter = ConsumptionMeter(
        name="Wasser Hauptzähler",
        meter_type="water",
        unit="m³",
        reading_schedule_last_day=True,
        reminder_days_json=json.dumps([datetime.now(ZoneInfo("Europe/Berlin")).day]),
    )
    work_session.add(meter)
    work_session.commit()
    service = WorkService(work_session)
    generated = next(item for item in service.list() if item.generated)

    meter.reading_schedule_last_day = False
    work_session.add(meter)
    work_session.commit()
    assert next(item for item in service.list() if item.id == generated.id).status == (
        WorkStatus.CANCELLED
    )

    meter.reading_schedule_day = 15
    work_session.add(meter)
    work_session.commit()
    reopened = next(item for item in service.list() if item.id == generated.id)
    assert reopened.status == WorkStatus.OPEN
    assert service.events(reopened.id)[0].event_type == "reopened"


def test_generated_meter_task_cannot_be_changed_manually(work_session: Session) -> None:
    from app.models.consumption import ConsumptionMeter

    meter = ConsumptionMeter(
        name="PV-Erzeugung",
        meter_type="electricity_pv",
        unit="kWh",
        reading_schedule_last_day=True,
        reminder_days_json=json.dumps([datetime.now(ZoneInfo("Europe/Berlin")).day]),
    )
    work_session.add(meter)
    work_session.commit()
    service = WorkService(work_session)
    generated = next(item for item in service.list() if item.generated)

    with pytest.raises(WorkConflictError):
        service.complete(generated.id, WorkCompletionWrite())
    with pytest.raises(WorkConflictError):
        service.cancel(generated.id)
    with pytest.raises(WorkConflictError):
        service.delete(generated.id)


def test_work_subject_and_manual_history_statistics(work_session: Session) -> None:
    from app.schemas.work import WorkHistoryEntryWrite, WorkSubjectType, WorkSubjectWrite

    service = WorkService(work_session)
    penny = service.create_subject(
        WorkSubjectWrite(name="Penny", subject_type=WorkSubjectType.ANIMAL)
    )
    item = service.create(
        WorkItemWrite(
            item_type=WorkItemType.MAINTENANCE,
            title="Impfung",
            subject_id=penny.id,
        )
    )
    first = datetime(2025, 2, 3, 10, 0, tzinfo=UTC)
    second = datetime(2026, 2, 4, 10, 0, tzinfo=UTC)
    service.add_history(item.id, WorkHistoryEntryWrite(occurred_at=first, note="Erste Impfung"))
    service.add_history(item.id, WorkHistoryEntryWrite(occurred_at=second, note="Auffrischung"))

    history = service.history(item.id)
    assert history.stats.count == 2
    assert history.stats.last_interval_days == 366
    assert history.stats.average_interval_days == 366
    assert history.entries[0].interval_days == 366
    refreshed = service.get(item.id)
    assert refreshed.subject_name == "Penny"
    assert refreshed.history_count == 2


def test_history_entry_supports_cost_reading_and_database_attachment(work_session: Session) -> None:
    from app.schemas.work import WorkHistoryEntryWrite

    service = WorkService(work_session)
    item = service.create(
        WorkItemWrite(item_type=WorkItemType.MAINTENANCE, title="Filter wechseln")
    )
    entry = service.add_history(
        item.id,
        WorkHistoryEntryWrite(
            occurred_at=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
            note="Filter ersetzt",
            cost_amount=24.9,
            cost_currency="EUR",
            reading_value=123.0,
            reading_unit="h",
        ),
    )
    attachment = service.add_attachment(
        item.id,
        entry.id,
        "beleg.pdf",
        "application/pdf",
        b"%PDF-test",
    )
    _record, content = service.attachment(item.id, entry.id, attachment.id)
    assert content == b"%PDF-test"
    loaded = service.history(item.id).entries[0]
    assert loaded.cost_amount == 24.9
    assert loaded.reading_value == 123.0
    assert loaded.attachments[0].file_name == "beleg.pdf"
