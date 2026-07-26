from datetime import UTC, datetime
from pathlib import PurePosixPath
from uuid import UUID

from sqlmodel import Session, select

from app.models.asset_engine import Asset, Location
from app.models.document_link import DocumentLink
from app.models.electrical import (
    ElectricalComponent,
    ElectricalDistribution,
    ElectricalProtectiveDevice,
)
from app.models.electrical_circuit import ElectricalCircuit
from app.schemas.document_links import DocumentLinkCreate, DocumentLinkRead, DocumentTargetType
from app.schemas.documents import DocumentEntryType
from app.services.documents import (
    DocumentError,
    DocumentNotFoundError,
    DocumentService,
)


class DocumentLinkError(RuntimeError):
    pass


class DocumentLinkNotFoundError(DocumentLinkError):
    pass


class DocumentLinkConflictError(DocumentLinkError):
    pass


class DocumentLinkValidationError(DocumentLinkError):
    pass


TARGET_MODELS = {
    DocumentTargetType.ASSET: Asset,
    DocumentTargetType.LOCATION: Location,
    DocumentTargetType.DISTRIBUTION: ElectricalDistribution,
    DocumentTargetType.PROTECTIVE_DEVICE: ElectricalProtectiveDevice,
    DocumentTargetType.CIRCUIT: ElectricalCircuit,
}


class DocumentLinkService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.documents = DocumentService(session)

    def list(self, target_type: DocumentTargetType, target_id: UUID) -> list[DocumentLinkRead]:
        self._require_target(target_type, target_id, include_deleted=True)
        records = self.session.exec(
            select(DocumentLink)
            .where(DocumentLink.target_type == target_type.value)
            .where(DocumentLink.target_id == target_id)
            .where(DocumentLink.deleted_at.is_(None))
            .order_by(DocumentLink.document_name, DocumentLink.created_at)
        ).all()
        return [self._read(record) for record in records]

    def create(self, payload: DocumentLinkCreate) -> DocumentLinkRead:
        self._require_target(payload.target_type, payload.target_id, include_deleted=False)
        path, name, etag = self._require_document(payload.document_path)
        duplicate = self.session.exec(
            select(DocumentLink)
            .where(DocumentLink.target_type == payload.target_type.value)
            .where(DocumentLink.target_id == payload.target_id)
            .where(DocumentLink.document_path == path)
            .where(DocumentLink.deleted_at.is_(None))
        ).first()
        if duplicate:
            raise DocumentLinkConflictError("Document is already linked to this entry")
        record = DocumentLink(
            target_type=payload.target_type.value,
            target_id=payload.target_id,
            document_path=path,
            document_name=name,
            document_etag=etag,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._read(record, available=True)

    def delete(self, link_id: UUID) -> None:
        record = self.session.get(DocumentLink, link_id)
        if not record or record.deleted_at is not None:
            raise DocumentLinkNotFoundError("Document link was not found")
        record.deleted_at = datetime.now(UTC)
        record.updated_at = record.deleted_at
        self.session.add(record)
        self.session.commit()

    def _require_target(
        self,
        target_type: DocumentTargetType,
        target_id: UUID,
        *,
        include_deleted: bool,
    ) -> None:
        model = TARGET_MODELS[target_type]
        record = self.session.get(model, target_id)
        if not record:
            raise DocumentLinkValidationError("Link target was not found")
        deleted_at = getattr(record, "deleted_at", None)
        if target_type in {
            DocumentTargetType.DISTRIBUTION,
            DocumentTargetType.PROTECTIVE_DEVICE,
        }:
            component = self.session.get(ElectricalComponent, target_id)
            deleted_at = component.deleted_at if component is not None else None
        if not include_deleted and deleted_at is not None:
            raise DocumentLinkValidationError("Archived entries cannot receive new document links")

    def _require_document(self, raw_path: str) -> tuple[str, str, str | None]:
        path = raw_path.strip().strip("/")
        if not path or "\\" in path:
            raise DocumentLinkValidationError("A valid document path is required")
        pure = PurePosixPath(path)
        if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
            raise DocumentLinkValidationError("A valid document path is required")
        parent = "/".join(pure.parts[:-1])
        try:
            listing = self.documents.list_entries(parent)
        except DocumentError as exc:
            raise DocumentLinkValidationError("Document could not be verified") from exc
        entry = next((item for item in listing.items if item.path == path), None)
        if not entry:
            raise DocumentLinkValidationError("Document was not found")
        if entry.entry_type != DocumentEntryType.FILE:
            raise DocumentLinkValidationError("Folders cannot be linked as documents")
        return path, entry.name, entry.etag

    def _available(self, record: DocumentLink) -> bool:
        try:
            path, _, _ = self._require_document(record.document_path)
            return path == record.document_path
        except (DocumentLinkValidationError, DocumentNotFoundError):
            return False

    def _read(self, record: DocumentLink, *, available: bool | None = None) -> DocumentLinkRead:
        return DocumentLinkRead(
            id=record.id,
            target_type=DocumentTargetType(record.target_type),
            target_id=record.target_id,
            document_path=record.document_path,
            document_name=record.document_name,
            document_etag=record.document_etag,
            available=self._available(record) if available is None else available,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
