from datetime import UTC, date, datetime

from sqlmodel import Session, select

from app.models.consumption import ConsumptionMeter, ConsumptionReading
from app.models.work import WorkItem
from app.services.consumption import ConsumptionService
from app.services.consumption_reminders import monthly_reading_window
from app.services.work import WorkService


def window(year: int, month: int, *, reminders: list[int] | None = None):
    return monthly_reading_window(
        year=year,
        month=month,
        schedule_day=None,
        last_day=True,
        reminder_days=reminders or [],
    )


def test_month_end_due_dates_cover_31_30_february_and_leap_year() -> None:
    assert window(2025, 1).due_date == date(2025, 1, 31)
    assert window(2025, 4).due_date == date(2025, 4, 30)
    assert window(2025, 2).due_date == date(2025, 2, 28)
    assert window(2024, 2).due_date == date(2024, 2, 29)


def test_month_end_validity_window_rejects_early_and_accepts_due_readings() -> None:
    july = window(2025, 7)
    assert july.starts_on == date(2025, 7, 28)
    assert date(2025, 7, 5) < july.starts_on
    assert july.starts_on <= date(2025, 7, 28) < july.ends_before
    assert july.starts_on <= date(2025, 7, 31) < july.ends_before


def test_late_reading_closes_previous_window_but_not_next_month() -> None:
    july = window(2025, 7)
    august = window(2025, 8)
    late = date(2025, 8, 5)
    assert july.starts_on <= late < july.ends_before
    assert not (august.starts_on <= late < august.ends_before)


def test_additional_reminder_is_calendar_day_not_offset() -> None:
    july = window(2025, 7, reminders=[28])
    april = window(2025, 4, reminders=[12])
    assert july.starts_on == date(2025, 7, 28)
    assert april.starts_on == date(2025, 4, 12)


def _meter(session: Session) -> ConsumptionMeter:
    meter = ConsumptionMeter(
        name="Strom Hauptzähler",
        meter_type="electricity_grid",
        unit="kWh",
        decimals=1,
        reading_schedule_last_day=True,
        reminder_days_json="[]",
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
    )
    session.add(meter)
    session.commit()
    return meter


def test_api_reminder_ignores_early_reading_and_keeps_overdue_month(session: Session) -> None:
    meter = _meter(session)
    session.add(
        ConsumptionReading(
            meter_id=meter.id,
            measured_at=datetime(2025, 7, 5, 12, tzinfo=UTC),
            value=100,
        )
    )
    session.commit()

    reminders = ConsumptionService(session).reading_reminders(
        days_ahead=3, _today=date(2025, 8, 1)
    )

    assert len(reminders) == 1
    assert reminders[0].due_at.date() == date(2025, 7, 31)
    assert reminders[0].status == "overdue"


def test_api_reminder_is_completed_inside_window_and_by_late_reading(session: Session) -> None:
    meter = _meter(session)
    session.add(
        ConsumptionReading(
            meter_id=meter.id,
            measured_at=datetime(2025, 7, 29, 12, tzinfo=UTC),
            value=100,
        )
    )
    session.commit()
    assert ConsumptionService(session).reading_reminders(
        days_ahead=3, _today=date(2025, 8, 1)
    ) == []

    previous = session.exec(select(ConsumptionReading)).first()
    assert previous is not None
    previous.deleted_at = datetime(2025, 8, 1, tzinfo=UTC)
    session.add(
        ConsumptionReading(
            meter_id=meter.id,
            measured_at=datetime(2025, 8, 2, 12, tzinfo=UTC),
            value=101,
        )
    )
    session.commit()
    assert ConsumptionService(session).reading_reminders(
        days_ahead=3, _today=date(2025, 8, 3)
    ) == []


def test_generated_task_stays_open_for_early_reading_and_late_reading_completes_it(
    session: Session,
) -> None:
    meter = _meter(session)
    session.add(
        ConsumptionReading(
            meter_id=meter.id,
            measured_at=datetime(2025, 7, 5, 12, tzinfo=UTC),
            value=100,
        )
    )
    session.commit()
    service = WorkService(session)
    service._sync_monthly_meter_tasks(_today=date(2025, 8, 1))
    july = session.exec(
        select(WorkItem).where(
            WorkItem.automation_key == f"meter-reading:{meter.id}:2025-07"
        )
    ).one()
    assert july.status == "open"

    session.add(
        ConsumptionReading(
            meter_id=meter.id,
            measured_at=datetime(2025, 8, 2, 12, tzinfo=UTC),
            value=101,
        )
    )
    session.commit()
    service._sync_monthly_meter_tasks(_today=date(2025, 8, 3))
    session.refresh(july)
    assert july.status == "completed"
