import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config

from app.core.settings import settings


def test_document_root_migration_preserves_nextcloud_configuration_and_downgrades(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
    command.upgrade(config, "0016")

    integration_id = uuid4().hex
    timestamp = "2026-07-22 12:00:00"
    with sqlite3.connect(settings.database_path) as connection:
        connection.execute(
            "INSERT INTO integration_settings "
            "(id, kind, enabled, base_url, account, secret, selected_album_id, "
            "created_at, updated_at) "
            "VALUES (?, 'nextcloud', 1, ?, ?, ?, NULL, ?, ?)",
            (
                integration_id,
                "https://nextcloud.example.test",
                "document-user",
                "secret",
                timestamp,
                timestamp,
            ),
        )
        connection.commit()

    command.upgrade(config, "head")
    with sqlite3.connect(settings.database_path) as connection:
        assert connection.execute(
            "SELECT document_root FROM integration_settings WHERE kind = 'nextcloud'"
        ).fetchone() == ("docofhome/Documents",)
        connection.execute(
            "UPDATE integration_settings SET document_root = ? WHERE kind = 'nextcloud'",
            ("Haus/Dokumente",),
        )
        connection.commit()

    command.downgrade(config, "0016")
    with sqlite3.connect(settings.database_path) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(integration_settings)")}
        assert "document_root" not in columns
        assert connection.execute(
            "SELECT base_url, account FROM integration_settings WHERE kind = 'nextcloud'"
        ).fetchone() == ("https://nextcloud.example.test", "document-user")
