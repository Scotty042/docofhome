from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401
from app.models.asset_engine import Asset, AssetType
from app.schemas.knowledge import KnowledgeTargetType
from app.schemas.work import (
    WorkCompletionWrite,
    WorkItemType,
    WorkItemWrite,
    WorkPriority,
    WorkStatus,
)
from app.services.work import WorkService, WorkValidationError


@pytest.fixture
def work_session(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'work.sqlite3'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_recurring_maintenance_advances_and_keeps_history(work_session: Session) -> None:
    due = datetime.now(UTC) - timedelta(days=10)
    service = WorkService(work_session)
    item = service.create(
        WorkItemWrite(
            item_type=WorkItemType.MAINTENANCE,
            title="Filter wechseln",
            due_at=due,
            recurrence_days=7,
            priority=WorkPriority.HIGH,
        )
    )
    assert item.overdue is True

    completed = service.complete(item.id, WorkCompletionWrite(note="Filter ersetzt"))
    assert completed.status == WorkStatus.OPEN
    assert completed.due_at is not None and completed.due_at > datetime.now(UTC)
    events = service.events(item.id)
    assert events[0].event_type == "completed"
    assert events[0].due_at_after == completed.due_at


def test_one_off_task_is_completed_and_summary_counts_overdue(work_session: Session) -> None:
    service = WorkService(work_session)
    overdue = service.create(
        WorkItemWrite(
            item_type=WorkItemType.TASK,
            title="Prüfprotokoll ergänzen",
            due_at=datetime.now(UTC) - timedelta(days=1),
        )
    )
    assert service.summary().overdue == 1
    completed = service.complete(overdue.id, WorkCompletionWrite())
    assert completed.status == WorkStatus.COMPLETED
    assert service.summary().overdue == 0


def test_archived_target_keeps_existing_work_but_rejects_new_entries(
    work_session: Session,
) -> None:
    asset_type = AssetType(name="Heizung", code_prefix="HZG")
    work_session.add(asset_type)
    work_session.flush()
    asset = Asset(name="Wärmepumpe", jarvis_code="HZG-0001", asset_type_id=asset_type.id)
    work_session.add(asset)
    work_session.commit()

    service = WorkService(work_session)
    item = service.create(
        WorkItemWrite(
            item_type=WorkItemType.MAINTENANCE,
            title="Filter prüfen",
            target_type=KnowledgeTargetType.ASSET,
            target_id=asset.id,
            due_at=datetime.now(UTC) + timedelta(days=30),
        )
    )
    asset.deleted_at = datetime.now(UTC)
    work_session.add(asset)
    work_session.commit()

    updated = service.update(
        item.id,
        WorkItemWrite(
            item_type=WorkItemType.MAINTENANCE,
            title="Filter und Dichtung prüfen",
            target_type=KnowledgeTargetType.ASSET,
            target_id=asset.id,
            due_at=item.due_at,
        ),
    )
    assert updated.title == "Filter und Dichtung prüfen"
    with pytest.raises(WorkValidationError):
        service.create(
            WorkItemWrite(
                item_type=WorkItemType.TASK,
                title="Neue Aufgabe",
                target_type=KnowledgeTargetType.ASSET,
                target_id=asset.id,
            )
        )
