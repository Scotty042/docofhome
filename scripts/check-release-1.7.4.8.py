"""Verify DocOfHome 1.7.4.8 meter-reading release contracts."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(relative: str, fragments: tuple[str, ...]) -> None:
    source = read(relative)
    missing = [fragment for fragment in fragments if fragment not in source]
    if missing:
        raise AssertionError(f"{relative}: fehlt: {', '.join(missing)}")


def reject(relative: str, fragments: tuple[str, ...]) -> None:
    source = read(relative)
    present = [fragment for fragment in fragments if fragment in source]
    if present:
        raise AssertionError(f"{relative}: unerwünscht: {', '.join(present)}")


def main() -> int:
    version = "1.7.4.8"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    source = json.loads(read("SOURCE_INFO.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    assert source["version"] == version and source["base_version"] == "1.7.4.7"
    assert source["release_notes"] == "RELEASE_NOTES_1.7.4.8.md"
    assert source["alembic_head"] == "0049"

    require("backend/app/services/consumption_reminders.py", (
        "class MonthlyReadingWindow:",
        "def monthly_due_date(",
        "def monthly_reading_window(",
        "ends_before=_window_start(next_due",
    ))
    require("backend/app/services/consumption.py", (
        "monthly_reading_window",
        "for offset in (-1, 0):",
        "window.starts_on",
        "window.ends_before",
    ))
    require("backend/app/services/work.py", (
        "monthly_reading_window",
        "periods = {shift_month(today.year, today.month, offset) for offset in (-1, 0)}",
        "ConsumptionReading.measured_at >= start_local.astimezone(UTC)",
        "ConsumptionReading.measured_at < end_local.astimezone(UTC)",
    ))
    reject("backend/app/services/work.py", ("lead_days = max(reminder_days or [3])",))
    require("backend/tests/test_consumption_reminders.py", (
        "test_month_end_due_dates_cover_31_30_february_and_leap_year",
        "test_month_end_validity_window_rejects_early_and_accepts_due_readings",
        "test_late_reading_closes_previous_window_but_not_next_month",
        "test_additional_reminder_is_calendar_day_not_offset",
        "test_generated_task_stays_open_for_early_reading_and_late_reading_completes_it",
    ))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0049_")
    print("Releasevertrag 1.7.4.8 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
