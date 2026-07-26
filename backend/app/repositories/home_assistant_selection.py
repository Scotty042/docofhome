from dataclasses import dataclass
from datetime import UTC, datetime

from sqlmodel import Session, col, select

from app.models.home_assistant import (
    HomeAssistantEntitySelection,
    HomeAssistantSelectionSetting,
)


@dataclass(frozen=True, slots=True)
class HomeAssistantSelectionState:
    mode: str
    entity_ids: tuple[str, ...]
    updated_at: datetime | None


class HomeAssistantSelectionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def read(self) -> HomeAssistantSelectionState:
        setting = self.session.get(HomeAssistantSelectionSetting, 1)
        if setting is None:
            return HomeAssistantSelectionState(mode="all", entity_ids=(), updated_at=None)
        statement = select(HomeAssistantEntitySelection).order_by(
            col(HomeAssistantEntitySelection.entity_id)
        )
        selections = self.session.exec(statement).all()
        return HomeAssistantSelectionState(
            mode=setting.mode,
            entity_ids=tuple(item.entity_id for item in selections),
            updated_at=setting.updated_at,
        )

    def replace(self, *, mode: str, entity_ids: tuple[str, ...]) -> None:
        now = datetime.now(UTC)
        setting = self.session.get(HomeAssistantSelectionSetting, 1)
        if setting is None:
            setting = HomeAssistantSelectionSetting(
                id=1,
                mode=mode,
                created_at=now,
                updated_at=now,
            )
        else:
            setting.mode = mode
            setting.updated_at = now
        self.session.add(setting)
        self.session.flush()

        existing = self.session.exec(select(HomeAssistantEntitySelection)).all()
        for item in existing:
            self.session.delete(item)
        self.session.flush()

        for entity_id in entity_ids:
            self.session.add(
                HomeAssistantEntitySelection(
                    setting_id=1,
                    entity_id=entity_id,
                    created_at=now,
                )
            )
