from pathlib import Path

source = (Path(__file__).resolve().parents[1] / "backend/migrations/versions/0057_recipe_title_integrity.py").read_text(encoding="utf-8")
for marker in ('revision = "0057"', 'down_revision = "0056"', 'ck_recipes_title_not_blank', 'Wiederhergestelltes Rezept', 'batch.drop_constraint'):
    assert marker in source, marker
print("Migration 0057 statisch geprüft.")
