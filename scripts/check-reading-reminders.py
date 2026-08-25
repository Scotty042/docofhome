"""Run dependency-free regression checks for all reading reminder date rules."""

from datetime import UTC, date, datetime
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.consumption_reminders import (  # noqa: E402
    interval_due_date,
    monthly_reading_window,
)


def main() -> int:
    zone = ZoneInfo("Europe/Berlin")
    today = date(2026, 7, 23)

    assert interval_due_date(
        today=today,
        latest_measured_at=None,
        reminder_days=31,
        zone=zone,
    ) == today
    assert interval_due_date(
        today=today,
        latest_measured_at=datetime(2026, 6, 13, 12, tzinfo=UTC),
        reminder_days=31,
        zone=zone,
    ) == date(2026, 7, 14)
    assert interval_due_date(
        today=today,
        latest_measured_at=datetime(2026, 7, 13, 12),
        reminder_days=31,
        zone=zone,
    ) == date(2026, 8, 13)

    january = monthly_reading_window(
        year=2026,
        month=1,
        schedule_day=None,
        last_day=True,
        reminder_days=[],
    )
    february = monthly_reading_window(
        year=2024,
        month=2,
        schedule_day=None,
        last_day=True,
        reminder_days=[],
    )
    april = monthly_reading_window(
        year=2026,
        month=4,
        schedule_day=None,
        last_day=True,
        reminder_days=[12],
    )
    assert january.due_date == date(2026, 1, 31)
    assert january.starts_on == date(2026, 1, 28)
    assert february.due_date == date(2024, 2, 29)
    assert april.due_date == date(2026, 4, 30)
    assert april.starts_on == date(2026, 4, 12)

    maintenance_page = (ROOT / "frontend/src/pages/MaintenancePage.vue").read_text(
        encoding="utf-8"
    )
    assert '<v-card class="mb-4" title="Ableseerinnerungen"' in maintenance_page
    assert 'v-if="readingReminders.length" class="mb-4" title="Ableseerinnerungen"' not in maintenance_page
    assert "globale Fälligkeit nach der letzten Ablesung" in maintenance_page

    consumption_service = (ROOT / "backend/app/services/consumption.py").read_text(
        encoding="utf-8"
    )
    assert "fallback_interval_days = self.get_settings().reminder_days" in consumption_service
    assert "latest_measured_at=latest.measured_at if latest else None" in consumption_service

    print("Ableseerinnerungen: Intervall, Monatsfenster und Wartungskarte geprüft")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
