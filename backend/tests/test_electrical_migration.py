import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config

from app.core.settings import settings


def migration_config() -> Config:
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
    return config


def test_electrical_migration_preserves_existing_data_and_is_downgrade_safe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = migration_config()
    command.upgrade(config, "0006")

    room_id = uuid4().hex
    asset_type_id = uuid4().hex
    asset_id = uuid4().hex
    archived_asset_id = uuid4().hex
    record = ("2026-07-21 12:00:00", "2026-07-21 12:00:00")
    with sqlite3.connect(settings.database_path) as connection:
        root_row = connection.execute(
            "SELECT id FROM locations WHERE parent_id IS NULL AND deleted_at IS NULL"
        ).fetchone()
        assert root_row is not None
        root_id = root_row[0]
        connection.execute(
            "INSERT INTO asset_types "
            "(id, created_at, updated_at, deleted_at, name, code_prefix, description, icon) "
            "VALUES (?, ?, ?, NULL, ?, ?, NULL, NULL)",
            (asset_type_id, *record, "Electrical equipment", "ELE"),
        )
        connection.execute(
            "INSERT INTO locations "
            "(id, created_at, updated_at, deleted_at, name, location_type, description, "
            "parent_id, short_name, sort_order, notes) "
            "VALUES (?, ?, ?, NULL, ?, ?, NULL, ?, NULL, NULL, NULL)",
            (room_id, *record, "Electrical room", "room", root_id),
        )
        connection.executemany(
            "INSERT INTO assets "
            "(id, created_at, updated_at, deleted_at, name, jarvis_code, description, "
            "asset_type_id, product_id, location_id, serial_number, inventory_number, status) "
            "VALUES (?, ?, ?, ?, ?, ?, NULL, ?, NULL, ?, NULL, NULL, ?)",
            [
                (
                    asset_id,
                    *record,
                    None,
                    "Existing panel",
                    "ELE-001",
                    asset_type_id,
                    room_id,
                    "active",
                ),
                (
                    archived_asset_id,
                    *record,
                    record[0],
                    "Archived panel",
                    "ELE-002",
                    asset_type_id,
                    room_id,
                    "retired",
                ),
            ],
        )
        connection.commit()

    command.upgrade(config, "head")

    role_id = uuid4().hex
    with sqlite3.connect(settings.database_path) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        stored_assets = connection.execute(
            "SELECT id, name, jarvis_code, location_id, status, deleted_at "
            "FROM assets ORDER BY jarvis_code"
        ).fetchall()
        connection.execute(
            "INSERT INTO electrical_components "
            "(id, asset_id, role, created_at, updated_at, deleted_at) "
            "VALUES (?, ?, 'distribution', ?, ?, NULL)",
            (role_id, asset_id, *record),
        )
        connection.execute(
            "INSERT INTO electrical_distributions "
            "(id, parent_distribution_id, distribution_type, designation, rows, "
            "modules_per_row, description, notes) "
            "VALUES (?, NULL, 'main', 'HV', NULL, NULL, NULL, NULL)",
            (role_id,),
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO electrical_components "
                "(id, asset_id, role, created_at, updated_at, deleted_at) "
                "VALUES (?, ?, 'protective_device', ?, ?, NULL)",
                (uuid4().hex, asset_id, *record),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO electrical_components "
                "(id, asset_id, role, created_at, updated_at, deleted_at) "
                "VALUES (?, ?, 'distribution', ?, ?, NULL)",
                (uuid4().hex, uuid4().hex, *record),
            )
        connection.commit()
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()

    assert {
        "electrical_components",
        "electrical_distributions",
        "electrical_protective_devices",
    }.issubset(tables)
    assert stored_assets == [
        (asset_id, "Existing panel", "ELE-001", room_id, "active", None),
        (
            archived_asset_id,
            "Archived panel",
            "ELE-002",
            room_id,
            "retired",
            record[0],
        ),
    ]
    assert violations == []

    command.downgrade(config, "0006")
    with sqlite3.connect(settings.database_path) as connection:
        remaining_tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        remaining_assets = connection.execute(
            "SELECT id, name, jarvis_code FROM assets ORDER BY jarvis_code"
        ).fetchall()

    assert "electrical_components" not in remaining_tables
    assert "electrical_distributions" not in remaining_tables
    assert "electrical_protective_devices" not in remaining_tables
    assert remaining_assets == [
        (asset_id, "Existing panel", "ELE-001"),
        (archived_asset_id, "Archived panel", "ELE-002"),
    ]


def test_electrical_migration_upgrades_a_fresh_database_without_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = migration_config()

    command.upgrade(config, "head")
    command.check(config)

    with sqlite3.connect(settings.database_path) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        constraints = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' "
            "AND name='electrical_protective_devices'"
        ).fetchone()

    assert constraints is not None
    assert "ck_electrical_protective_devices_position_group" in constraints[0]
