from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any
from uuid import UUID

from app.core.settings import settings

from .docker_engine import DockerEngineError


def _key_directory() -> Path:
    directory = Path(settings.data_dir) / "secrets" / "docker-ssh"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory.chmod(0o700)
    return directory


def key_paths(host_id: UUID) -> tuple[Path, Path, Path]:
    base = _key_directory() / str(host_id)
    return base, base.with_suffix(".pub"), base.with_suffix(".known_hosts")


def ensure_key_pair(host_id: UUID) -> str:
    private_key, public_key, _ = key_paths(host_id)
    if not private_key.is_file() or not public_key.is_file():
        try:
            subprocess.run(
                [
                    "ssh-keygen",
                    "-q",
                    "-t",
                    "ed25519",
                    "-N",
                    "",
                    "-C",
                    f"docofhome-docker-{host_id}",
                    "-f",
                    str(private_key),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise DockerEngineError(f"SSH-Schlüssel konnte nicht erzeugt werden: {exc}") from exc
    private_key.chmod(0o600)
    public_key.chmod(0o644)
    return public_key.read_text(encoding="utf-8").strip()


def remove_key_pair(host_id: UUID) -> None:
    for path in key_paths(host_id):
        if path.is_file():
            path.unlink()


def host_key_fingerprint(host_key: str | None) -> str | None:
    if not host_key:
        return None
    parts = host_key.strip().split()
    if len(parts) < 3:
        return None
    try:
        digest = hashlib.sha256(base64.b64decode(parts[2], validate=True)).digest()
    except (ValueError, binascii.Error):
        return None
    return "SHA256:" + base64.b64encode(digest).decode("ascii").rstrip("=")


def scan_host_key(host: str, port: int) -> tuple[str, str]:
    try:
        result = subprocess.run(
            ["ssh-keyscan", "-T", "5", "-p", str(port), host],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise DockerEngineError(f"SSH-Serveridentität konnte nicht gelesen werden: {exc}") from exc
    lines = [
        line.strip() for line in result.stdout.splitlines() if line and not line.startswith("#")
    ]
    selected = next(
        (line for line in lines if " ssh-ed25519 " in line), lines[0] if lines else None
    )
    fingerprint = host_key_fingerprint(selected)
    if selected is None or fingerprint is None:
        detail = result.stderr.strip()[:300]
        raise DockerEngineError(
            f"SSH-Server lieferte keinen gültigen Host-Schlüssel. {detail}".strip()
        )
    return selected, fingerprint


class SshDockerEngineConnector:
    """Read a constrained Docker snapshot through a pinned SSH connection."""

    def __init__(
        self,
        host_id: UUID,
        host: str,
        port: int,
        user: str,
        host_key: str,
        timeout: float = 15.0,
    ) -> None:
        self.host_id = host_id
        self.host = host
        self.port = port
        self.user = user
        self.host_key = host_key
        self.timeout = timeout
        self._snapshot: dict[str, Any] | None = None

    def _load(self) -> dict[str, Any]:
        if self._snapshot is not None:
            return self._snapshot
        public_key = ensure_key_pair(self.host_id)
        if not public_key:
            raise DockerEngineError("SSH-Public-Key fehlt")
        private_key, _, known_hosts = key_paths(self.host_id)
        known_hosts.write_text(self.host_key.strip() + "\n", encoding="utf-8")
        known_hosts.chmod(0o600)
        command = [
            "ssh",
            "-T",
            "-F",
            "/dev/null",
            "-p",
            str(self.port),
            "-i",
            str(private_key),
            "-o",
            "BatchMode=yes",
            "-o",
            "PasswordAuthentication=no",
            "-o",
            "KbdInteractiveAuthentication=no",
            "-o",
            "PreferredAuthentications=publickey",
            "-o",
            "IdentitiesOnly=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"UserKnownHostsFile={known_hosts}",
            "-o",
            "GlobalKnownHostsFile=/dev/null",
            "-o",
            "ConnectTimeout=8",
            "-o",
            "ConnectionAttempts=1",
            "-o",
            "LogLevel=ERROR",
            f"{self.user}@{self.host}",
            "docofhome-docker-snapshot",
        ]
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")},
            )
        except subprocess.TimeoutExpired as exc:
            raise DockerEngineError("SSH-Verbindung hat das Zeitlimit überschritten") from exc
        except OSError as exc:
            raise DockerEngineError(f"SSH konnte nicht gestartet werden: {exc}") from exc
        if result.returncode != 0:
            detail = result.stderr.strip()[:500] or "unbekannter SSH-Fehler"
            raise DockerEngineError(f"SSH-Docker-Abfrage fehlgeschlagen: {detail}")
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise DockerEngineError("SSH-Hilfsprogramm lieferte kein gültiges JSON") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("containers"), list):
            raise DockerEngineError("SSH-Hilfsprogramm lieferte eine ungültige Docker-Antwort")
        self._snapshot = payload
        return payload

    def version(self) -> str | None:
        value = self._load().get("docker_version")
        return str(value) if value else None

    def containers(self, *, all_containers: bool = True) -> list[dict[str, Any]]:
        del all_containers
        return [item for item in self._load()["containers"] if isinstance(item, dict)]
