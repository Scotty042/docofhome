import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config

from app.core.settings import settings


def test_integrity_migration_preserves_existing_uuids_and_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
    command.upgrade(config, "0004")

    asset_type_id = uuid4().hex
    asset_id = uuid4().hex
    label_id = uuid4().hex
    database_path = settings.database_path
    with sqlite3.connect(database_path) as connection:
        record = ("2026-07-20 12:00:00", "2026-07-20 12:00:00", None)
        connection.execute(
            "INSERT INTO asset_types "
            "(id, created_at, updated_at, deleted_at, name, description, icon) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (asset_type_id, *record, "Electrical Distribution", "Existing type", None),
        )
        connection.execute(
            "INSERT INTO assets "
            "(id, created_at, updated_at, deleted_at, name, description, asset_type_id, "
            "product_id, location_id, serial_number, inventory_number, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                asset_id,
                *record,
                "Existing panel",
                "Must survive",
                asset_type_id,
                None,
                None,
                "SERIAL-OLD",
                "INV-OLD",
                "active",
            ),
        )
        connection.execute(
            "INSERT INTO labels "
            "(id, created_at, updated_at, deleted_at, name, color) VALUES (?, ?, ?, ?, ?, ?)",
            (label_id, *record, " Existing Label ", "#336699"),
        )
        connection.commit()

    command.upgrade(config, "head")

    with sqlite3.connect(database_path) as connection:
        stored_type = connection.execute(
            "SELECT id, name, code_prefix FROM asset_types WHERE id = ?", (asset_type_id,)
        ).fetchone()
        stored_asset = connection.execute(
            "SELECT id, name, description, serial_number, inventory_number, jarvis_code "
            "FROM assets WHERE id = ?",
            (asset_id,),
        ).fetchone()
        stored_label = connection.execute(
            "SELECT id, name, normalized_name FROM labels WHERE id = ?", (label_id,)
        ).fetchone()

    assert stored_type == (asset_type_id, "Electrical Distribution", "EL-DIST")
    assert stored_asset == (
        asset_id,
        "Existing panel",
        "Must survive",
        "SERIAL-OLD",
        "INV-OLD",
        "EL-DIST-001",
    )
    assert stored_label == (label_id, " Existing Label ", "existing label")
