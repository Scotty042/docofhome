import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from app.core.settings import settings


def test_upgrade_repairs_blank_titles_without_losing_recipe_content(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    backend = Path(__file__).parents[1]
    config = Config(str(backend / "alembic.ini"))
    config.set_main_option("script_location", str(backend / "migrations"))
    command.upgrade(config, "0056")
    with sqlite3.connect(settings.database_path) as connection:
        connection.execute(
            "INSERT INTO recipes (id, title, ingredients_json, steps_json, servings, favorite, "
            "created_at, updated_at, category, tags_json, notes, attachments_json) "
            "VALUES ('blank', '   ', '[\"Kartoffeln\"]', '[\"Kochen\"]', 2, 0, "
            "'2026-09-08', '2026-09-08', '', '[]', '', '[]')"
        )
    command.upgrade(config, "head")
    with sqlite3.connect(settings.database_path) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == ("0060",)
        assert connection.execute(
            "SELECT title, ingredients_json, steps_json FROM recipes WHERE id='blank'"
        ).fetchone() == ("Wiederhergestelltes Rezept blank", '["Kartoffeln"]', '["Kochen"]')
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE recipes SET title=' ' WHERE id='blank'")
    command.downgrade(config, "0056")
    with sqlite3.connect(settings.database_path) as connection:
        assert connection.execute(
            "SELECT ingredients_json FROM recipes WHERE id='blank'"
        ).fetchone() == ('["Kartoffeln"]',)
