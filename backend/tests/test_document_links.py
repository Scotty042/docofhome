from uuid import uuid4

import pytest
from sqlmodel import Session

from app.models.asset_engine import Asset, AssetType
from app.schemas.document_links import DocumentLinkCreate, DocumentTargetType
from app.services.document_links import (
    DocumentLinkConflictError,
    DocumentLinkService,
    DocumentLinkValidationError,
)


def create_asset(session: Session) -> Asset:
    asset_type = AssetType(name="Test", code_prefix="TST")
    session.add(asset_type)
    session.commit()
    session.refresh(asset_type)
    asset = Asset(name="Pumpe", jarvis_code="TST-0001", asset_type_id=asset_type.id)
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def test_create_list_and_delete_document_link(
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asset = create_asset(session)
    service = DocumentLinkService(session)
    monkeypatch.setattr(
        service,
        "_require_document",
        lambda path: (path, "Anleitung.pdf", '"etag"'),
    )

    created = service.create(
        DocumentLinkCreate(
            target_type=DocumentTargetType.ASSET,
            target_id=asset.id,
            document_path="Anleitungen/Anleitung.pdf",
        )
    )
    assert created.available is True
    assert created.document_name == "Anleitung.pdf"

    monkeypatch.setattr(DocumentLinkService, "_available", lambda self, record: True)
    listed = DocumentLinkService(session).list(DocumentTargetType.ASSET, asset.id)
    assert [item.id for item in listed] == [created.id]

    DocumentLinkService(session).delete(created.id)
    assert DocumentLinkService(session).list(DocumentTargetType.ASSET, asset.id) == []


def test_duplicate_link_is_rejected(session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    asset = create_asset(session)
    service = DocumentLinkService(session)
    monkeypatch.setattr(service, "_require_document", lambda path: (path, "Plan.pdf", None))
    payload = DocumentLinkCreate(
        target_type=DocumentTargetType.ASSET,
        target_id=asset.id,
        document_path="Plan.pdf",
    )
    service.create(payload)
    with pytest.raises(DocumentLinkConflictError):
        service.create(payload)


def test_missing_target_is_rejected(session: Session) -> None:
    with pytest.raises(DocumentLinkValidationError):
        DocumentLinkService(session).create(
            DocumentLinkCreate(
                target_type=DocumentTargetType.LOCATION,
                target_id=uuid4(),
                document_path="Plan.pdf",
            )
        )
