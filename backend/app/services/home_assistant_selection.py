import re

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.repositories.home_assistant_selection import HomeAssistantSelectionRepository
from app.schemas.home_assistant import (
    HomeAssistantSelectionMode,
    HomeAssistantSelectionRead,
    HomeAssistantSelectionWrite,
)

ENTITY_ID_PATTERN = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")
MAX_SELECTED_ENTITY_IDS = 10_000


class HomeAssistantSelectionError(RuntimeError):
    """Raised when a Home Assistant entity selection cannot be stored."""


class HomeAssistantSelectionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = HomeAssistantSelectionRepository(session)

    def get(self) -> HomeAssistantSelectionRead:
        return self._to_read()

    def replace(self, payload: HomeAssistantSelectionWrite) -> HomeAssistantSelectionRead:
        if len(payload.entity_ids) > MAX_SELECTED_ENTITY_IDS:
            raise HomeAssistantSelectionError(
                f"Es dürfen höchstens {MAX_SELECTED_ENTITY_IDS} Entitäten ausgewählt werden."
            )
        entity_ids = tuple(sorted({self._normalize_entity_id(item) for item in payload.entity_ids}))
        try:
            self.repository.replace(mode=payload.mode.value, entity_ids=entity_ids)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise HomeAssistantSelectionError(
                "Die Home-Assistant-Entitätsauswahl konnte nicht gespeichert werden."
            ) from exc
        return self._to_read()

    def _to_read(self) -> HomeAssistantSelectionRead:
        state = self.repository.read()
        return HomeAssistantSelectionRead(
            mode=HomeAssistantSelectionMode(state.mode),
            entity_ids=list(state.entity_ids),
            selected_count=len(state.entity_ids),
            updated_at=state.updated_at,
        )

    @staticmethod
    def _normalize_entity_id(value: str) -> str:
        normalized = value.strip()
        if len(normalized) > 255 or ENTITY_ID_PATTERN.fullmatch(normalized) is None:
            raise HomeAssistantSelectionError(
                f"Ungültige Home-Assistant-Entitäts-ID: {normalized or '(leer)'}"
            )
        return normalized
