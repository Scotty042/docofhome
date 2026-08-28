import asyncio

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from app.db.session import engine
from app.services.docker_sync import DockerSyncError, DockerSyncService


class DockerSyncScheduler:
    def run_once(self) -> bool:
        try:
            with Session(engine) as session:
                service = DockerSyncService(session)
                if not service.is_due():
                    return False
                service.sync()
            return True
        except (DockerSyncError, SQLAlchemyError, OSError):
            return False


async def docker_sync_scheduler_loop() -> None:
    scheduler = DockerSyncScheduler()
    while True:
        await asyncio.to_thread(scheduler.run_once)
        # The shortest supported interval is 30 seconds.
        await asyncio.sleep(30)
