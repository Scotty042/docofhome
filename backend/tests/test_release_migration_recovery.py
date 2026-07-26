import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from app.core.settings import settings


def _alembic_config() -> Config:
    backend_dir = Path(__file__).parents[1]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("script_location", str(backend_dir / "migrations"))
    return config


def test_release_migration_recovers_stale_sqlite_batch_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = _alembic_config()
    command.upgrade(config, "0023")

    work_item_id = "11111111111111111111111111111111"
    with sqlite3.connect(settings.database_path) as connection:
        connection.execute(
            """
            INSERT INTO work_items (
                id, item_type, title, priority, status, created_at, updated_at
            ) VALUES (?, 'task', 'Must survive recovery', 'normal', 'open', ?, ?)
            """,
            (work_item_id, "2026-07-23 12:00:00", "2026-07-23 12:00:00"),
        )
        connection.execute(
            "CREATE TABLE _alembic_tmp_work_items AS SELECT * FROM work_items"
        )

    command.upgrade(config, "head")

    with sqlite3.connect(settings.database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(work_items)").fetchall()
        }
        preserved_title = connection.execute(
            "SELECT title FROM work_items WHERE id = ?", (work_item_id,)
        ).fetchone()
        revision = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()

    assert "_alembic_tmp_work_items" not in tables
    assert "recurrence_mode" in columns
    assert preserved_title == ("Must survive recovery",)
    assert revision == ("0026",)
