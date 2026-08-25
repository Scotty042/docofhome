import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config

from app.core.settings import settings


def test_circuit_migration_preserves_electrical_data_and_downgrades(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
    command.upgrade(config, "0012")

    database_path = settings.database_path
    asset_type_id = uuid4().hex
    asset_id = uuid4().hex
    component_id = uuid4().hex
    timestamp = "2026-07-22 08:00:00"
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            "INSERT INTO asset_types "
            "(id, created_at, updated_at, deleted_at, name, code_prefix) "
            "VALUES (?, ?, ?, NULL, ?, ?)",
            (asset_type_id, timestamp, timestamp, "Distribution", "DIS"),
        )
        connection.execute(
            "INSERT INTO assets "
            "(id, created_at, updated_at, deleted_at, name, asset_type_id, status, jarvis_code) "
            "VALUES (?, ?, ?, NULL, ?, ?, ?, ?)",
            (
                asset_id,
                timestamp,
                timestamp,
                "Existing distribution",
                asset_type_id,
                "active",
                "DIS-001",
            ),
        )
        connection.execute(
            "INSERT INTO electrical_components "
            "(id, asset_id, role, created_at, updated_at, deleted_at) "
            "VALUES (?, ?, 'distribution', ?, ?, NULL)",
            (component_id, asset_id, timestamp, timestamp),
        )
        connection.execute(
            "INSERT INTO electrical_distributions "
            "(id, parent_distribution_id, distribution_type, layout_mode, designation) "
            "VALUES (?, NULL, 'main', 'rows', 'HV')",
            (component_id,),
        )
        connection.commit()

    command.upgrade(config, "head")
    circuit_id = uuid4().hex
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            "INSERT INTO electrical_circuits "
            "(id, distribution_id, protective_device_id, name, circuit_number, "
            "description, notes, created_at, updated_at, deleted_at) "
            "VALUES (?, ?, NULL, 'Kitchen', 'F1', NULL, NULL, ?, ?, NULL)",
            (circuit_id, component_id, timestamp, timestamp),
        )
        connection.commit()
        assert connection.execute(
            "SELECT name, circuit_number FROM electrical_circuits"
        ).fetchone() == ("Kitchen", "F1")
        assert connection.execute(
            "SELECT designation FROM electrical_distributions"
        ).fetchone() == ("HV",)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    command.downgrade(config, "0012")
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert "electrical_circuits" not in tables
        assert connection.execute(
            "SELECT designation FROM electrical_distributions"
        ).fetchone() == ("HV",)
