from __future__ import annotations

import http.client
import json
import socket
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


class DockerEngineError(RuntimeError):
    pass


class _UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: str, timeout: float = 5.0) -> None:
        super().__init__("localhost", timeout=timeout)
        self.socket_path = socket_path

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect(self.socket_path)
        self.sock = sock


class DockerEngineConnector:
    """Small read-only Docker Engine API client using the local Unix socket."""

    def __init__(self, socket_path: str = "/var/run/docker.sock", timeout: float = 5.0) -> None:
        self.socket_path = socket_path
        self.timeout = timeout

    def _request(self, path: str) -> Any:
        socket_file = Path(self.socket_path)
        if not socket_file.exists():
            raise DockerEngineError(f"Docker-Socket nicht gefunden: {self.socket_path}")
        connection = _UnixHTTPConnection(self.socket_path, timeout=self.timeout)
        try:
            connection.request("GET", path, headers={"Host": "docker"})
            response = connection.getresponse()
            payload = response.read()
        except (OSError, http.client.HTTPException) as exc:
            raise DockerEngineError(f"Docker Engine ist nicht erreichbar: {exc}") from exc
        finally:
            connection.close()
        if response.status >= 400:
            detail = payload.decode("utf-8", errors="replace")[:500]
            raise DockerEngineError(f"Docker Engine antwortet mit HTTP {response.status}: {detail}")
        if not payload:
            return None
        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise DockerEngineError("Docker Engine lieferte eine ungültige JSON-Antwort") from exc

    def version(self) -> str | None:
        payload = self._request("/version")
        if isinstance(payload, dict):
            value = payload.get("Version")
            return str(value) if value else None
        return None

    def containers(self, *, all_containers: bool = True) -> list[dict[str, Any]]:
        query = urlencode({"all": 1 if all_containers else 0})
        payload = self._request(f"/containers/json?{query}")
        if not isinstance(payload, list):
            raise DockerEngineError("Docker Engine lieferte keine Containerliste")
        return [item for item in payload if isinstance(item, dict)]
