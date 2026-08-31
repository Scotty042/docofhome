from pathlib import Path

path = Path(__file__).resolve().parents[1] / "backend/migrations/versions/0055_work_subject_timeline_paperless.py"
content = path.read_text(encoding="utf-8")
markers = (
    'revision: str = "0055"',
    'down_revision: str | None = "0054"',
    'profile_json',
    'activity_kind',
    'work_item_event_paperless_links',
    'uq_work_event_paperless_document',
)
for marker in markers:
    if marker not in content:
        raise SystemExit(f"Migration 0055 unvollständig: {marker}")
print("Migration 0055 statisch geprüft.")
