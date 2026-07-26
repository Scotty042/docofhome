import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config

from app.core.settings import settings


def test_immich_link_migration_preserves_existing_data_and_downgrades(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
    command.upgrade(config, "0011")

    database_path = settings.database_path
    asset_type_id = uuid4().hex
    asset_id = uuid4().hex
    ha_link_id = uuid4().hex
    timestamp = "2026-07-21 12:00:00"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "INSERT INTO asset_types "
            "(id, created_at, updated_at, deleted_at, name, code_prefix) "
            "VALUES (?, ?, ?, NULL, ?, ?)",
            (asset_type_id, timestamp, timestamp, "Panel", "PNL"),
        )
        connection.execute(
            "INSERT INTO assets "
            "(id, created_at, updated_at, deleted_at, name, asset_type_id, status, jarvis_code) "
            "VALUES (?, ?, ?, NULL, ?, ?, ?, ?)",
            (asset_id, timestamp, timestamp, "Main", asset_type_id, "active", "PNL-001"),
        )
        connection.execute(
            "INSERT INTO home_assistant_asset_links "
            "(id, object_type, external_id, asset_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ha_link_id, "entity", "sensor.panel", asset_id, timestamp, timestamp),
        )
        connection.execute(
            "INSERT INTO home_assistant_selection_settings "
            "(id, mode, created_at, updated_at) VALUES (1, 'selected', ?, ?)",
            (timestamp, timestamp),
        )
        connection.commit()

    command.upgrade(config, "head")
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM immich_asset_links").fetchone() == (0,)
        assert connection.execute(
            "SELECT mode FROM home_assistant_selection_settings"
        ).fetchone() == ("selected",)
        assert connection.execute(
            "SELECT external_id FROM home_assistant_asset_links"
        ).fetchone() == ("sensor.panel",)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    command.downgrade(config, "0011")
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert "immich_asset_links" not in tables
        assert connection.execute("SELECT name FROM assets").fetchone() == ("Main",)
        assert connection.execute(
            "SELECT mode FROM home_assistant_selection_settings"
        ).fetchone() == ("selected",)
