import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from app.core.settings import settings


def _config() -> Config:
    backend_dir = Path(__file__).parents[1]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("script_location", str(backend_dir / "migrations"))
    return config


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}


def test_collected_integration_migration_upgrade_downgrade_and_reupgrade(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = _config()

    command.upgrade(config, "0027")
    command.upgrade(config, "0028")
    with sqlite3.connect(settings.database_path) as connection:
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert "electrical_meter_placements" in tables
        assert {
            "home_assistant_power_entity_id",
            "home_assistant_voltage_entity_id",
        }.issubset(_columns(connection, "consumption_meters"))
        assert "width" in _columns(connection, "electrical_distribution_areas")
        assert "logical_interface_id" in _columns(connection, "network_interfaces")
        area_sql = connection.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type = 'table' AND name = 'electrical_distribution_areas'"
        ).fetchone()[0]
        connection_sql = connection.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type = 'table' AND name = 'electrical_connections'"
        ).fetchone()[0]
        assert "neutral_rail" in area_sql
        assert "protective_earth_rail" in area_sql
        assert "grid_connection" in connection_sql

    command.downgrade(config, "0027")
    with sqlite3.connect(settings.database_path) as connection:
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert "electrical_meter_placements" not in tables
        assert "home_assistant_power_entity_id" not in _columns(
            connection, "consumption_meters"
        )
        assert "width" not in _columns(connection, "electrical_distribution_areas")
        assert "logical_interface_id" not in _columns(connection, "network_interfaces")

    command.upgrade(config, "head")
    with sqlite3.connect(settings.database_path) as connection:
        assert "electrical_meter_placements" in {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone() == ("0028",)
