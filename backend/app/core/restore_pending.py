import json
import logging
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.core.settings import settings

logger = logging.getLogger(__name__)


def _assert_integrity(path: Path) -> None:
    connection = sqlite3.connect(path)
    try:
        result = connection.execute("PRAGMA integrity_check").fetchone()
    finally:
        connection.close()
    if result is None or result[0] != "ok":
        raise RuntimeError("Pending restore database failed SQLite integrity check")


def apply_pending_restore() -> bool:
    restore_dir = settings.data_dir / "restore"
    marker = restore_dir / "pending.json"
    pending = restore_dir / "pending.sqlite3"
    if not marker.is_file() and not pending.is_file():
        return False
    if not marker.is_file() or not pending.is_file():
        raise RuntimeError("Pending restore is incomplete")

    metadata = json.loads(marker.read_text(encoding="utf-8"))
    _assert_integrity(pending)
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)

    if settings.database_path.is_file():
        safety_dir = settings.data_dir / "backups" / "pre-restore"
        safety_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        safety_copy = safety_dir / f"jarvis-before-restore-{stamp}.sqlite3"
        shutil.copy2(settings.database_path, safety_copy)

    replacement = settings.database_path.with_suffix(".restore.tmp")
    shutil.copy2(pending, replacement)
    _assert_integrity(replacement)
    replacement.replace(settings.database_path)
    pending.unlink()
    marker.unlink()
    logger.info(
        "Applied scheduled restore from %s",
        metadata.get("filename", "unknown backup"),
    )
    return True


if __name__ == "__main__":
    apply_pending_restore()
