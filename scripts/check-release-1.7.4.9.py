"""Verify DocOfHome 1.7.4.9 work-history release contracts without project deps."""
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


def main() -> int:
    version = "1.7.4.9"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    source = json.loads(read("SOURCE_INFO.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    assert source["version"] == version and source["base_version"] == "1.7.4.8"
    assert source["release_notes"] == "RELEASE_NOTES_1.7.4.9.md"
    assert source["alembic_head"] == "0050"

    require("backend/app/models/work.py", (
        "class WorkSubject(SQLModel, table=True):",
        "subject_id: UUID | None",
        "occurred_at: datetime",
        "cost_amount: float | None",
        "reading_value: float | None",
        "class WorkItemEventAttachment(SQLModel, table=True):",
        "LargeBinary",
    ))
    require("backend/app/services/work.py", (
        "def history(self, item_id: UUID) -> WorkHistoryRead:",
        "def add_history(",
        "def update_history(",
        "def delete_history(",
        "average_interval_days",
        "shortest_interval_days",
        "longest_interval_days",
        "def create_subject(",
        "def add_attachment(",
        "content=content",
    ))
    require("backend/app/api/v1/work.py", (
        '"/subjects"',
        '"/{item_id}/history"',
        '"/{item_id}/history/{event_id}/attachments"',
    ))
    require("frontend/src/pages/MaintenancePage.vue", (
        "Bezugsobjekte",
        "Vergangene Durchführung",
        "Ø Abstand",
        "Datei oder Bild",
        "Penny",
    ))
    require("backend/tests/test_work_items.py", (
        "test_work_subject_and_manual_history_statistics",
        'name="Penny"',
        "assert history.stats.last_interval_days == 366",
        "test_history_entry_supports_cost_reading_and_database_attachment",
    ))
    require("backend/migrations/versions/0050_work_history_and_subjects.py", (
        'revision: str = "0050"',
        'down_revision: str | None = "0049"',
        '"work_subjects"',
        '"subject_id"',
        '"occurred_at"',
        '"work_item_event_attachments"',
        "sa.LargeBinary()",
    ))
    require("backend/app/services/release.py", (
        '("work_subjects", WorkSubject, True)',
        '"subject_id": WorkSubject',
    ))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0050_")
    print("Releasevertrag 1.7.4.9 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
