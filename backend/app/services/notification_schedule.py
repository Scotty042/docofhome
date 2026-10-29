import asyncio
import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from app.db.session import engine
from app.services.notifications import PushService

logger = logging.getLogger(__name__)


async def notification_scheduler_loop() -> None:
    def tick() -> None:
        try:
            with Session(engine) as session:
                PushService(session).run_once()
        except (SQLAlchemyError, ValueError, OSError):
            logger.warning("Push-Prüfung fehlgeschlagen; erneuter Versuch beim nächsten Lauf")

    while True:
        await asyncio.to_thread(tick)
        await asyncio.sleep(60)
