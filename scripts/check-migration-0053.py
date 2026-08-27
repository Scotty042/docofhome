from pathlib import Path

path = Path(__file__).resolve().parents[1] / "backend/migrations/versions/0053_complete_module_navigation.py"
content = path.read_text(encoding="utf-8")
for marker in (
    'down_revision: str | None = "0052"',
    '"images"',
    '"documents"',
    '"workloads"',
    '"enabled_modules_json"',
    '"main_menu_modules_json"',
):
    if marker not in content:
        raise SystemExit(f"Migration 0053 unvollständig: {marker}")
print("Migration 0053 statisch geprüft.")
