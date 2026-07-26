from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from urllib.parse import SplitResult, quote, unquote, urlsplit

import httpx

MAX_PROPFIND_BYTES = 8 * 1024 * 1024


class NextcloudConnectorError(RuntimeError):
    """Raised when WebDAV transport or response handling fails."""


class NextcloudResponseError(NextcloudConnectorError):
    """Raised when Nextcloud returns a non-success WebDAV response."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class NextcloudWebDavConnector:
    """Small bounded WebDAV adapter for one configured Nextcloud account."""

    def __init__(
        self,
        *,
        base_url: str,
        account: str,
        secret: str,
        transport: httpx.BaseTransport | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        parsed_base = urlsplit(base_url)
        if (
            parsed_base.scheme.lower() not in {"http", "https"}
            or not parsed_base.hostname
            or parsed_base.username is not None
            or parsed_base.password is not None
            or parsed_base.query
            or parsed_base.fragment
        ):
            raise ValueError("Invalid Nextcloud base URL")
        if (
            not account
            or "/" in account
            or "\\" in account
            or any(ord(character) < 32 or ord(character) == 127 for character in account)
        ):
            raise ValueError("Invalid Nextcloud account or username")
        self.account = account
        self.auth = (account, secret)
        self.transport = transport
        self.timeout_seconds = timeout_seconds
        self.files_root_url = (
            f"{base_url.rstrip('/')}/remote.php/dav/files/{quote(account, safe='')}"
        )
        parsed_root = urlsplit(self.files_root_url)
        self.files_root_path = parsed_root.path.rstrip("/")
        self.files_root_origin = self._origin(parsed_root)

    @contextmanager
    def client(self) -> Iterator[httpx.Client]:
        with httpx.Client(
            timeout=self.timeout_seconds,
            follow_redirects=False,
            auth=self.auth,
            transport=self.transport,
        ) as client:
            yield client

    def url(self, parts: Sequence[str]) -> str:
        suffix = "/".join(quote(part, safe="") for part in parts)
        return f"{self.files_root_url}/{suffix}" if suffix else self.files_root_url

    def parts_from_href(self, href: str) -> list[str]:
        parsed = urlsplit(href)
        if (
            parsed.query
            or parsed.fragment
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise NextcloudConnectorError("Nextcloud returned an unsafe WebDAV path")
        if (parsed.scheme or parsed.netloc) and self._origin(parsed) != self.files_root_origin:
            raise NextcloudConnectorError("Nextcloud returned an out-of-scope WebDAV origin")

        decoded_path = unquote(parsed.path).rstrip("/")
        root = unquote(self.files_root_path)
        if decoded_path == root:
            return []
        prefix = f"{root}/"
        if not decoded_path.startswith(prefix):
            raise NextcloudConnectorError("Nextcloud returned an out-of-scope WebDAV path")
        parts = decoded_path[len(prefix) :].split("/")
        if any(
            not part
            or part in {".", ".."}
            or "\\" in part
            or len(part) > 255
            or any(ord(character) < 32 or ord(character) == 127 for character in part)
            for part in parts
        ):
            raise NextcloudConnectorError("Nextcloud returned an unsafe WebDAV path")
        return parts

    def propfind(self, parts: Sequence[str], *, depth: int) -> bytes | None:
        request_body = (
            '<?xml version="1.0" encoding="utf-8" ?>'
            '<d:propfind xmlns:d="DAV:"><d:prop>'
            "<d:resourcetype/><d:getcontentlength/><d:getlastmodified/>"
            "<d:getcontenttype/><d:getetag/>"
            "</d:prop></d:propfind>"
        )
        try:
            with self.client() as client:
                with client.stream(
                    "PROPFIND",
                    self.url(parts),
                    headers={"Depth": str(depth), "Content-Type": "application/xml"},
                    content=request_body,
                ) as response:
                    if response.status_code == 404:
                        return None
                    if response.status_code != 207:
                        raise NextcloudResponseError(
                            response.status_code,
                            f"Nextcloud WebDAV listing failed ({response.status_code})",
                        )
                    return self._read_bounded_response(
                        response,
                        max_bytes=MAX_PROPFIND_BYTES,
                        message="Nextcloud WebDAV listing exceeds the response limit",
                    )
        except httpx.HTTPError as exc:
            raise NextcloudConnectorError("Nextcloud could not be reached") from exc

    def create_collection(self, parts: Sequence[str]) -> bool:
        try:
            with self.client() as client:
                response = client.request("MKCOL", self.url(parts))
        except httpx.HTTPError as exc:
            raise NextcloudConnectorError("Nextcloud could not be reached") from exc
        if response.status_code == 201:
            return True
        if response.status_code == 405:
            return False
        raise NextcloudResponseError(
            response.status_code,
            f"Nextcloud folder could not be created ({response.status_code})",
        )

    def upload(
        self,
        parts: Sequence[str],
        *,
        content: bytes,
        content_type: str,
        overwrite: bool,
    ) -> int:
        headers = {"Content-Type": content_type}
        if not overwrite:
            headers["If-None-Match"] = "*"
        try:
            with self.client() as client:
                response = client.put(self.url(parts), content=content, headers=headers)
        except httpx.HTTPError as exc:
            raise NextcloudConnectorError("Nextcloud could not be reached") from exc
        if response.status_code not in {200, 201, 204}:
            raise NextcloudResponseError(
                response.status_code,
                f"Nextcloud upload failed ({response.status_code})",
            )
        return response.status_code

    def download(self, parts: Sequence[str], *, max_bytes: int) -> tuple[bytes, str, str | None]:
        try:
            with self.client() as client:
                with client.stream("GET", self.url(parts)) as response:
                    if response.status_code != 200:
                        raise NextcloudResponseError(
                            response.status_code,
                            f"Nextcloud document could not be downloaded ({response.status_code})",
                        )
                    content = self._read_bounded_response(
                        response,
                        max_bytes=max_bytes,
                        message="Nextcloud document exceeds the download limit",
                    )
                    return (
                        content,
                        response.headers.get("content-type", "application/octet-stream"),
                        response.headers.get("etag"),
                    )
        except httpx.HTTPError as exc:
            raise NextcloudConnectorError("Nextcloud could not be reached") from exc

    def delete(self, parts: Sequence[str], *, etag: str | None = None) -> None:
        headers = {"If-Match": etag} if etag else None
        try:
            with self.client() as client:
                response = client.delete(self.url(parts), headers=headers)
        except httpx.HTTPError as exc:
            raise NextcloudConnectorError("Nextcloud could not be reached") from exc
        if response.status_code not in {200, 204}:
            raise NextcloudResponseError(
                response.status_code,
                f"Nextcloud document could not be deleted ({response.status_code})",
            )

    def move(self, source: Sequence[str], destination: Sequence[str]) -> None:
        try:
            with self.client() as client:
                response = client.request(
                    "MOVE",
                    self.url(source),
                    headers={"Destination": self.url(destination), "Overwrite": "F"},
                )
        except httpx.HTTPError as exc:
            raise NextcloudConnectorError("Nextcloud could not be reached") from exc
        if response.status_code not in {201, 204}:
            raise NextcloudResponseError(
                response.status_code,
                f"Nextcloud document could not be moved ({response.status_code})",
            )

    @staticmethod
    def _origin(split: SplitResult) -> tuple[str, str, int | None]:
        scheme = split.scheme.lower()
        hostname = (split.hostname or "").lower()
        port = split.port
        if port is None:
            port = 443 if scheme == "https" else 80 if scheme == "http" else None
        return scheme, hostname, port

    @staticmethod
    def _read_bounded_response(
        response: httpx.Response,
        *,
        max_bytes: int,
        message: str,
    ) -> bytes:
        length = response.headers.get("content-length")
        if length:
            try:
                if int(length) > max_bytes:
                    raise NextcloudResponseError(413, message)
            except ValueError:
                pass
        chunks: list[bytes] = []
        total = 0
        for chunk in response.iter_bytes():
            total += len(chunk)
            if total > max_bytes:
                raise NextcloudResponseError(413, message)
            chunks.append(chunk)
        return b"".join(chunks)
