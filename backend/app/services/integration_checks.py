from __future__ import annotations

from time import perf_counter
from urllib.parse import quote, urlparse

import httpx
from sqlmodel import Session

from app.connectors.fritzbox import FritzBoxConnector, FritzBoxConnectorError
from app.repositories.settings import SettingsRepository
from app.schemas.settings import IntegrationKind, IntegrationTestResult, IntegrationWrite


class IntegrationCheckService:
    """Perform read-only connection checks with stored credentials."""

    def __init__(
        self,
        session: Session,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.repository = SettingsRepository(session)
        self.transport = transport

    def check(self, kind: IntegrationKind) -> IntegrationTestResult:
        setting = self.repository.get_integration(kind.value)
        if setting is None:
            return self._result(kind, perf_counter(), False, "Die Integration ist nicht konfiguriert.")
        payload = IntegrationWrite(
            kind=kind, enabled=setting.enabled, base_url=setting.base_url, account=setting.account,
            secret=setting.secret, selected_album_id=setting.selected_album_id,
            document_root=setting.document_root,
        )
        return self.check_payload(payload)

    def check_payload(self, payload: IntegrationWrite) -> IntegrationTestResult:
        kind = payload.kind
        started = perf_counter()
        setting = payload
        if setting is None or not setting.enabled:
            return self._result(kind, started, False, "Die Integration ist deaktiviert.")
        secret = setting.secret.get_secret_value() if hasattr(setting.secret, "get_secret_value") else setting.secret
        if not setting.base_url or not secret:
            return self._result(
                kind,
                started,
                False,
                "URL oder Zugangsdaten sind nicht vollständig gespeichert.",
            )
        if kind in {IntegrationKind.NEXTCLOUD, IntegrationKind.FRITZBOX} and not setting.account:
            return self._result(
                kind,
                started,
                False,
                "Für Nextcloud oder FRITZ!Box wird ein Konto beziehungsweise Benutzername benötigt.",
            )

        try:
            with httpx.Client(
                timeout=httpx.Timeout(5.0),
                follow_redirects=False,
                transport=self.transport,
                headers={"User-Agent": "DocOfHome integration check"},
            ) as client:
                if kind is IntegrationKind.HOME_ASSISTANT:
                    message, version = self._check_home_assistant(
                        client, setting.base_url, secret
                    )
                elif kind is IntegrationKind.IMMICH:
                    message, version = self._check_immich(client, setting.base_url, secret)
                elif kind is IntegrationKind.NEXTCLOUD:
                    message, version = self._check_nextcloud(
                        client,
                        setting.base_url,
                        setting.account or "",
                        secret,
                    )
                elif kind is IntegrationKind.FRITZBOX:
                    devices = FritzBoxConnector(
                        base_url=setting.base_url,
                        account=setting.account or "",
                        secret=secret,
                        transport=self.transport,
                    ).devices()
                    message = f"FRITZ!Box ist read-only erreichbar ({len(devices)} Geräte)."
                    version = None
                elif kind is IntegrationKind.PAPERLESS:
                    message, version = self._check_paperless(client, setting.base_url, secret)
                else:
                    return self._result(
                        kind,
                        started,
                        False,
                        "Für diese Integration ist kein Verbindungstest implementiert.",
                    )
        except httpx.TimeoutException:
            return self._result(
                kind,
                started,
                False,
                "Zeitüberschreitung beim Verbindungsaufbau.",
            )
        except httpx.RequestError:
            return self._result(
                kind,
                started,
                False,
                "Der Server ist nicht erreichbar oder die TLS-Verbindung ist fehlgeschlagen.",
            )
        except IntegrationResponseError as exc:
            return self._result(kind, started, False, str(exc))
        except FritzBoxConnectorError as exc:
            return self._result(kind, started, False, str(exc))

        return self._result(kind, started, True, message, version)

    @staticmethod
    def _check_home_assistant(
        client: httpx.Client,
        base_url: str,
        secret: str,
    ) -> tuple[str, str | None]:
        parsed_path = urlparse(base_url).path.rstrip("/")
        endpoint = (
            f"{base_url.rstrip('/')}/config"
            if parsed_path.endswith("/api")
            else f"{base_url.rstrip('/')}/api/config"
        )
        response = client.get(
            endpoint,
            headers={"Authorization": f"Bearer {secret}", "Accept": "application/json"},
        )
        IntegrationCheckService._require_status(response, {200})
        payload = IntegrationCheckService._json_object(response)
        version = payload.get("version")
        return "Home Assistant ist erreichbar und das Token ist gültig.", (
            str(version) if version else None
        )

    @staticmethod
    def _check_immich(
        client: httpx.Client,
        base_url: str,
        secret: str,
    ) -> tuple[str, str | None]:
        api_base = IntegrationCheckService._immich_api_base(base_url)
        headers = {"x-api-key": secret, "Accept": "application/json"}
        auth_response = client.get(f"{api_base}/api-keys/me", headers=headers)
        IntegrationCheckService._require_status(auth_response, {200})

        version_response = client.get(f"{api_base}/server/version", headers=headers)
        IntegrationCheckService._require_status(version_response, {200})
        payload = IntegrationCheckService._json_object(version_response)
        version = payload.get("version")
        if not version:
            parts = [payload.get(key) for key in ("major", "minor", "patch")]
            if all(part is not None for part in parts):
                version = ".".join(str(part) for part in parts)
        return "Immich ist erreichbar und der API-Key ist gültig.", (
            str(version) if version else None
        )

    @staticmethod
    def _check_nextcloud(
        client: httpx.Client,
        base_url: str,
        account: str,
        secret: str,
    ) -> tuple[str, str | None]:
        endpoint = f"{base_url.rstrip('/')}/remote.php/dav/files/{quote(account, safe='')}/"
        response = client.request(
            "PROPFIND",
            endpoint,
            auth=httpx.BasicAuth(account, secret),
            headers={"Depth": "0", "Accept": "application/xml"},
        )
        IntegrationCheckService._require_status(response, {207})
        return "Nextcloud-WebDAV ist erreichbar und die Anmeldung war erfolgreich.", None


    @staticmethod
    def _check_paperless(
        client: httpx.Client,
        base_url: str,
        secret: str,
    ) -> tuple[str, str | None]:
        endpoint = f"{base_url.rstrip('/')}/api/documents/?page_size=1"
        response = client.get(
            endpoint,
            headers={
                "Authorization": f"Token {secret}",
                "Accept": "application/json; version=10",
            },
        )
        IntegrationCheckService._require_status(response, {200})
        IntegrationCheckService._json_object(response)
        version = response.headers.get("X-Version")
        return "Paperless ist erreichbar und der API-Token ist gültig.", version

    @staticmethod
    def _immich_api_base(base_url: str) -> str:
        normalized = base_url.rstrip("/")
        return normalized if urlparse(normalized).path.endswith("/api") else f"{normalized}/api"

    @staticmethod
    def _require_status(response: httpx.Response, expected: set[int]) -> None:
        if response.status_code in expected:
            return
        if response.status_code in {401, 403}:
            raise IntegrationResponseError("Die Zugangsdaten wurden vom Server abgelehnt.")
        if 300 <= response.status_code < 400:
            raise IntegrationResponseError(
                "Der Server antwortet mit einer Umleitung. Bitte die direkte interne URL verwenden."
            )
        if response.status_code == 404:
            raise IntegrationResponseError(
                "Die URL ist erreichbar, aber der erwartete API-Endpunkt wurde nicht gefunden."
            )
        raise IntegrationResponseError(
            f"Der Server antwortet unerwartet mit HTTP {response.status_code}."
        )

    @staticmethod
    def _json_object(response: httpx.Response) -> dict[str, object]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise IntegrationResponseError(
                "Der Server liefert keine gültige JSON-Antwort."
            ) from exc
        if not isinstance(payload, dict):
            raise IntegrationResponseError("Der Server liefert ein unerwartetes Antwortformat.")
        return payload

    @staticmethod
    def _result(
        kind: IntegrationKind,
        started: float,
        success: bool,
        message: str,
        service_version: str | None = None,
    ) -> IntegrationTestResult:
        return IntegrationTestResult(
            kind=kind,
            success=success,
            message=message,
            service_version=service_version,
            response_time_ms=max(0, round((perf_counter() - started) * 1000)),
        )


class IntegrationResponseError(RuntimeError):
    """Raised for a reachable service with an invalid integration response."""
