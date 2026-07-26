from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401
from app.models.asset_engine import Asset, AssetType
from app.schemas.knowledge import (
    KnowledgeTargetType,
    NoteCreate,
    NoteUpdate,
    WikiPageCreate,
    WikiPageUpdate,
)
from app.services.knowledge import KnowledgeValidationError, NoteService, WikiService


@pytest.fixture
def knowledge_session(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'knowledge.sqlite3'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def create_asset(session: Session) -> Asset:
    asset_type = AssetType(name="Heizung", code_prefix="HZG")
    session.add(asset_type)
    session.flush()
    asset = Asset(name="Wärmepumpe", jarvis_code="HZG-0001", asset_type_id=asset_type.id)
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def test_wiki_hierarchy_and_notes(knowledge_session: Session) -> None:
    wiki = WikiService(knowledge_session)
    root = wiki.create(WikiPageCreate(title="Heizung", content="Grundlagen"))
    child = wiki.create(
        WikiPageCreate(title="Filterwechsel", content="Alle sechs Monate", parent_id=root.id)
    )

    assert child.path == "Heizung / Filterwechsel"
    assert child.depth == 1
    assert [page.title for page in wiki.list(search="sechs")] == ["Filterwechsel"]

    with pytest.raises(KnowledgeValidationError):
        wiki.update(
            root.id,
            WikiPageUpdate(title="Heizung", content="Grundlagen", parent_id=child.id),
        )

    wiki.archive(child.id)
    assert [page.title for page in wiki.list()] == ["Heizung"]
    archived = wiki.get(child.id, include_archived=True)
    assert archived.archived is True
    assert archived.path == "Heizung / Filterwechsel"
    assert {page.title for page in wiki.list(include_archived=True)} == {
        "Heizung",
        "Filterwechsel",
    }

    asset = create_asset(knowledge_session)
    notes = NoteService(knowledge_session)
    created = notes.create(
        NoteCreate(
            target_type=KnowledgeTargetType.ASSET,
            target_id=asset.id,
            content="Ersatzfilter liegen im Keller.",
        )
    )
    updated = notes.update(created.id, NoteUpdate(content="Ersatzfilter liegen links im Keller."))
    assert updated.content.endswith("Keller.")
    assert len(notes.list(KnowledgeTargetType.ASSET, asset.id)) == 1

    asset.deleted_at = datetime.now(UTC)
    knowledge_session.add(asset)
    knowledge_session.commit()
    assert len(notes.list(KnowledgeTargetType.ASSET, asset.id)) == 1
    with pytest.raises(KnowledgeValidationError):
        notes.update(created.id, NoteUpdate(content="Darf nicht geändert werden"))

    asset.deleted_at = None
    knowledge_session.add(asset)
    knowledge_session.commit()
    notes.delete(created.id)
    assert notes.list(KnowledgeTargetType.ASSET, asset.id) == []
