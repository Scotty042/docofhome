from __future__ import annotations

import re
from collections import deque
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx
from sqlmodel import Session

from app.connectors.nextcloud import (
    NextcloudConnectorError,
    NextcloudResponseError,
    NextcloudWebDavConnector,
)
from app.repositories.settings import SettingsRepository
from app.schemas.documents import (
    DocumentDownload,
    DocumentEntry,
    DocumentEntryType,
    DocumentListRead,
    DocumentMutationRead,
)

DAV_NAMESPACE = "{DAV:}"
MAX_DOCUMENT_BYTES = 100 * 1024 * 1024
CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")
MEDIA_TYPE = re.compile(r"^[A-Za-z0-9!#$&^_.+\-]+/[A-Za-z0-9!#$&^_.+\-]+$")


class DocumentError(RuntimeError):
    """Base class for safe document-management failures."""


class DocumentConfigurationError(DocumentError):
    """Raised when Nextcloud document storage is not configured."""


class DocumentValidationError(DocumentError):
    """Raised for unsafe or invalid relative paths and names."""


class DocumentNotFoundError(DocumentError):
    """Raised when a requested remote entry is missing."""


class DocumentConflictError(DocumentError):
    """Raised when a safe mutation would overwrite or recursively remove content."""


class DocumentTooLargeError(DocumentError):
    """Raised when an upload or download exceeds the bounded document limit."""


class DocumentRemoteError(DocumentError):
    """Raised when Nextcloud is unavailable or returns an unexpected response."""


class DocumentService:
    """Manage files below one configured Nextcloud folder without exposing credentials."""

    def __init__(
        self,
        session: Session,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.session = session
        self.transport = transport

    def list_entries(self, path: str = "") -> DocumentListRead:
        connector, root_parts, root_path = self._connection()
        relative_parts = self._clean_path(path)
        try:
            payload = connector.propfind([*root_parts, *relative_parts], depth=1)
        except (NextcloudConnectorError, NextcloudResponseError) as exc:
            raise self._remote_error(exc) from exc
        if payload is None:
            if not relative_parts:
                return DocumentListRead(
                    path="",
                    root_path=root_path,
                    root_exists=False,
                    items=[],
                )
            raise DocumentNotFoundError("Document folder was not found")
        entries = self._parse_multistatus(
            connector,
            payload,
            root_parts=root_parts,
            parent_relative_parts=relative_parts,
        )
        return DocumentListRead(
            path="/".join(relative_parts),
            root_path=root_path,
            root_exists=True,
            items=entries,
        )

    def create_folder(self, parent_path: str, name: str) -> DocumentMutationRead:
        connector, root_parts, _ = self._connection()
        parent_parts = self._clean_path(parent_path)
        folder_name = self._clean_name(name)
        self._ensure_root(connector, root_parts)
        self._ensure_existing_folder(connector, root_parts, parent_parts)
        target = [*root_parts, *parent_parts, folder_name]
        try:
            created = connector.create_collection(target)
        except NextcloudResponseError as exc:
            if exc.status_code in {405, 409, 412}:
                raise DocumentConflictError(
                    "A document entry with this name already exists"
                ) from exc
            raise self._remote_error(exc) from exc
        except NextcloudConnectorError as exc:
            raise self._remote_error(exc) from exc
        if not created:
            raise DocumentConflictError("A document entry with this name already exists")
        return DocumentMutationRead(
            item=self._entry(
                name=folder_name,
                path_parts=[*parent_parts, folder_name],
                entry_type=DocumentEntryType.FOLDER,
            ),
            created=True,
        )

    def upload(
        self,
        folder_path: str,
        filename: str,
        content: bytes,
        *,
        content_type: str,
        overwrite: bool,
    ) -> DocumentMutationRead:
        if len(content) > MAX_DOCUMENT_BYTES:
            raise DocumentTooLargeError("Document exceeds the 100 MB upload limit")
        connector, root_parts, _ = self._connection()
        folder_parts = self._clean_path(folder_path)
        safe_name = self._clean_name(filename)
        safe_content_type = self._normalize_content_type(content_type)
        self._ensure_root(connector, root_parts)
        self._ensure_existing_folder(connector, root_parts, folder_parts)
        try:
            status_code = connector.upload(
                [*root_parts, *folder_parts, safe_name],
                content=content,
                content_type=safe_content_type,
                overwrite=overwrite,
            )
        except NextcloudResponseError as exc:
            if exc.status_code in {409, 412}:
                raise DocumentConflictError("A document with this name already exists") from exc
            if exc.status_code == 413:
                raise DocumentTooLargeError("Document exceeds the Nextcloud upload limit") from exc
            raise self._remote_error(exc) from exc
        except NextcloudConnectorError as exc:
            raise self._remote_error(exc) from exc
        return DocumentMutationRead(
            item=self._entry(
                name=safe_name,
                path_parts=[*folder_parts, safe_name],
                entry_type=DocumentEntryType.FILE,
                size_bytes=len(content),
                content_type=safe_content_type,
                modified_at=datetime.now(UTC),
            ),
            created=status_code == 201,
            overwritten=overwrite and status_code in {200, 204},
        )

    def download(self, path: str) -> DocumentDownload:
        connector, root_parts, _ = self._connection()
        relative_parts = self._clean_path(path, allow_empty=False)
        entry = self._read_entry(connector, root_parts, relative_parts)
        if entry.entry_type == DocumentEntryType.FOLDER:
            raise DocumentValidationError("Folders cannot be downloaded as files")
        try:
            content, content_type, etag = connector.download(
                [*root_parts, *relative_parts],
                max_bytes=MAX_DOCUMENT_BYTES,
            )
        except NextcloudResponseError as exc:
            if exc.status_code == 404:
                raise DocumentNotFoundError("Document was not found") from exc
            if exc.status_code == 413:
                raise DocumentTooLargeError("Document exceeds the 100 MB download limit") from exc
            raise self._remote_error(exc) from exc
        except NextcloudConnectorError as exc:
            raise self._remote_error(exc) from exc
        return DocumentDownload(
            filename=relative_parts[-1],
            content=content,
            content_type=self._normalize_content_type(content_type),
            etag=self._sanitize_etag(etag),
        )

    def delete(self, path: str) -> None:
        connector, root_parts, _ = self._connection()
        relative_parts = self._clean_path(path, allow_empty=False)
        entry = self._read_entry(connector, root_parts, relative_parts)
        if entry.entry_type == DocumentEntryType.FOLDER:
            # Nextcloud installations commonly omit getetag for collections. Verify the
            # folder twice immediately before DELETE and use an ETag only when one is
            # actually available. This keeps non-empty folders protected while allowing
            # legitimately empty folders to be removed on those installations.
            for _ in range(2):
                listing = self.list_entries("/".join(relative_parts))
                if listing.items:
                    raise DocumentConflictError("Only empty document folders can be deleted")
            entry = self._read_entry(connector, root_parts, relative_parts)
        try:
            connector.delete([*root_parts, *relative_parts], etag=entry.etag)
        except NextcloudResponseError as exc:
            if exc.status_code == 404:
                raise DocumentNotFoundError("Document entry was not found") from exc
            if exc.status_code in {409, 412}:
                raise DocumentConflictError("Document entry could not be deleted safely") from exc
            raise self._remote_error(exc) from exc
        except NextcloudConnectorError as exc:
            raise self._remote_error(exc) from exc

    def search_entries(
        self,
        query: str,
        *,
        limit: int = 5,
        max_entries: int = 500,
        max_folders: int = 100,
    ) -> list[DocumentEntry]:
        normalized_query = query.strip().casefold()
        if len(normalized_query) < 2:
            raise DocumentValidationError("Document search requires at least two characters")
        if limit < 1 or max_entries < 1 or max_folders < 1:
            raise DocumentValidationError("Document search bounds are invalid")

        queue: deque[str] = deque([""])
        visited_folders = 0
        visited_entries = 0
        matches: list[tuple[int, str, DocumentEntry]] = []

        while queue and visited_folders < max_folders and visited_entries < max_entries:
            folder_path = queue.popleft()
            visited_folders += 1
            listing = self.list_entries(folder_path)
            if not listing.root_exists:
                break
            for entry in listing.items:
                visited_entries += 1
                if entry.entry_type == DocumentEntryType.FOLDER and (
                    visited_folders + len(queue) < max_folders
                ):
                    queue.append(entry.path)

                name = entry.name.casefold()
                path = entry.path.casefold()
                content_type = (entry.content_type or "").casefold()
                if (
                    normalized_query not in name
                    and normalized_query not in path
                    and (normalized_query not in content_type)
                ):
                    if visited_entries >= max_entries:
                        break
                    continue

                if name == normalized_query:
                    rank = 0
                elif name.startswith(normalized_query):
                    rank = 1
                elif normalized_query in name:
                    rank = 2
                elif normalized_query in path:
                    rank = 3
                else:
                    rank = 4
                matches.append((rank, entry.path.casefold(), entry))
                if visited_entries >= max_entries:
                    break

        matches.sort(key=lambda item: (item[0], item[1]))
        return [entry for _, _, entry in matches[:limit]]

    def move(self, source_path: str, target_parent_path: str, name: str) -> DocumentMutationRead:
        connector, root_parts, _ = self._connection()
        source_parts = self._clean_path(source_path, allow_empty=False)
        target_parent = self._clean_path(target_parent_path)
        target_name = self._clean_name(name)
        source_entry = self._read_entry(connector, root_parts, source_parts)
        self._ensure_existing_folder(connector, root_parts, target_parent)
        if source_entry.entry_type == DocumentEntryType.FOLDER:
            if target_parent[: len(source_parts)] == source_parts:
                raise DocumentValidationError("A folder cannot be moved into itself")
        target_parts = [*target_parent, target_name]
        if source_parts == target_parts:
            return DocumentMutationRead(item=source_entry)
        try:
            connector.move(
                [*root_parts, *source_parts],
                [*root_parts, *target_parts],
            )
        except NextcloudResponseError as exc:
            if exc.status_code == 404:
                raise DocumentNotFoundError("Source document entry was not found") from exc
            if exc.status_code in {409, 412}:
                raise DocumentConflictError("The destination already exists or is invalid") from exc
            raise self._remote_error(exc) from exc
        except NextcloudConnectorError as exc:
            raise self._remote_error(exc) from exc
        return DocumentMutationRead(
            item=source_entry.model_copy(
                update={"name": target_name, "path": "/".join(target_parts)}
            )
        )

    def _connection(self) -> tuple[NextcloudWebDavConnector, list[str], str]:
        integration = SettingsRepository(self.session).get_integration("nextcloud")
        if integration is None or not integration.enabled:
            raise DocumentConfigurationError(
                "Nextcloud integration is not fully configured or enabled"
            )
        base_url = integration.base_url
        account = integration.account
        secret = integration.secret
        if not base_url or not account or not secret:
            raise DocumentConfigurationError(
                "Nextcloud integration is not fully configured or enabled"
            )
        root_path = integration.document_root or "docofhome/Documents"
        root_parts = self._clean_path(root_path, allow_empty=False)
        try:
            connector = NextcloudWebDavConnector(
                base_url=base_url,
                account=account,
                secret=secret,
                transport=self.transport,
            )
        except ValueError as exc:
            raise DocumentConfigurationError("Nextcloud configuration is invalid") from exc
        return connector, root_parts, "/".join(root_parts)

    def _ensure_root(
        self,
        connector: NextcloudWebDavConnector,
        root_parts: list[str],
    ) -> None:
        current: list[str] = []
        try:
            for part in root_parts:
                current.append(part)
                connector.create_collection(current)
        except NextcloudResponseError as exc:
            if exc.status_code in {409, 412}:
                raise DocumentConflictError(
                    "The configured document root cannot be created"
                ) from exc
            raise self._remote_error(exc) from exc
        except NextcloudConnectorError as exc:
            raise self._remote_error(exc) from exc

    def _ensure_existing_folder(
        self,
        connector: NextcloudWebDavConnector,
        root_parts: list[str],
        relative_parts: list[str],
    ) -> None:
        entry = self._read_entry(connector, root_parts, relative_parts, allow_root=True)
        if entry.entry_type != DocumentEntryType.FOLDER:
            raise DocumentValidationError("The target path is not a folder")

    def _read_entry(
        self,
        connector: NextcloudWebDavConnector,
        root_parts: list[str],
        relative_parts: list[str],
        *,
        allow_root: bool = False,
    ) -> DocumentEntry:
        if not relative_parts and not allow_root:
            raise DocumentValidationError("The managed document root cannot be changed")
        try:
            payload = connector.propfind([*root_parts, *relative_parts], depth=0)
        except (NextcloudConnectorError, NextcloudResponseError) as exc:
            raise self._remote_error(exc) from exc
        if payload is None:
            raise DocumentNotFoundError("Document entry was not found")
        entries = self._parse_multistatus(
            connector,
            payload,
            root_parts=root_parts,
            exact_relative_parts=relative_parts,
            include_exact=True,
        )
        if entries:
            return entries[0]
        raise DocumentNotFoundError("Document entry was not found")

    def _parse_multistatus(
        self,
        connector: NextcloudWebDavConnector,
        payload: bytes,
        *,
        root_parts: list[str],
        parent_relative_parts: list[str] | None = None,
        exact_relative_parts: list[str] | None = None,
        include_exact: bool = False,
    ) -> list[DocumentEntry]:
        upper_payload = payload.upper()
        if b"<!DOCTYPE" in upper_payload or b"<!ENTITY" in upper_payload:
            raise DocumentRemoteError("Nextcloud returned an unsafe WebDAV response")
        try:
            root = ElementTree.fromstring(payload)
        except ElementTree.ParseError as exc:
            raise DocumentRemoteError("Nextcloud returned an invalid WebDAV response") from exc
        result: list[DocumentEntry] = []
        for response in root.findall(f"{DAV_NAMESPACE}response"):
            properties = self._successful_properties(response)
            if properties is None:
                continue
            href = response.findtext(f"{DAV_NAMESPACE}href") or ""
            try:
                absolute_parts = connector.parts_from_href(href)
            except NextcloudConnectorError as exc:
                raise DocumentRemoteError(str(exc)) from exc
            if absolute_parts[: len(root_parts)] != root_parts:
                raise DocumentRemoteError("Nextcloud returned an entry outside the document root")
            relative_parts = absolute_parts[len(root_parts) :]
            if exact_relative_parts is not None:
                if relative_parts != exact_relative_parts:
                    continue
            elif parent_relative_parts is not None:
                if relative_parts == parent_relative_parts and not include_exact:
                    continue
                if relative_parts[:-1] != parent_relative_parts:
                    continue
            name = relative_parts[-1] if relative_parts else root_parts[-1]
            resource_type = properties.find(f"{DAV_NAMESPACE}resourcetype")
            is_collection = bool(
                resource_type is not None
                and resource_type.find(f"{DAV_NAMESPACE}collection") is not None
            )
            size_text = properties.findtext(f"{DAV_NAMESPACE}getcontentlength") or "0"
            try:
                size_bytes = max(0, int(size_text))
            except ValueError:
                size_bytes = 0
            content_type = properties.findtext(f"{DAV_NAMESPACE}getcontenttype")
            result.append(
                self._entry(
                    name=name,
                    path_parts=relative_parts,
                    entry_type=(
                        DocumentEntryType.FOLDER if is_collection else DocumentEntryType.FILE
                    ),
                    size_bytes=size_bytes,
                    modified_at=self._parse_http_datetime(
                        properties.findtext(f"{DAV_NAMESPACE}getlastmodified")
                    ),
                    content_type=(
                        None if is_collection else self._normalize_content_type(content_type)
                    ),
                    etag=self._sanitize_etag(properties.findtext(f"{DAV_NAMESPACE}getetag")),
                )
            )
        return sorted(
            result,
            key=lambda item: (
                item.entry_type != DocumentEntryType.FOLDER,
                item.name.casefold(),
                item.name,
            ),
        )

    @staticmethod
    def _successful_properties(response: ElementTree.Element) -> ElementTree.Element | None:
        propstats = response.findall(f"{DAV_NAMESPACE}propstat")
        if not propstats:
            return response.find(f"{DAV_NAMESPACE}prop")
        for propstat in propstats:
            status_text = propstat.findtext(f"{DAV_NAMESPACE}status")
            if status_text and not re.search(r"\s2\d\d(?:\s|$)", status_text):
                continue
            properties = propstat.find(f"{DAV_NAMESPACE}prop")
            if properties is not None:
                return properties
        return None

    @staticmethod
    def _entry(
        *,
        name: str,
        path_parts: list[str],
        entry_type: DocumentEntryType,
        size_bytes: int = 0,
        modified_at: datetime | None = None,
        content_type: str | None = None,
        etag: str | None = None,
    ) -> DocumentEntry:
        return DocumentEntry(
            name=name,
            path="/".join(path_parts),
            entry_type=entry_type,
            size_bytes=size_bytes,
            modified_at=modified_at,
            content_type=content_type,
            etag=etag,
        )

    @staticmethod
    def _clean_path(value: str, *, allow_empty: bool = True) -> list[str]:
        if value == "":
            if allow_empty:
                return []
            raise DocumentValidationError("Document path must not be empty")
        if (
            len(value) > 1000
            or value.startswith("/")
            or value.endswith("/")
            or "//" in value
            or "\\" in value
            or CONTROL_CHARACTERS.search(value)
            or not value.strip()
        ):
            raise DocumentValidationError("Document path is invalid")
        parts = value.split("/")
        if any(
            not part or part in {".", ".."} or len(part) > 255 or CONTROL_CHARACTERS.search(part)
            for part in parts
        ):
            raise DocumentValidationError("Document path is invalid")
        return parts

    @classmethod
    def _clean_name(cls, value: str) -> str:
        if not value or not value.strip():
            raise DocumentValidationError("Document name must not be empty")
        parts = cls._clean_path(value, allow_empty=False)
        if len(parts) != 1:
            raise DocumentValidationError("Document name must not contain a path separator")
        return parts[0]

    @staticmethod
    def _normalize_content_type(value: str | None) -> str:
        if not value:
            return "application/octet-stream"
        media_type = value.split(";", 1)[0].strip().lower()
        if len(media_type) > 255 or not MEDIA_TYPE.fullmatch(media_type):
            return "application/octet-stream"
        return media_type

    @staticmethod
    def _sanitize_etag(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if (
            not normalized
            or len(normalized) > 512
            or any(ord(character) < 32 or ord(character) > 126 for character in normalized)
        ):
            return None
        return normalized

    @staticmethod
    def _parse_http_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)

    @staticmethod
    def _remote_error(exc: Exception) -> DocumentError:
        if isinstance(exc, NextcloudResponseError):
            if exc.status_code == 404:
                return DocumentNotFoundError("Document entry was not found")
            if exc.status_code in {409, 412}:
                return DocumentConflictError("Nextcloud reported a document conflict")
            if exc.status_code == 413:
                return DocumentTooLargeError("Document exceeds the configured size limit")
        return DocumentRemoteError(str(exc))
