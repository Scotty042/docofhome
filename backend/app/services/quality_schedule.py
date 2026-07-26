import asyncio

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from app.db.session import engine
from app.repositories.settings import SettingsRepository
from app.services.quality import QualityError, QualityService


class QualityScheduler:
    def run_once(self, *, force: bool = False) -> bool:
        try:
            with Session(engine) as session:
                setting = SettingsRepository(session).get_application()
                if setting is None or setting.setup_completed_at is None:
                    return False
                service = QualityService(session)
                if not force and not service.is_due():
                    return False
                service.run(trigger="scheduled")
            return True
        except (QualityError, SQLAlchemyError):
            return False


async def quality_scheduler_loop() -> None:
    scheduler = QualityScheduler()
    while True:
        await asyncio.to_thread(scheduler.run_once)
        await asyncio.sleep(3600)
