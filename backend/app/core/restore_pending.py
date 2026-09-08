import hashlib
import json
import logging
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from app.core.backup_files import validate_archive
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
    bundle = None
    manifest = None
    if metadata.get("bundle"):
        bundle = restore_dir / metadata["bundle"]
        if bundle.parent.resolve() != restore_dir.resolve() or bundle.is_symlink():
            raise RuntimeError("Unsafe restore bundle")
        with bundle.open("rb") as handle:
            if hashlib.file_digest(handle, "sha256").hexdigest() != metadata["sha256"]:
                raise RuntimeError("Restore bundle checksum mismatch")
        with zipfile.ZipFile(bundle) as archive:
            manifest = validate_archive(archive)
        with pending.open("rb") as handle:
            if hashlib.file_digest(handle, "sha256").hexdigest() != manifest["database_sha256"]:
                raise RuntimeError("Pending database checksum mismatch")
    _assert_integrity(pending)
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)

    safety_dir = settings.data_dir / "backups" / "pre-restore"
    safety_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    if settings.database_path.is_file():
        safety_copy = safety_dir / f"jarvis-before-restore-{stamp}.sqlite3"
        shutil.copy2(settings.database_path, safety_copy)

    replacement = settings.database_path.with_suffix(".restore.tmp")
    shutil.copy2(pending, replacement)
    _assert_integrity(replacement)
    if bundle and manifest:
        with tempfile.TemporaryDirectory(dir=restore_dir) as staging:
            with zipfile.ZipFile(bundle) as archive:
                for name in manifest.get("files", {}):
                    destination = settings.data_dir / name
                    if settings.data_dir.resolve() not in destination.resolve().parents:
                        raise RuntimeError("Unsafe restore target")
                    archive.extract(name, staging)
                for name in manifest.get("files", {}):
                    destination = settings.data_dir / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if destination.exists():
                        original = safety_dir / stamp / name
                        original.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(destination, original)
                    staged = destination.with_name(destination.name + ".restore.tmp")
                    shutil.copy2(Path(staging) / name, staged)
                    staged.replace(destination)
    replacement.replace(settings.database_path)
    pending.unlink()
    marker.unlink()
    if bundle:
        bundle.unlink()
    logger.info(
        "Applied scheduled restore from %s",
        metadata.get("filename", "unknown backup"),
    )
    return True


if __name__ == "__main__":
    apply_pending_restore()
