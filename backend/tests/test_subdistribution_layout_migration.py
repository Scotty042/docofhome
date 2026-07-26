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


def test_0030_allows_subdistribution_sections_and_round_trips(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = migration_config()
    command.upgrade(config, "0029")

    timestamp = "2026-07-24 08:00:00"
    asset_type_id = uuid4().hex
    main_asset_id = uuid4().hex
    sub_asset_id = uuid4().hex
    main_id = uuid4().hex
    sub_id = uuid4().hex

    with sqlite3.connect(settings.database_path) as connection:
        root = connection.execute(
            "SELECT id FROM locations WHERE parent_id IS NULL AND deleted_at IS NULL"
        ).fetchone()
        assert root is not None
        connection.execute(
            "INSERT INTO asset_types "
            "(id, created_at, updated_at, deleted_at, name, code_prefix, description, icon) "
            "VALUES (?, ?, ?, NULL, 'Electrical distribution', 'ELE', NULL, NULL)",
            (asset_type_id, timestamp, timestamp),
        )
        connection.executemany(
            "INSERT INTO assets "
            "(id, created_at, updated_at, deleted_at, name, jarvis_code, description, "
            "asset_type_id, product_id, location_id, serial_number, inventory_number, status) "
            "VALUES (?, ?, ?, NULL, ?, ?, NULL, ?, NULL, ?, NULL, NULL, 'active')",
            [
                (
                    main_asset_id,
                    timestamp,
                    timestamp,
                    "Main distribution",
                    "ELE-0001",
                    asset_type_id,
                    root[0],
                ),
                (
                    sub_asset_id,
                    timestamp,
                    timestamp,
                    "Subdistribution",
                    "ELE-0002",
                    asset_type_id,
                    root[0],
                ),
            ],
        )
        connection.executemany(
            "INSERT INTO electrical_components "
            "(id, asset_id, role, created_at, updated_at, deleted_at) "
            "VALUES (?, ?, 'distribution', ?, ?, NULL)",
            [
                (main_id, main_asset_id, timestamp, timestamp),
                (sub_id, sub_asset_id, timestamp, timestamp),
            ],
        )
        connection.execute(
            "INSERT INTO electrical_distributions "
            "(id, parent_distribution_id, distribution_type, layout_mode, designation, "
            "rows, modules_per_row, description, notes) "
            "VALUES (?, NULL, 'main', 'sections', 'HV', NULL, NULL, NULL, NULL)",
            (main_id,),
        )
        connection.execute(
            "INSERT INTO electrical_distributions "
            "(id, parent_distribution_id, distribution_type, layout_mode, designation, "
            "rows, modules_per_row, description, notes) "
            "VALUES (?, ?, 'sub', 'rows', 'UV', 3, 12, NULL, NULL)",
            (sub_id, main_id),
        )
        connection.commit()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "UPDATE electrical_distributions SET layout_mode='sections', "
                "rows=NULL, modules_per_row=NULL WHERE id=?",
                (sub_id,),
            )

    command.upgrade(config, "0030")
    with sqlite3.connect(settings.database_path) as connection:
        connection.execute(
            "UPDATE electrical_distributions SET layout_mode='sections', "
            "rows=NULL, modules_per_row=NULL WHERE id=?",
            (sub_id,),
        )
        connection.commit()
        table_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' "
            "AND name='electrical_distributions'"
        ).fetchone()
        assert table_sql is not None
        assert "ck_electrical_distributions_sub_rows_layout" not in table_sql[0]
        assert connection.execute(
            "SELECT layout_mode FROM electrical_distributions WHERE id=?",
            (sub_id,),
        ).fetchone() == ("sections",)

    command.downgrade(config, "0029")
    with sqlite3.connect(settings.database_path) as connection:
        table_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' "
            "AND name='electrical_distributions'"
        ).fetchone()
        assert table_sql is not None
        assert "ck_electrical_distributions_sub_rows_layout" in table_sql[0]
        assert connection.execute(
            "SELECT layout_mode FROM electrical_distributions WHERE id=?",
            (sub_id,),
        ).fetchone() == ("rows",)

    command.upgrade(config, "0030")
    with sqlite3.connect(settings.database_path) as connection:
        assert connection.execute(
            "SELECT designation FROM electrical_distributions WHERE id=?",
            (sub_id,),
        ).fetchone() == ("UV",)
