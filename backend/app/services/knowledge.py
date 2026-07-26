from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime
from uuid import UUID

from sqlmodel import Session, select

from app.models.asset_engine import Asset, Location
from app.models.electrical import (
    ElectricalComponent,
    ElectricalDistribution,
    ElectricalProtectiveDevice,
)
from app.models.electrical_circuit import ElectricalCircuit
from app.models.knowledge import DomainNote, WikiPage
from app.schemas.knowledge import (
    KnowledgeTargetType,
    NoteCreate,
    NoteRead,
    NoteUpdate,
    WikiPageCreate,
    WikiPageRead,
    WikiPageUpdate,
)


class KnowledgeError(RuntimeError):
    pass


class KnowledgeNotFoundError(KnowledgeError):
    pass


class KnowledgeConflictError(KnowledgeError):
    pass


class KnowledgeValidationError(KnowledgeError):
    pass


_TARGET_MODELS = {
    KnowledgeTargetType.ASSET: Asset,
    KnowledgeTargetType.LOCATION: Location,
    KnowledgeTargetType.DISTRIBUTION: ElectricalDistribution,
    KnowledgeTargetType.PROTECTIVE_DEVICE: ElectricalProtectiveDevice,
    KnowledgeTargetType.CIRCUIT: ElectricalCircuit,
}


def require_domain_target(
    session: Session,
    target_type: KnowledgeTargetType,
    target_id: UUID,
    *,
    include_deleted: bool,
) -> object:
    record = session.get(_TARGET_MODELS[target_type], target_id)
    if record is None:
        raise KnowledgeValidationError("Das verknüpfte Objekt wurde nicht gefunden")
    deleted_at = getattr(record, "deleted_at", None)
    if target_type in {
        KnowledgeTargetType.DISTRIBUTION,
        KnowledgeTargetType.PROTECTIVE_DEVICE,
    }:
        component = session.get(ElectricalComponent, target_id)
        deleted_at = component.deleted_at if component is not None else None
    if not include_deleted and deleted_at is not None:
        raise KnowledgeValidationError("Archivierte Objekte können nicht mehr geändert werden")
    return record


class WikiService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(
        self,
        *,
        search: str | None = None,
        include_archived: bool = False,
    ) -> list[WikiPageRead]:
        statement = select(WikiPage)
        if not include_archived:
            statement = statement.where(WikiPage.deleted_at.is_(None))
        pages = list(self.session.exec(statement).all())
        reads = [self._read(page, pages=pages) for page in pages]
        if search and search.strip():
            needle = search.strip().casefold()
            reads = [
                page
                for page in reads
                if needle in page.title.casefold()
                or needle in page.content.casefold()
                or needle in page.path.casefold()
            ]
        return self._hierarchy_order(reads)

    @staticmethod
    def _hierarchy_order(pages: list[WikiPageRead]) -> list[WikiPageRead]:
        by_parent: dict[UUID | None, list[WikiPageRead]] = {}
        known_ids = {page.id for page in pages}
        for page in pages:
            parent_id = page.parent_id if page.parent_id in known_ids else None
            by_parent.setdefault(parent_id, []).append(page)
        for siblings in by_parent.values():
            siblings.sort(key=lambda page: (page.sort_order, page.title.casefold()))

        ordered: list[WikiPageRead] = []
        visited: set[UUID] = set()

        def append_children(parent_id: UUID | None) -> None:
            for page in by_parent.get(parent_id, []):
                if page.id in visited:
                    continue
                visited.add(page.id)
                ordered.append(page)
                append_children(page.id)

        append_children(None)
        for page in pages:
            if page.id not in visited:
                ordered.append(page)
        return ordered

    def get(self, page_id: UUID, *, include_archived: bool = False) -> WikiPageRead:
        page = self._require_page(page_id, include_archived=include_archived)
        pages = list(self.session.exec(select(WikiPage)).all())
        return self._read(page, pages=pages)

    def create(self, payload: WikiPageCreate) -> WikiPageRead:
        if payload.parent_id is not None:
            self._require_page(payload.parent_id, include_archived=False)
        page = WikiPage(
            parent_id=payload.parent_id,
            title=payload.title,
            slug=self._unique_slug(payload.title),
            content=payload.content,
            sort_order=payload.sort_order,
        )
        self.session.add(page)
        self.session.commit()
        self.session.refresh(page)
        return self.get(page.id)

    def update(self, page_id: UUID, payload: WikiPageUpdate) -> WikiPageRead:
        page = self._require_page(page_id, include_archived=False)
        if payload.parent_id == page.id:
            raise KnowledgeValidationError(
                "Eine Wiki-Seite kann nicht ihr eigener Elternknoten sein"
            )
        if payload.parent_id is not None:
            self._require_page(payload.parent_id, include_archived=False)
            if self._is_descendant(payload.parent_id, page.id):
                raise KnowledgeValidationError(
                    "Eine Wiki-Seite kann nicht unter sich selbst verschoben werden"
                )
        if payload.title != page.title:
            page.slug = self._unique_slug(payload.title, exclude_id=page.id)
        page.parent_id = payload.parent_id
        page.title = payload.title
        page.content = payload.content
        page.sort_order = payload.sort_order
        page.updated_at = datetime.now(UTC)
        self.session.add(page)
        self.session.commit()
        self.session.refresh(page)
        return self.get(page.id)

    def archive(self, page_id: UUID) -> None:
        page = self._require_page(page_id, include_archived=False)
        child = self.session.exec(
            select(WikiPage)
            .where(WikiPage.parent_id == page.id)
            .where(WikiPage.deleted_at.is_(None))
        ).first()
        if child is not None:
            raise KnowledgeConflictError(
                "Wiki-Seiten mit aktiven Unterseiten können nicht archiviert werden"
            )
        now = datetime.now(UTC)
        page.deleted_at = now
        page.updated_at = now
        self.session.add(page)
        self.session.commit()

    def _require_page(self, page_id: UUID, *, include_archived: bool) -> WikiPage:
        page = self.session.get(WikiPage, page_id)
        if page is None or (page.deleted_at is not None and not include_archived):
            raise KnowledgeNotFoundError("Wiki-Seite wurde nicht gefunden")
        return page

    def _is_descendant(self, candidate_parent_id: UUID, page_id: UUID) -> bool:
        current = self.session.get(WikiPage, candidate_parent_id)
        visited: set[UUID] = set()
        while current is not None and current.id not in visited:
            if current.id == page_id:
                return True
            visited.add(current.id)
            current = self.session.get(WikiPage, current.parent_id) if current.parent_id else None
        return False

    def _unique_slug(self, title: str, *, exclude_id: UUID | None = None) -> str:
        normalized = unicodedata.normalize("NFKD", title)
        ascii_title = "".join(
            character for character in normalized if not unicodedata.combining(character)
        )
        base = re.sub(r"[^a-z0-9]+", "-", ascii_title.casefold()).strip("-") or "seite"
        base = base[:180]
        candidate = base
        suffix = 2
        while True:
            statement = (
                select(WikiPage)
                .where(WikiPage.slug == candidate)
                .where(WikiPage.deleted_at.is_(None))
            )
            existing = self.session.exec(statement).first()
            if existing is None or existing.id == exclude_id:
                return candidate
            candidate = f"{base[:170]}-{suffix}"
            suffix += 1

    def _read(self, page: WikiPage, *, pages: list[WikiPage]) -> WikiPageRead:
        by_id = {item.id: item for item in pages}
        parts = [page.title]
        depth = 0
        parent_id = page.parent_id
        visited = {page.id}
        while parent_id is not None and parent_id not in visited:
            parent = by_id.get(parent_id)
            if parent is None:
                break
            visited.add(parent.id)
            parts.append(parent.title)
            parent_id = parent.parent_id
            depth += 1
        return WikiPageRead(
            id=page.id,
            parent_id=page.parent_id,
            title=page.title,
            slug=page.slug,
            content=page.content,
            path=" / ".join(reversed(parts)),
            depth=depth,
            sort_order=page.sort_order,
            archived=page.deleted_at is not None,
            created_at=page.created_at,
            updated_at=page.updated_at,
        )


class NoteService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self, target_type: KnowledgeTargetType, target_id: UUID) -> list[NoteRead]:
        require_domain_target(self.session, target_type, target_id, include_deleted=True)
        records = self.session.exec(
            select(DomainNote)
            .where(DomainNote.target_type == target_type.value)
            .where(DomainNote.target_id == target_id)
            .where(DomainNote.deleted_at.is_(None))
            .order_by(DomainNote.created_at.desc())
        ).all()
        return [self._read(record) for record in records]

    def create(self, payload: NoteCreate) -> NoteRead:
        require_domain_target(
            self.session,
            payload.target_type,
            payload.target_id,
            include_deleted=False,
        )
        record = DomainNote(
            target_type=payload.target_type.value,
            target_id=payload.target_id,
            content=payload.content,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._read(record)

    def update(self, note_id: UUID, payload: NoteUpdate) -> NoteRead:
        record = self._require_note(note_id)
        target_type = KnowledgeTargetType(record.target_type)
        require_domain_target(self.session, target_type, record.target_id, include_deleted=False)
        record.content = payload.content
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._read(record)

    def delete(self, note_id: UUID) -> None:
        record = self._require_note(note_id)
        target_type = KnowledgeTargetType(record.target_type)
        require_domain_target(self.session, target_type, record.target_id, include_deleted=False)
        now = datetime.now(UTC)
        record.deleted_at = now
        record.updated_at = now
        self.session.add(record)
        self.session.commit()

    def _require_note(self, note_id: UUID) -> DomainNote:
        record = self.session.get(DomainNote, note_id)
        if record is None or record.deleted_at is not None:
            raise KnowledgeNotFoundError("Notiz wurde nicht gefunden")
        return record

    @staticmethod
    def _read(record: DomainNote) -> NoteRead:
        return NoteRead(
            id=record.id,
            target_type=KnowledgeTargetType(record.target_type),
            target_id=record.target_id,
            content=record.content,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
