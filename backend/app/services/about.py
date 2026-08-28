from __future__ import annotations

import json
import re
import secrets
from collections import defaultdict, deque
from datetime import UTC, date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from threading import Lock
from zipfile import ZIP_DEFLATED, ZipFile

from sqlmodel import Session

from app.connectors.nextcloud import NextcloudConnectorError
from app.connectors.nextcloud_public_share import NextcloudPublicShareUploader
from app.core.project_info import (
    FEEDBACK_PUBLIC_SHARE_URL,
    LICENSE_NOTICE,
    PROJECT_LINKS,
)
from app.core.settings import settings
from app.schemas.about import (
    AboutLinkRead,
    AboutRead,
    FeedbackResultRead,
    FeedbackWrite,
    ReleaseNoteRead,
)

_HISTORY_HEADING = re.compile(r"^##\s+(\d+\.\d+\.\d+(?:\.\d+)?)\s+[–-]\s+(\d{4}-\d{2}-\d{2})\s*$")
_RATE_WINDOW = timedelta(minutes=10)
_RATE_LIMIT = 5
_MAX_FEEDBACK_ZIP_BYTES = 256 * 1024
_rate_events: dict[str, deque[datetime]] = defaultdict(deque)
_rate_lock = Lock()


class AboutError(RuntimeError):
    pass


class FeedbackUnavailableError(AboutError):
    pass


class FeedbackRateLimitError(AboutError):
    pass


class AboutService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def read(self) -> AboutRead:
        return AboutRead(
            name=settings.app_name,
            slogan="Know your home.",
            version=settings.app_version,
            project_summary=(
                "DocOfHome ist eine lokale, alltagstaugliche Dokumentation für Gebäude, "
                "Räume, Technik, Verbräuche und die wichtigsten Zusammenhänge im eigenen Zuhause."
            ),
            data_sovereignty=(
                "Die Anwendung ist für den selbst betriebenen Einsatz gedacht. Deine Daten "
                "bleiben in deiner Installation. Feedback wird nur nach ausdrücklichem Absenden "
                "als begrenztes ZIP an den fest hinterlegten DocOfHome-File-Drop übertragen."
            ),
            license_notice=LICENSE_NOTICE,
            links=self._links(),
            releases=self._release_notes(),
            feedback_available=self._feedback_target_valid(),
            feedback_unavailable_reason=(
                None
                if self._feedback_target_valid()
                else "Das fest hinterlegte Feedbackziel ist ungültig."
            ),
        )

    def submit_feedback(self, payload: FeedbackWrite, client_key: str) -> FeedbackResultRead:
        self._check_rate_limit(client_key)
        now = datetime.now(UTC)
        reference = f"{now:%Y%m%dT%H%M%SZ}-{secrets.token_hex(4)}"
        filename = f"docofhome-feedback-{reference}.zip"
        archive = self._feedback_zip(payload, reference, now)
        if len(archive) > _MAX_FEEDBACK_ZIP_BYTES:
            raise FeedbackUnavailableError("Das erzeugte Feedback-ZIP ist unerwartet groß.")
        try:
            uploader = NextcloudPublicShareUploader(
                share_url=FEEDBACK_PUBLIC_SHARE_URL,
                timeout_seconds=20.0,
            )
            uploader.upload(
                filename,
                content=archive,
                content_type="application/zip",
            )
        except (NextcloudConnectorError, ValueError) as exc:
            raise FeedbackUnavailableError(
                "Feedback konnte nicht an den DocOfHome-File-Drop übertragen werden."
            ) from exc
        return FeedbackResultRead(
            message="Vielen Dank. Dein Feedback wurde als ZIP übertragen.",
            reference=reference,
        )

    @staticmethod
    def _feedback_target_valid() -> bool:
        try:
            NextcloudPublicShareUploader(share_url=FEEDBACK_PUBLIC_SHARE_URL)
        except ValueError:
            return False
        return True

    @staticmethod
    def _links() -> list[AboutLinkRead]:
        return [
            AboutLinkRead(label=link.label, url=link.url, icon=link.icon)
            for link in PROJECT_LINKS
            if link.url
        ]

    @classmethod
    def _release_notes(cls) -> list[ReleaseNoteRead]:
        entries: dict[str, ReleaseNoteRead] = {}
        for root in cls._content_roots():
            path = root / "PROJECT_HISTORY.md"
            if not path.is_file():
                continue
            current_version: str | None = None
            current_date: date | None = None
            body: list[str] = []

            def flush() -> None:
                nonlocal current_version, current_date, body
                if current_version is None or current_version in entries:
                    body = []
                    return
                markdown_body = "\n".join(body).strip()
                entries[current_version] = ReleaseNoteRead(
                    version=current_version,
                    title=f"DocOfHome {current_version}",
                    release_date=current_date,
                    markdown=(
                        f"# DocOfHome {current_version}\n\n{markdown_body}"
                        if markdown_body
                        else f"# DocOfHome {current_version}"
                    ),
                    current=current_version == settings.app_version,
                )
                body = []

            for line in path.read_text(encoding="utf-8").splitlines():
                match = _HISTORY_HEADING.match(line)
                if match:
                    flush()
                    current_version = match.group(1)
                    current_date = date.fromisoformat(match.group(2))
                    continue
                if current_version is not None:
                    body.append(line)
            flush()
            if entries:
                break

        if settings.app_version not in entries:
            entries[settings.app_version] = ReleaseNoteRead(
                version=settings.app_version,
                title=f"DocOfHome {settings.app_version}",
                release_date=None,
                markdown=f"# DocOfHome {settings.app_version}\n\nAktuell installierte Version.",
                current=True,
            )
        return sorted(entries.values(), key=lambda item: cls._version_key(item.version), reverse=True)

    @staticmethod
    def _content_roots() -> list[Path]:
        module = Path(__file__).resolve()
        candidates = [
            module.parents[3],
            module.parents[2],
            module.parents[2] / "release-notes",
            Path("/app/release-notes"),
        ]
        result: list[Path] = []
        for candidate in candidates:
            if candidate not in result:
                result.append(candidate)
        return result


    @staticmethod
    def _version_key(value: str) -> tuple[int, int, int, int]:
        try:
            parts = [int(item) for item in value.split(".")]
            if len(parts) not in {3, 4}:
                raise ValueError
            return tuple((parts + [0])[:4])  # type: ignore[return-value]
        except (ValueError, TypeError):
            return 0, 0, 0, 0

    @classmethod
    def _feedback_zip(
        cls,
        payload: FeedbackWrite,
        reference: str,
        created_at: datetime,
    ) -> bytes:
        technical_info = None
        if payload.include_technical_info and payload.technical_info:
            technical_info = payload.technical_info.model_dump(exclude_none=True)
        metadata = {
            "schema_version": 1,
            "reference": reference,
            "created_at": created_at.isoformat(),
            "category": payload.category.value,
            "subject": payload.subject,
            "current_page": payload.current_page,
            "technical_info": technical_info,
        }
        buffer = BytesIO()
        with ZipFile(buffer, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
            archive.writestr("feedback.md", cls._feedback_markdown(payload, reference, created_at))
            archive.writestr(
                "metadata.json",
                json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8"),
            )
            archive.writestr(
                "README.txt",
                (
                    "Dieses ZIP wurde von DocOfHome erzeugt. Es enthält nur das bewusst "
                    "abgesendete Feedback und gegebenenfalls ausdrücklich freigegebene "
                    "technische Angaben. Datenbank, Zugangsdaten und Tokens sind nicht enthalten.\n"
                ),
            )
        return buffer.getvalue()

    @staticmethod
    def _feedback_markdown(
        payload: FeedbackWrite,
        reference: str,
        created_at: datetime,
    ) -> str:
        category_labels = {
            "error": "Fehler",
            "improvement": "Verbesserung",
            "usability": "Bedienung",
            "documentation": "Dokumentation",
            "other": "Sonstiges",
        }
        lines = [
            f"# DocOfHome-Feedback {reference}",
            "",
            f"- Zeitpunkt: {created_at.isoformat()}",
            f"- Kategorie: {category_labels[payload.category.value]}",
            f"- Betreff: {payload.subject}",
        ]
        if payload.current_page:
            lines.append(f"- Aktuelle Seite: {payload.current_page}")
        lines.extend(["", "## Beschreibung", "", payload.description])
        if payload.include_technical_info and payload.technical_info:
            lines.extend(["", "## Freigegebene technische Informationen", ""])
            labels = {
                "app_version": "App-Version",
                "route": "Route",
                "user_agent": "Browserkennung",
                "viewport": "Fenstergröße",
            }
            for key, value in payload.technical_info.model_dump().items():
                if value:
                    lines.append(f"- {labels[key]}: {value}")
        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def _check_rate_limit(client_key: str) -> None:
        now = datetime.now(UTC)
        threshold = now - _RATE_WINDOW
        with _rate_lock:
            events = _rate_events[client_key]
            while events and events[0] < threshold:
                events.popleft()
            if len(events) >= _RATE_LIMIT:
                raise FeedbackRateLimitError(
                    "Zu viele Feedbacksendungen. Bitte versuche es in einigen Minuten erneut."
                )
            events.append(now)
