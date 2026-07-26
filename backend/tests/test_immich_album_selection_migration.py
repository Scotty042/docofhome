import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config

from app.core.settings import settings


def test_immich_album_selection_migration_preserves_integration_and_downgrades(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
    command.upgrade(config, "0013")

    integration_id = uuid4().hex
    album_id = str(uuid4())
    timestamp = "2026-07-22 12:00:00"
    with sqlite3.connect(settings.database_path) as connection:
        connection.execute(
            "INSERT INTO integration_settings "
            "(id, kind, enabled, base_url, account, secret, created_at, updated_at) "
            "VALUES (?, 'immich', 1, ?, NULL, ?, ?, ?)",
            (integration_id, "https://immich.example.test", "secret", timestamp, timestamp),
        )
        connection.commit()

    command.upgrade(config, "head")
    with sqlite3.connect(settings.database_path) as connection:
        connection.execute(
            "UPDATE integration_settings SET selected_album_id = ? WHERE kind = 'immich'",
            (album_id,),
        )
        connection.commit()
        assert connection.execute(
            "SELECT selected_album_id FROM integration_settings WHERE kind = 'immich'"
        ).fetchone() == (album_id,)

    command.downgrade(config, "0013")
    with sqlite3.connect(settings.database_path) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(integration_settings)")}
        assert "selected_album_id" not in columns
        assert connection.execute(
            "SELECT base_url FROM integration_settings WHERE kind = 'immich'"
        ).fetchone() == ("https://immich.example.test",)
