import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config

from app.core.settings import settings


def test_topology_migration_preserves_existing_data_and_downgrades(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
    command.upgrade(config, "0015")
    database_path = settings.database_path
    timestamp = "2026-07-22 14:00:00"
    asset_type_id = uuid4().hex
    source_id = uuid4().hex
    target_id = uuid4().hex
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "INSERT INTO asset_types "
            "(id, created_at, updated_at, deleted_at, name, code_prefix) "
            "VALUES (?, ?, ?, NULL, 'Electrical', 'ELE')",
            (asset_type_id, timestamp, timestamp),
        )
        for asset_id, name, code in (
            (source_id, "Grid", "ELE-001"),
            (target_id, "Meter", "ELE-002"),
        ):
            connection.execute(
                "INSERT INTO assets "
                "(id, created_at, updated_at, deleted_at, name, asset_type_id, "
                "status, jarvis_code) VALUES (?, ?, ?, NULL, ?, ?, 'active', ?)",
                (asset_id, timestamp, timestamp, name, asset_type_id, code),
            )
        connection.commit()

    command.upgrade(config, "head")
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "INSERT INTO electrical_connections "
            "(id, source_kind, source_id, target_kind, target_id, connection_type, "
            "phase_l1, phase_l2, phase_l3, neutral, protective_earth, created_at, "
            "updated_at, deleted_at) VALUES (?, 'asset', ?, 'asset', ?, 'cable', "
            "1, 1, 1, 1, 1, ?, ?, NULL)",
            (uuid4().hex, source_id, target_id, timestamp, timestamp),
        )
        connection.commit()
        assert connection.execute(
            "SELECT connection_type, phase_l1, phase_l2, phase_l3 FROM electrical_connections"
        ).fetchone() == ("cable", 1, 1, 1)

    command.downgrade(config, "0015")
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert "electrical_connections" not in tables
        assert connection.execute("SELECT COUNT(*) FROM assets").fetchone() == (2,)
