from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.connectors.paperless import PaperlessConnector, PaperlessConnectorError
from app.models.work import WorkItemEvent, WorkItemEventPaperlessLink
from app.repositories.settings import SettingsRepository
from app.schemas.paperless import PaperlessDocumentRead
from app.schemas.work import WorkPaperlessLinkRead


class PaperlessServiceError(RuntimeError):
    pass


class PaperlessNotConfiguredError(PaperlessServiceError):
    pass


class PaperlessService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = SettingsRepository(session)

    def _connector(self) -> PaperlessConnector:
        setting = self.settings.get_integration("paperless")
        if (
            setting is None
            or not setting.enabled
            or not setting.base_url
            or not setting.secret
        ):
            raise PaperlessNotConfiguredError(
                "Paperless ist nicht eingerichtet. Konfiguriere zuerst Server-URL und "
                "API-Token in den Einstellungen."
            )
        return PaperlessConnector(base_url=setting.base_url, token=setting.secret)

    def search(self, query: str, page_size: int = 25) -> list[PaperlessDocumentRead]:
        connector = self._connector()
        setting = self.settings.get_integration("paperless")
        configured_url = setting.browser_url or setting.base_url if setting else None
        browser_url = configured_url.rstrip("/") if configured_url else connector.base_url
        try:
            documents = connector.search(query, page_size=page_size)
        except PaperlessConnectorError as exc:
            raise PaperlessServiceError(str(exc)) from exc
        return [
            PaperlessDocumentRead(
                document_id=document.document_id,
                title=document.title,
                created=document.created,
                added=document.added,
                original_file_name=document.original_file_name,
                source_url=f"{browser_url}/documents/{document.document_id}/details",
            )
            for document in documents
        ]

    def link(self, event_id: UUID, document_id: int) -> WorkPaperlessLinkRead:
        event = self.session.get(WorkItemEvent, event_id)
        if event is None or event.event_type != "completed":
            raise PaperlessServiceError("Historieneintrag wurde nicht gefunden.")
        existing = self.session.exec(
            select(WorkItemEventPaperlessLink)
            .where(col(WorkItemEventPaperlessLink.event_id) == event_id)
            .where(col(WorkItemEventPaperlessLink.document_id) == document_id)
        ).first()
        if existing is not None:
            return self._read(existing)
        connector = self._connector()
        try:
            document = connector.get_document(document_id)
        except PaperlessConnectorError as exc:
            raise PaperlessServiceError(str(exc)) from exc
        record = WorkItemEventPaperlessLink(
            event_id=event_id,
            document_id=document.document_id,
            title=document.title,
            created_date=document.created,
            original_file_name=document.original_file_name,
        )
        self.session.add(record)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            existing = self.session.exec(
                select(WorkItemEventPaperlessLink)
                .where(col(WorkItemEventPaperlessLink.event_id) == event_id)
                .where(col(WorkItemEventPaperlessLink.document_id) == document_id)
            ).first()
            if existing is None:
                raise
            return self._read(existing)
        self.session.refresh(record)
        return self._read(record)

    def unlink(self, event_id: UUID, link_id: UUID) -> None:
        record = self.session.get(WorkItemEventPaperlessLink, link_id)
        if record is None or record.event_id != event_id:
            raise PaperlessServiceError("Paperless-Verknüpfung wurde nicht gefunden.")
        self.session.delete(record)
        self.session.commit()

    def list_for_event(self, event_id: UUID) -> list[WorkPaperlessLinkRead]:
        records = self.session.exec(
            select(WorkItemEventPaperlessLink)
            .where(col(WorkItemEventPaperlessLink.event_id) == event_id)
            .order_by(col(WorkItemEventPaperlessLink.created_at))
        ).all()
        return [self._read(record) for record in records]

    def _read(self, record: WorkItemEventPaperlessLink) -> WorkPaperlessLinkRead:
        setting = self.settings.get_integration("paperless")
        configured_url = setting.browser_url or setting.base_url if setting else None
        source_url = (
            f"{configured_url.rstrip('/')}/documents/{record.document_id}/details"
            if configured_url
            else None
        )
        return WorkPaperlessLinkRead(
            id=record.id,
            event_id=record.event_id,
            document_id=record.document_id,
            title=record.title,
            created_date=record.created_date,
            original_file_name=record.original_file_name,
            source_url=source_url,
            created_at=record.created_at,
        )
