"""Dependency-free DocOfHome 1.7.5 release contract."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
version = "1.7.5"
assert (root / "VERSION").read_text().strip() == version
assert json.loads((root / "frontend/package.json").read_text())["version"] == version
source = json.loads((root / "SOURCE_INFO.json").read_text())
assert source["version"] == version and source["base_version"] == "1.7.4.9"
assert source["alembic_head"] == "0051"
assert (root / "backend/migrations/versions/0051_subject_activity_ux.py").exists()
page = (root / "frontend/src/pages/MaintenancePage.vue").read_text()
for contract in ("Heute gegeben", "Anderes Datum / Details", 'type="date"', "history-summary"):
    assert contract in page, contract
schema = (root / "backend/app/schemas/work.py").read_text()
assert "Wiederkehrende Wartungen benötigen einen Fälligkeitstermin" not in schema
print("Releasevertrag 1.7.5 erfolgreich.")
