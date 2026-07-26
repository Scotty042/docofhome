import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config

from app.core.settings import settings


def test_energy_migration_adds_balance_tables_and_multiple_incoming_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
    command.upgrade(config, "head")
    database_path = settings.database_path
    timestamp = "2026-07-23 12:00:00"
    asset_type_id = uuid4().hex
    source_one = uuid4().hex
    source_two = uuid4().hex
    target = uuid4().hex

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert {"energy_configurations", "energy_components"}.issubset(tables)
        assert connection.execute(
            "SELECT COUNT(*) FROM energy_configurations WHERE id = 1"
        ).fetchone() == (1,)
        connection.execute(
            "INSERT INTO asset_types "
            "(id, created_at, updated_at, deleted_at, name, code_prefix) "
            "VALUES (?, ?, ?, NULL, 'Electrical', 'ELE')",
            (asset_type_id, timestamp, timestamp),
        )
        for asset_id, name in (
            (source_one, "Grid"),
            (source_two, "PV"),
            (target, "House bus"),
        ):
            connection.execute(
                "INSERT INTO assets "
                "(id, created_at, updated_at, deleted_at, name, asset_type_id, "
                "status, jarvis_code) "
                "VALUES (?, ?, ?, NULL, ?, ?, 'active', ?)",
                (asset_id, timestamp, timestamp, name, asset_type_id, f"ELE-{asset_id[:4]}"),
            )
        for source in (source_one, source_two):
            connection.execute(
                "INSERT INTO electrical_connections "
                "(id, source_kind, source_id, target_kind, target_id, connection_type, "
                "phase_l1, phase_l2, phase_l3, neutral, protective_earth, "
                "created_at, updated_at, deleted_at) "
                "VALUES (?, 'asset', ?, 'asset', ?, 'wire', 1, 1, 1, 0, 0, ?, ?, NULL)",
                (uuid4().hex, source, target, timestamp, timestamp),
            )
        connection.commit()
        assert connection.execute(
            "SELECT COUNT(*) FROM electrical_connections WHERE target_id = ?",
            (target,),
        ).fetchone() == (2,)
