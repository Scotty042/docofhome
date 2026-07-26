from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401
from app.models.asset_engine import Asset, AssetType
from app.models.knowledge import WikiPage
from app.models.work import WorkItem
from app.services.quality import QualityService


@pytest.fixture
def quality_session(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'quality.sqlite3'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_quality_report_detects_missing_data_and_overdue_work(quality_session: Session) -> None:
    asset_type = AssetType(name="Gerät", code_prefix="GER")
    quality_session.add(asset_type)
    quality_session.flush()
    quality_session.add(
        Asset(name="Unvollständiges Gerät", jarvis_code="GER-0001", asset_type_id=asset_type.id)
    )
    quality_session.add(WikiPage(title="Leere Seite", slug="leere-seite", content=""))
    quality_session.add(
        WorkItem(
            item_type="task",
            title="Überfällige Aufgabe",
            due_at=datetime.now(UTC) - timedelta(days=1),
        )
    )
    quality_session.commit()

    report = QualityService(quality_session).run(trigger="manual")
    codes = {issue.code for issue in report.issues}
    assert "asset_missing_location" in codes
    assert "wiki_page_empty" in codes
    assert "work_item_overdue" in codes
    assert report.error_count == 1
    assert report.score < 100
    assert QualityService(quality_session).latest().id == report.id
