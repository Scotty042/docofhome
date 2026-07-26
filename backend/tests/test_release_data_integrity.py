from calendar import monthrange
from datetime import UTC, datetime, timedelta

from sqlmodel import Session

from app.models.asset_engine import Asset, AssetType
from app.models.consumption import ConsumptionMeter, ConsumptionReading, ConsumptionSetting
from app.models.work import WorkItem
from app.schemas.work import RecurrenceMode
from app.services.asset_engine import AssetService
from app.services.consumption import ConsumptionService
from app.services.work import WorkService


def test_next_inventory_number_skips_archived_and_preserves_width(session: Session) -> None:
    asset_type = AssetType(name="Inventar", code_prefix="INV")
    session.add(asset_type)
    session.flush()
    first = Asset(
        name="Aktiv",
        jarvis_code="INV-0001",
        inventory_number="0001",
        asset_type_id=asset_type.id,
    )
    archived = Asset(
        name="Archiviert",
        jarvis_code="INV-0002",
        inventory_number="0002",
        asset_type_id=asset_type.id,
        deleted_at=datetime.now(UTC),
    )
    session.add(first)
    session.add(archived)
    session.commit()
    assert AssetService(session).next_inventory_number() == "0003"


def test_calendar_recurrence_uses_last_available_february_day(session: Session) -> None:
    service = WorkService(session)
    record = WorkItem(
        item_type="maintenance",
        title="Monatsende",
        due_at=datetime(2024, 1, 31, 12, tzinfo=UTC),
        recurrence_mode=RecurrenceMode.CALENDAR.value,
        calendar_months=1,
        calendar_day=31,
    )
    next_due = service._next_calendar_due(record, datetime(2024, 2, 1, tzinfo=UTC))
    assert next_due == datetime(2024, 2, 29, 12, tzinfo=UTC)
    record.due_at = next_due
    following = service._next_calendar_due(record, datetime(2024, 3, 1, tzinfo=UTC))
    # The local wall-clock time remains stable across the Europe/Berlin DST boundary.
    assert following == datetime(2024, 3, 31, 11, tzinfo=UTC)


def test_monthly_reading_reminder_disappears_after_period_reading(session: Session) -> None:
    today = datetime.now(UTC)
    meter = ConsumptionMeter(
        name="Strom Hauptzähler",
        meter_type="electricity_grid",
        unit="kWh",
        decimals=1,
        reading_schedule_day=min(today.day, monthrange(today.year, today.month)[1]),
        reminder_days_json="[]",
    )
    session.add(meter)
    session.commit()
    service = ConsumptionService(session)
    reminders = service.reading_reminders(days_ahead=3)
    assert [item.meter_id for item in reminders] == [meter.id]
    session.add(
        ConsumptionReading(
            meter_id=meter.id,
            measured_at=today,
            value=123.4,
        )
    )
    session.commit()
    assert service.reading_reminders(days_ahead=3) == []


def test_interval_reading_reminder_is_visible_without_monthly_schedule(
    session: Session,
) -> None:
    now = datetime.now(UTC)
    setting = ConsumptionSetting(reminder_days=31, plausibility_threshold_percent=150)
    meter = ConsumptionMeter(
        name="Gas Hauptzähler",
        meter_type="gas",
        unit="m³",
        decimals=3,
    )
    session.add(setting)
    session.add(meter)
    session.flush()
    session.add(
        ConsumptionReading(
            meter_id=meter.id,
            measured_at=now - timedelta(days=40),
            value=4321.0,
        )
    )
    session.commit()

    reminders = ConsumptionService(session).reading_reminders(days_ahead=31)

    assert [item.meter_id for item in reminders] == [meter.id]
    assert reminders[0].days_remaining <= -9
    assert reminders[0].status == "overdue"


def test_meter_without_any_reading_is_immediately_visible_as_reminder(
    session: Session,
) -> None:
    meter = ConsumptionMeter(
        name="PV Erzeugung",
        meter_type="electricity_pv",
        unit="kWh",
        decimals=1,
    )
    session.add(meter)
    session.commit()

    reminders = ConsumptionService(session).reading_reminders(days_ahead=0)

    assert [item.meter_id for item in reminders] == [meter.id]
    assert reminders[0].days_remaining == 0
    assert reminders[0].status == "today"


def test_interval_reading_reminder_respects_the_requested_horizon(
    session: Session,
) -> None:
    now = datetime.now(UTC)
    setting = ConsumptionSetting(reminder_days=31, plausibility_threshold_percent=150)
    meter = ConsumptionMeter(
        name="Strom Nebenzähler",
        meter_type="electricity_grid",
        unit="kWh",
        decimals=1,
    )
    session.add(setting)
    session.add(meter)
    session.flush()
    session.add(
        ConsumptionReading(
            meter_id=meter.id,
            measured_at=now - timedelta(days=10),
            value=100.0,
        )
    )
    session.commit()

    assert ConsumptionService(session).reading_reminders(days_ahead=3) == []
