from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

import httpx


class PaperlessConnectorError(RuntimeError):
    """Raised when Paperless cannot be queried safely."""


@dataclass(slots=True)
class PaperlessDocument:
    document_id: int
    title: str
    created: str | None
    added: str | None
    original_file_name: str | None


class PaperlessConnector:
    """Minimal read-only client for the Paperless-ngx REST API."""

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.transport = transport

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Token {self.token}",
            "Accept": "application/json; version=10",
            "User-Agent": "DocOfHome Paperless connector",
        }

    def search(self, query: str = "", *, page_size: int = 25) -> list[PaperlessDocument]:
        params: dict[str, str | int] = {
            "page_size": max(1, min(page_size, 100)),
            "ordering": "-created",
        }
        if query.strip():
            # Paperless API v10 documents the `text` parameter for full-text search.
            params["text"] = query.strip()
        payload = self._get_json("/api/documents/", params=params)
        results = payload.get("results")
        if not isinstance(results, list):
            raise PaperlessConnectorError("Paperless liefert keine gültige Dokumentliste.")
        return [self._document(item) for item in results if isinstance(item, dict)]

    def get_document(self, document_id: int) -> PaperlessDocument:
        payload = self._get_json(f"/api/documents/{document_id}/")
        return self._document(payload)

    def document_url(self, document_id: int) -> str:
        return f"{self.base_url}/documents/{document_id}/details"

    def _get_json(
        self,
        path: str,
        *,
        params: dict[str, str | int] | None = None,
    ) -> dict[str, object]:
        try:
            with httpx.Client(
                timeout=httpx.Timeout(8.0),
                follow_redirects=False,
                transport=self.transport,
                headers=self._headers(),
            ) as client:
                response = client.get(
                    urljoin(f"{self.base_url}/", path.lstrip("/")),
                    params=params,
                )
        except httpx.TimeoutException as exc:
            raise PaperlessConnectorError(
                "Zeitüberschreitung beim Zugriff auf Paperless."
            ) from exc
        except httpx.RequestError as exc:
            raise PaperlessConnectorError("Paperless ist nicht erreichbar.") from exc
        if response.status_code in {401, 403}:
            raise PaperlessConnectorError("Der Paperless API-Token wurde abgelehnt.")
        if response.status_code == 404:
            raise PaperlessConnectorError(
                "Der erwartete Paperless-API-Endpunkt wurde nicht gefunden."
            )
        if response.status_code != 200:
            raise PaperlessConnectorError(
                f"Paperless antwortet mit HTTP {response.status_code}."
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise PaperlessConnectorError(
                "Paperless liefert keine gültige JSON-Antwort."
            ) from exc
        if not isinstance(payload, dict):
            raise PaperlessConnectorError(
                "Paperless liefert ein unerwartetes Antwortformat."
            )
        return payload

    @staticmethod
    def _document(payload: dict[str, object]) -> PaperlessDocument:
        raw_id = payload.get("id")
        if not isinstance(raw_id, int) or raw_id < 1:
            raise PaperlessConnectorError("Paperless-Dokument enthält keine gültige ID.")
        raw_title = payload.get("title")
        title = str(raw_title).strip() if raw_title is not None else f"Dokument {raw_id}"
        if not title:
            title = f"Dokument {raw_id}"
        created = str(payload.get("created")) if payload.get("created") else None
        added = str(payload.get("added")) if payload.get("added") else None
        original = payload.get("original_file_name") or payload.get("original_filename")
        return PaperlessDocument(
            document_id=raw_id,
            title=title[:500],
            created=created[:40] if created else None,
            added=added[:40] if added else None,
            original_file_name=str(original)[:500] if original else None,
        )
