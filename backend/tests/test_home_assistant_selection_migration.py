import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config

from app.core.settings import settings


def test_selection_migration_preserves_links_and_downgrades_to_0010(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
    command.upgrade(config, "0010")

    database_path = settings.database_path
    asset_type_id = uuid4().hex
    asset_id = uuid4().hex
    link_id = uuid4().hex
    timestamp = "2026-07-21 12:00:00"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "INSERT INTO asset_types "
            "(id, created_at, updated_at, deleted_at, name, code_prefix) "
            "VALUES (?, ?, ?, NULL, ?, ?)",
            (asset_type_id, timestamp, timestamp, "Smart Home", "SH"),
        )
        connection.execute(
            "INSERT INTO assets "
            "(id, created_at, updated_at, deleted_at, name, asset_type_id, status, jarvis_code) "
            "VALUES (?, ?, ?, NULL, ?, ?, ?, ?)",
            (asset_id, timestamp, timestamp, "Meter", asset_type_id, "active", "SH-001"),
        )
        connection.execute(
            "INSERT INTO home_assistant_asset_links "
            "(id, object_type, external_id, asset_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                link_id,
                "entity",
                "sensor.grid_power",
                asset_id,
                timestamp,
                timestamp,
            ),
        )
        connection.commit()

    command.upgrade(config, "head")
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM home_assistant_selection_settings"
        ).fetchone() == (0,)
        assert connection.execute(
            "SELECT external_id, asset_id FROM home_assistant_asset_links"
        ).fetchone() == ("sensor.grid_power", asset_id)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    command.downgrade(config, "0010")
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert "home_assistant_selection_settings" not in tables
        assert "home_assistant_entity_selections" not in tables
        assert connection.execute(
            "SELECT external_id FROM home_assistant_asset_links"
        ).fetchone() == ("sensor.grid_power",)
