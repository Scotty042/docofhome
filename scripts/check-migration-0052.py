from pathlib import Path

path = Path(__file__).resolve().parents[1] / "backend/migrations/versions/0052_cookbook_and_navigation.py"
content = path.read_text(encoding="utf-8")
for marker in ('down_revision: str | None = "0051"', '"recipes"', '"main_menu_modules_json"'):
    if marker not in content:
        raise SystemExit(f"Migration 0052 unvollständig: {marker}")
print("Migration 0052 statisch geprüft.")
