import hashlib
import json
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
from xml.etree import ElementTree

import httpx
from sqlmodel import Session

from app.core.settings import settings
from app.repositories.settings import SettingsRepository
from app.schemas.backups import BackupRecord, RemoteBackupRecord

MAX_IMPORT_BYTES = 512 * 1024 * 1024
DAV_NAMESPACE = "{DAV:}"


class BackupError(RuntimeError):
    """Raised when a backup cannot be created, validated, uploaded, or restored."""


class BackupService:
    def __init__(
        self,
        session: Session,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.session = session
        self.transport = transport
        self.backup_dir = settings.data_dir / "backups"
        self.restore_dir = settings.data_dir / "restore"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.restore_dir.mkdir(parents=True, exist_ok=True)

    def list_backups(self) -> list[BackupRecord]:
        records: list[BackupRecord] = []
        for path in sorted(self.backup_dir.glob("tectoryn-backup-*.zip"), reverse=True):
            try:
                records.append(self._record_from_archive(path))
            except (BackupError, OSError, zipfile.BadZipFile, json.JSONDecodeError):
                continue
        return records

    def create_backup(
        self,
        *,
        upload_to_nextcloud: bool = False,
        nextcloud_folder: str = "DocOfHome/Backups",
    ) -> BackupRecord:
        if not settings.database_path.is_file():
            raise BackupError("Database file does not exist")

        created_at = datetime.now(UTC)
        stamp = created_at.strftime("%Y%m%dT%H%M%S%fZ")
        filename = f"tectoryn-backup-{stamp}.zip"
        archive_path = self.backup_dir / filename

        with tempfile.TemporaryDirectory(dir=self.backup_dir) as temp_dir:
            snapshot_path = Path(temp_dir) / "database.sqlite3"
            self._snapshot_database(snapshot_path)
            database_sha = self._sha256(snapshot_path)
            manifest = {
                "format_version": 1,
                "created_at": created_at.isoformat(),
                "app_version": settings.app_version,
                "database_filename": "database.sqlite3",
                "database_size_bytes": snapshot_path.stat().st_size,
                "database_sha256": database_sha,
            }
            temp_archive = Path(temp_dir) / filename
            with zipfile.ZipFile(
                temp_archive,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as archive:
                archive.write(snapshot_path, "database.sqlite3")
                archive.writestr(
                    "manifest.json",
                    json.dumps(manifest, ensure_ascii=False, indent=2),
                )
            shutil.move(temp_archive, archive_path)

        record = self._record_from_archive(archive_path)
        if upload_to_nextcloud:
            self.upload_to_nextcloud(archive_path, nextcloud_folder)
            record.nextcloud_uploaded = True
        return record

    def import_backup(self, content: bytes) -> BackupRecord:
        if not content:
            raise BackupError("Backup upload is empty")
        if len(content) > MAX_IMPORT_BYTES:
            raise BackupError("Backup upload exceeds the 512 MB limit")

        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        filename = f"tectoryn-backup-{stamp}.zip"
        target = self.backup_dir / filename
        with tempfile.TemporaryDirectory(dir=self.backup_dir) as temp_dir:
            temporary = Path(temp_dir) / filename
            temporary.write_bytes(content)
            self._validate_archive_path(temporary)
            shutil.move(temporary, target)
        return self._record_from_archive(target)

    def validate_backup(self, filename: str) -> BackupRecord:
        archive_path = self.archive_path(filename)
        self._validate_archive_path(archive_path)
        return self._record_from_archive(archive_path)

    def archive_path(self, filename: str) -> Path:
        """Return a validated local archive path suitable for read-only download."""
        return self._safe_archive_path(filename)

    def delete_backup(self, filename: str) -> None:
        """Delete one local archive after validating its constrained filename and path."""
        archive_path = self._safe_archive_path(filename)
        pending_marker = self.restore_dir / "pending.json"
        if pending_marker.is_file():
            try:
                pending = json.loads(pending_marker.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pending = {}
            if pending.get("filename") == filename:
                raise BackupError("A backup scheduled for restore cannot be deleted")
        try:
            archive_path.unlink()
        except OSError as exc:
            raise BackupError("Backup file could not be deleted") from exc

    def schedule_restore(self, filename: str) -> None:
        record = self.validate_backup(filename)
        archive_path = self._safe_archive_path(filename)
        pending_database = self.restore_dir / "pending.sqlite3"
        pending_marker = self.restore_dir / "pending.json"
        with tempfile.TemporaryDirectory(dir=self.restore_dir) as temp_dir:
            extracted = Path(temp_dir) / "database.sqlite3"
            with zipfile.ZipFile(archive_path) as archive:
                archive.extract("database.sqlite3", temp_dir)
            shutil.copy2(extracted, pending_database)
        pending_marker.write_text(
            json.dumps(
                {
                    "filename": record.filename,
                    "sha256": record.sha256,
                    "scheduled_at": datetime.now(UTC).isoformat(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def upload_to_nextcloud(self, archive_path: Path, folder: str) -> None:
        folder_url, auth = self._nextcloud_folder_url(folder)
        current = folder_url.rsplit("/", len(self._clean_folder_parts(folder)))[0]
        try:
            with self._nextcloud_client(auth) as client:
                for part in self._clean_folder_parts(folder):
                    current = f"{current}/{quote(part, safe='')}"
                    response = client.request("MKCOL", current)
                    if response.status_code not in {201, 405}:
                        raise BackupError(
                            f"Nextcloud folder could not be created ({response.status_code})"
                        )
                target = f"{current}/{quote(archive_path.name, safe='')}"
                with archive_path.open("rb") as handle:
                    response = client.put(target, content=handle)
                if response.status_code not in {200, 201, 204}:
                    raise BackupError(f"Nextcloud upload failed ({response.status_code})")
        except httpx.HTTPError as exc:
            raise BackupError("Nextcloud could not be reached") from exc

    def list_nextcloud_backups(self, folder: str) -> list[RemoteBackupRecord]:
        folder_url, auth = self._nextcloud_folder_url(folder)
        request_body = (
            '<?xml version="1.0" encoding="utf-8" ?>'
            '<d:propfind xmlns:d="DAV:"><d:prop>'
            "<d:resourcetype/><d:getcontentlength/><d:getlastmodified/>"
            "</d:prop></d:propfind>"
        )
        try:
            with self._nextcloud_client(auth) as client:
                response = client.request(
                    "PROPFIND",
                    folder_url,
                    headers={"Depth": "1", "Content-Type": "application/xml"},
                    content=request_body,
                )
        except httpx.HTTPError as exc:
            raise BackupError("Nextcloud could not be reached") from exc
        if response.status_code == 404:
            return []
        if response.status_code != 207:
            raise BackupError(f"Nextcloud backup list could not be loaded ({response.status_code})")

        try:
            root = ElementTree.fromstring(response.content)
        except ElementTree.ParseError as exc:
            raise BackupError("Nextcloud returned an invalid WebDAV response") from exc

        records: list[RemoteBackupRecord] = []
        for item in root.findall(f"{DAV_NAMESPACE}response"):
            href = item.findtext(f"{DAV_NAMESPACE}href") or ""
            filename = Path(unquote(urlsplit(href).path).rstrip("/")).name
            if not self._is_backup_filename(filename):
                continue
            properties = item.find(f".//{DAV_NAMESPACE}prop")
            if properties is None:
                continue
            resource_type = properties.find(f"{DAV_NAMESPACE}resourcetype")
            if (
                resource_type is not None
                and resource_type.find(f"{DAV_NAMESPACE}collection") is not None
            ):
                continue
            size_text = properties.findtext(f"{DAV_NAMESPACE}getcontentlength") or "0"
            modified_text = properties.findtext(f"{DAV_NAMESPACE}getlastmodified")
            try:
                size_bytes = max(0, int(size_text))
            except ValueError:
                size_bytes = 0
            modified_at = None
            if modified_text:
                try:
                    modified_at = parsedate_to_datetime(modified_text)
                except (TypeError, ValueError):
                    modified_at = None
            records.append(
                RemoteBackupRecord(
                    filename=filename,
                    size_bytes=size_bytes,
                    modified_at=modified_at,
                    local_available=(self.backup_dir / filename).is_file(),
                )
            )
        return sorted(records, key=lambda record: record.filename, reverse=True)

    def import_from_nextcloud(self, filename: str, folder: str) -> BackupRecord:
        self._validate_filename(filename)
        local_path = self.backup_dir / filename
        if local_path.is_file():
            self._validate_archive_path(local_path)
            return self._record_from_archive(local_path)

        folder_url, auth = self._nextcloud_folder_url(folder)
        remote_url = f"{folder_url}/{quote(filename, safe='')}"
        with tempfile.TemporaryDirectory(dir=self.backup_dir) as temp_dir:
            temporary = Path(temp_dir) / filename
            try:
                with self._nextcloud_client(auth) as client:
                    with client.stream("GET", remote_url) as response:
                        if response.status_code != 200:
                            raise BackupError(
                                f"Nextcloud backup could not be downloaded ({response.status_code})"
                            )
                        content_length = response.headers.get("content-length")
                        if content_length and int(content_length) > MAX_IMPORT_BYTES:
                            raise BackupError("Remote backup exceeds the 512 MB limit")
                        total = 0
                        with temporary.open("wb") as handle:
                            for chunk in response.iter_bytes():
                                total += len(chunk)
                                if total > MAX_IMPORT_BYTES:
                                    raise BackupError("Remote backup exceeds the 512 MB limit")
                                handle.write(chunk)
            except httpx.HTTPError as exc:
                raise BackupError("Nextcloud could not be reached") from exc
            self._validate_archive_path(temporary)
            shutil.move(temporary, local_path)
        return self._record_from_archive(local_path)

    def delete_from_nextcloud(self, filename: str, folder: str) -> None:
        self._validate_filename(filename)
        folder_url, auth = self._nextcloud_folder_url(folder)
        remote_url = f"{folder_url}/{quote(filename, safe='')}"
        try:
            with self._nextcloud_client(auth) as client:
                response = client.delete(remote_url)
        except httpx.HTTPError as exc:
            raise BackupError("Nextcloud could not be reached") from exc
        if response.status_code not in {200, 204}:
            raise BackupError(f"Nextcloud backup could not be deleted ({response.status_code})")

    def _nextcloud_folder_url(self, folder: str) -> tuple[str, tuple[str, str]]:
        integration = SettingsRepository(self.session).get_integration("nextcloud")
        if (
            integration is None
            or not integration.enabled
            or not integration.base_url
            or not integration.account
            or not integration.secret
        ):
            raise BackupError("Nextcloud integration is not fully configured")
        parts = self._clean_folder_parts(folder)
        root = (
            f"{integration.base_url.rstrip('/')}/remote.php/dav/files/"
            f"{quote(integration.account, safe='')}"
        )
        suffix = "/".join(quote(part, safe="") for part in parts)
        return f"{root}/{suffix}", (integration.account, integration.secret)

    def _nextcloud_client(self, auth: tuple[str, str]) -> httpx.Client:
        return httpx.Client(
            timeout=30.0,
            follow_redirects=False,
            auth=auth,
            transport=self.transport,
        )

    @staticmethod
    def _clean_folder_parts(folder: str) -> list[str]:
        parts = [part for part in folder.strip("/").split("/") if part]
        if not parts or any(part in {".", ".."} for part in parts):
            raise BackupError("Nextcloud folder is invalid")
        return parts

    def _validate_archive_path(self, path: Path) -> None:
        try:
            record = self._record_from_archive(path)
            with tempfile.TemporaryDirectory(dir=self.restore_dir) as temp_dir:
                database_path = Path(temp_dir) / "database.sqlite3"
                with zipfile.ZipFile(path) as archive:
                    names = set(archive.namelist())
                    if names != {"database.sqlite3", "manifest.json"}:
                        raise BackupError("Backup archive contains unexpected files")
                    archive.extract("database.sqlite3", temp_dir)
                self._assert_integrity(database_path)
                extracted_size = database_path.stat().st_size
            if record.database_size_bytes != extracted_size:
                raise BackupError("Database size does not match the manifest")
        except (zipfile.BadZipFile, json.JSONDecodeError, KeyError, ValueError) as exc:
            raise BackupError("Backup archive is invalid") from exc

    def _record_from_archive(self, path: Path) -> BackupRecord:
        with zipfile.ZipFile(path) as archive:
            try:
                manifest = json.loads(archive.read("manifest.json"))
                database_bytes = archive.read("database.sqlite3")
            except KeyError as exc:
                raise BackupError("Backup archive is incomplete") from exc
        if manifest.get("format_version") != 1:
            raise BackupError("Backup format version is not supported")
        database_sha = hashlib.sha256(database_bytes).hexdigest()
        if database_sha != manifest.get("database_sha256"):
            raise BackupError("Database checksum does not match the manifest")
        return BackupRecord(
            filename=path.name,
            created_at=datetime.fromisoformat(manifest["created_at"]),
            size_bytes=path.stat().st_size,
            sha256=self._sha256(path),
            database_size_bytes=int(manifest["database_size_bytes"]),
            app_version=str(manifest["app_version"]),
        )

    def _safe_archive_path(self, filename: str) -> Path:
        self._validate_filename(filename)
        path = (self.backup_dir / filename).resolve()
        if path.parent != self.backup_dir.resolve() or not path.is_file():
            raise BackupError("Backup file was not found")
        return path

    @staticmethod
    def _is_backup_filename(filename: str) -> bool:
        return (
            Path(filename).name == filename
            and filename.startswith("tectoryn-backup-")
            and filename.endswith(".zip")
        )

    @classmethod
    def _validate_filename(cls, filename: str) -> None:
        if not cls._is_backup_filename(filename):
            raise BackupError("Invalid backup filename")

    @staticmethod
    def _snapshot_database(destination: Path) -> None:
        source = sqlite3.connect(settings.database_path)
        target = sqlite3.connect(destination)
        try:
            source.backup(target)
        finally:
            target.close()
            source.close()
        BackupService._assert_integrity(destination)

    @staticmethod
    def _assert_integrity(database_path: Path) -> None:
        connection = sqlite3.connect(database_path)
        try:
            result = connection.execute("PRAGMA integrity_check").fetchone()
        finally:
            connection.close()
        if result is None or result[0] != "ok":
            raise BackupError("SQLite integrity check failed")

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
