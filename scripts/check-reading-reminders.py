"""Run dependency-free regression checks for interval-based reading reminders."""

from datetime import UTC, date, datetime
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.consumption_reminders import interval_due_date  # noqa: E402


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

    print("Ableseerinnerungen: Intervall-Fallback und sichtbare Wartungskarte geprüft")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
