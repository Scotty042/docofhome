"""Dependency-free contract for the 1.7.5 migration retained by 1.7.6."""

from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "backend/migrations/versions/0051_subject_activity_ux.py"
text = path.read_text()

assert 'revision: str = "0051"' in text
assert 'down_revision: str | None = "0050"' in text
assert "'+2000 years'" in text
assert "ck_work_items_recurrence_due" in text
assert "def downgrade()" in text
print("Migration 0051 Vertrag erfolgreich.")
