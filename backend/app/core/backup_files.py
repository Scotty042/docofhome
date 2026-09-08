"""Bounded, checksummed backup format shared by creation and restore."""

import hashlib
import json
import stat
import zipfile
from pathlib import PurePosixPath
from typing import Any

MAX_BACKUP_BYTES = 512 * 1024 * 1024


def allowed_file(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        bool(name)
        and "\\" not in name
        and not path.is_absolute()
        and all(part not in {"", ".", ".."} for part in name.split("/"))
        and (name == "backups/config.json" or (len(path.parts) > 1 and path.parts[0] == "uploads"))
    )


def validate_archive(archive: zipfile.ZipFile) -> dict[str, Any]:
    entries = archive.infolist()
    if len(entries) > 100000 or len({entry.filename for entry in entries}) != len(entries):
        raise ValueError("Backup contains duplicate or too many entries")
    if sum(entry.file_size for entry in entries) > MAX_BACKUP_BYTES:
        raise ValueError("Uncompressed backup exceeds the 512 MB limit")
    if any(stat.S_ISLNK(entry.external_attr >> 16) or entry.is_dir() for entry in entries):
        raise ValueError("Backup contains unsupported entries")
    if archive.getinfo("manifest.json").file_size > 8 * 1024 * 1024:
        raise ValueError("Backup manifest is too large")
    manifest = json.loads(archive.read("manifest.json"))
    if not isinstance(manifest, dict):
        raise ValueError("Backup manifest must be an object")
    version = manifest.get("format_version")
    if version not in {1, 2}:
        raise ValueError("Backup format version is not supported")
    files = manifest.get("files", {}) if version == 2 else {}
    if not isinstance(files, dict) or any(not allowed_file(name) for name in files):
        raise ValueError("Backup contains unsafe file paths")
    if {entry.filename for entry in entries} != {"database.sqlite3", "manifest.json", *files}:
        raise ValueError("Backup contains unexpected files")
    expected = {
        "database.sqlite3": {
            "sha256": manifest["database_sha256"],
            "size_bytes": manifest["database_size_bytes"],
        },
        **files,
    }
    for name, metadata in expected.items():
        digest = hashlib.sha256()
        size = 0
        with archive.open(name) as handle:
            while chunk := handle.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_BACKUP_BYTES:
                    raise ValueError("Backup member exceeds size limit")
                digest.update(chunk)
        if size != metadata["size_bytes"] or digest.hexdigest() != metadata["sha256"]:
            raise ValueError(f"Backup checksum or size mismatch: {name}")
    return manifest
