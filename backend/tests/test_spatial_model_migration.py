import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config

from app.core.settings import settings


def test_spatial_migration_preserves_and_reparents_existing_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
    command.upgrade(config, "0005")

    top_id = uuid4().hex
    child_id = uuid4().hex
    archived_id = uuid4().hex
    asset_type_id = uuid4().hex
    asset_id = uuid4().hex
    record = ("2026-07-20 12:00:00", "2026-07-20 12:00:00")
    with sqlite3.connect(settings.database_path) as connection:
        connection.execute(
            "INSERT INTO application_settings "
            "(id, installation_name, language, timezone, theme, setup_completed_at, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (1, "Existing House", "de", "Europe/Berlin", "dark", record[0], *record),
        )
        connection.execute(
            "INSERT INTO asset_types "
            "(id, created_at, updated_at, deleted_at, name, description, icon, code_prefix) "
            "VALUES (?, ?, ?, NULL, ?, NULL, NULL, ?)",
            (asset_type_id, *record, "Device", "DEV"),
        )
        connection.executemany(
            "INSERT INTO locations "
            "(id, created_at, updated_at, deleted_at, name, description, parent_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (top_id, *record, None, "Ground floor", "Existing top level", None),
                (child_id, *record, None, "Kitchen", "Existing child", top_id),
                (archived_id, *record, record[0], "Old shed", "Archived top level", None),
            ],
        )
        connection.execute(
            "INSERT INTO assets "
            "(id, created_at, updated_at, deleted_at, name, description, asset_type_id, "
            "product_id, location_id, serial_number, inventory_number, status, jarvis_code) "
            "VALUES (?, ?, ?, NULL, ?, NULL, ?, NULL, ?, NULL, NULL, ?, ?)",
            (asset_id, *record, "Existing oven", asset_type_id, child_id, "active", "DEV-001"),
        )
        connection.commit()

    command.upgrade(config, "head")

    with sqlite3.connect(settings.database_path) as connection:
        roots = connection.execute(
            "SELECT id, name, location_type FROM locations "
            "WHERE parent_id IS NULL AND deleted_at IS NULL"
        ).fetchall()
        rows = {
            row[0]: row[1:]
            for row in connection.execute(
                "SELECT id, name, description, parent_id, location_type, deleted_at "
                "FROM locations WHERE id IN (?, ?, ?)",
                (top_id, child_id, archived_id),
            ).fetchall()
        }
        stored_asset = connection.execute(
            "SELECT id, name, location_id, jarvis_code FROM assets WHERE id = ?",
            (asset_id,),
        ).fetchone()
        columns = {row[1] for row in connection.execute("PRAGMA table_info(locations)").fetchall()}
        connection.execute("PRAGMA foreign_keys=ON")
        foreign_key_violations = connection.execute("PRAGMA foreign_key_check").fetchall()

    assert len(roots) == 1
    root_id, root_name, root_type = roots[0]
    assert root_name == "Existing House"
    assert root_type == "building"
    assert rows[top_id] == ("Ground floor", "Existing top level", root_id, "area", None)
    assert rows[child_id] == ("Kitchen", "Existing child", top_id, "area", None)
    assert rows[archived_id] == (
        "Old shed",
        "Archived top level",
        root_id,
        "area",
        record[0],
    )
    assert stored_asset == (asset_id, "Existing oven", child_id, "DEV-001")
    assert "path" not in columns
    assert foreign_key_violations == []
