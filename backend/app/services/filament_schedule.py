import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from app.db.session import engine
from app.models.application_setting import ApplicationSetting
from app.services.filament import FilamentService

logger = logging.getLogger(__name__)


def tick() -> None:
    try:
        with Session(engine) as session:
            application = session.get(ApplicationSetting, 1)
            if application and "filament" not in json.loads(application.enabled_modules_json):
                return
            service = FilamentService(session)
            config = service.config()
            if not config.enabled:
                return
            last = service.value("last_attempt")
            if last and datetime.now(UTC) - datetime.fromisoformat(last) < timedelta(
                minutes=config.interval_minutes
            ):
                return
            service.store("last_attempt", datetime.now(UTC).isoformat())
            session.commit()
            try:
                service.sync()
            except ValueError:
                logger.warning("Filament-Cloud-Abgleich fehlgeschlagen; Details im Modulstatus")
            if config.mqtt_enabled and config.printer_serials:
                try:
                    service.refresh_mqtt()
                except ValueError:
                    logger.warning("AMS-Abfrage fehlgeschlagen; Details im Modulstatus")
    except (SQLAlchemyError, ValueError, OSError):
        logger.warning("Filament-Abgleich nicht verfügbar")


async def filament_scheduler_loop() -> None:
    while True:
        await asyncio.to_thread(tick)
        await asyncio.sleep(60)
