import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config

from app.core.settings import settings


def test_circuit_asset_migration_preserves_existing_data_and_downgrades(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
    command.upgrade(config, "0014")

    database_path = settings.database_path
    asset_type_id = uuid4().hex
    distribution_asset_id = uuid4().hex
    assigned_asset_id = uuid4().hex
    distribution_id = uuid4().hex
    circuit_id = uuid4().hex
    link_id = uuid4().hex
    timestamp = "2026-07-22 12:00:00"
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            "INSERT INTO asset_types "
            "(id, created_at, updated_at, deleted_at, name, code_prefix) "
            "VALUES (?, ?, ?, NULL, 'Electrical', 'ELE')",
            (asset_type_id, timestamp, timestamp),
        )
        for asset_id, name, code in (
            (distribution_asset_id, "Main distribution", "ELE-001"),
            (assigned_asset_id, "Dishwasher", "ELE-002"),
        ):
            connection.execute(
                "INSERT INTO assets "
                "(id, created_at, updated_at, deleted_at, name, asset_type_id, "
                "status, jarvis_code) VALUES (?, ?, ?, NULL, ?, ?, 'active', ?)",
                (asset_id, timestamp, timestamp, name, asset_type_id, code),
            )
        connection.execute(
            "INSERT INTO electrical_components "
            "(id, asset_id, role, created_at, updated_at, deleted_at) "
            "VALUES (?, ?, 'distribution', ?, ?, NULL)",
            (distribution_id, distribution_asset_id, timestamp, timestamp),
        )
        connection.execute(
            "INSERT INTO electrical_distributions "
            "(id, parent_distribution_id, distribution_type, layout_mode, designation) "
            "VALUES (?, NULL, 'main', 'rows', 'HV')",
            (distribution_id,),
        )
        connection.execute(
            "INSERT INTO electrical_circuits "
            "(id, distribution_id, protective_device_id, name, circuit_number, "
            "description, notes, created_at, updated_at, deleted_at) "
            "VALUES (?, ?, NULL, 'Kitchen', 'F1', NULL, NULL, ?, ?, NULL)",
            (circuit_id, distribution_id, timestamp, timestamp),
        )
        connection.commit()

    command.upgrade(config, "head")
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            "INSERT INTO electrical_circuit_asset_links "
            "(id, circuit_id, asset_id, created_at, updated_at, deleted_at) "
            "VALUES (?, ?, ?, ?, ?, NULL)",
            (link_id, circuit_id, assigned_asset_id, timestamp, timestamp),
        )
        connection.commit()
        assert connection.execute(
            "SELECT circuit_id, asset_id FROM electrical_circuit_asset_links"
        ).fetchone() == (circuit_id, assigned_asset_id)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    command.downgrade(config, "0014")
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert "electrical_circuit_asset_links" not in tables
        assert connection.execute("SELECT name FROM electrical_circuits").fetchone() == ("Kitchen",)
