from __future__ import annotations

import re
from urllib.parse import quote, urlsplit, urlunsplit

import httpx

from app.connectors.nextcloud import NextcloudConnectorError, NextcloudResponseError

_SHARE_TOKEN = re.compile(r"^[A-Za-z0-9_-]{8,128}$")


class NextcloudPublicShareUploader:
    """Upload-only WebDAV adapter for one fixed public Nextcloud folder share."""

    def __init__(
        self,
        *,
        share_url: str,
        transport: httpx.BaseTransport | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        parsed = urlsplit(share_url)
        if (
            parsed.scheme.lower() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Invalid public Nextcloud share URL")

        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 2 or parts[-2] != "s" or not _SHARE_TOKEN.fullmatch(parts[-1]):
            raise ValueError("Invalid public Nextcloud share token")
        token = parts[-1]
        prefix = parts[:-2]
        if prefix and prefix[-1] == "index.php":
            prefix = prefix[:-1]
        root_path = "/" + "/".join(
            [*prefix, "public.php", "dav", "files", quote(token, safe="")]
        )
        self.files_root_url = urlunsplit(
            (parsed.scheme.lower(), parsed.netloc, root_path, "", "")
        ).rstrip("/")
        self.transport = transport
        self.timeout_seconds = timeout_seconds

    def upload(
        self,
        filename: str,
        *,
        content: bytes,
        content_type: str,
    ) -> int:
        if (
            not filename
            or filename in {".", ".."}
            or "/" in filename
            or "\\" in filename
            or len(filename) > 255
            or any(ord(character) < 32 or ord(character) == 127 for character in filename)
        ):
            raise ValueError("Invalid feedback filename")
        url = f"{self.files_root_url}/{quote(filename, safe='')}"
        headers = {
            "Content-Type": content_type,
            "If-None-Match": "*",
            "X-Requested-With": "XMLHttpRequest",
        }
        try:
            with httpx.Client(
                timeout=self.timeout_seconds,
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                response = client.put(url, content=content, headers=headers)
        except httpx.HTTPError as exc:
            raise NextcloudConnectorError("Nextcloud File Drop could not be reached") from exc
        if response.status_code not in {200, 201, 204}:
            raise NextcloudResponseError(
                response.status_code,
                f"Nextcloud File Drop upload failed ({response.status_code})",
            )
        return response.status_code
