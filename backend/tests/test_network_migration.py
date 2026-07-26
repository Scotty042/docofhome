import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from app.core.settings import settings


def test_network_migration_upgrades_and_downgrades(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
    command.upgrade(config, "0021")
    command.upgrade(config, "0022")

    with sqlite3.connect(settings.database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert {
            "network_devices",
            "network_segments",
            "network_interfaces",
            "network_addresses",
            "network_connections",
        }.issubset(tables)
        indexes = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            ).fetchall()
        }
        assert "uq_network_devices_active_asset" in indexes
        assert "uq_network_connections_active_endpoints" in indexes

    command.downgrade(config, "0021")
    with sqlite3.connect(settings.database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert "network_devices" not in tables
