import asyncio
import json
from contextlib import suppress
from datetime import UTC, datetime, timedelta

from sqlmodel import Session

from app.core.settings import settings
from app.db.session import engine
from app.schemas.backups import BackupScheduleRead, BackupScheduleWrite
from app.services.backups import BackupError, BackupService


class BackupScheduleStore:
    def __init__(self) -> None:
        self.path = settings.data_dir / "backups" / "config.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def read(self) -> BackupScheduleRead:
        if not self.path.is_file():
            return BackupScheduleRead()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return BackupScheduleRead.model_validate(payload)
        except (OSError, json.JSONDecodeError, ValueError):
            return BackupScheduleRead(
                last_error="Die Backup-Konfiguration war ungültig und wurde ignoriert."
            )

    def write(self, configuration: BackupScheduleWrite) -> BackupScheduleRead:
        current = self.read()
        updated = BackupScheduleRead(
            **configuration.model_dump(),
            last_attempt_at=current.last_attempt_at,
            last_success_at=current.last_success_at,
            last_error=current.last_error,
        )
        self._persist(updated)
        return updated

    def mark_result(
        self,
        *,
        success: bool,
        message: str | None = None,
    ) -> BackupScheduleRead:
        current = self.read()
        now = datetime.now(UTC)
        updated = current.model_copy(
            update={
                "last_attempt_at": now,
                "last_success_at": now if success else current.last_success_at,
                "last_error": None if success else message,
            }
        )
        self._persist(updated)
        return updated

    def _persist(self, configuration: BackupScheduleRead) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            configuration.model_dump_json(indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)


class BackupScheduler:
    def __init__(self, store: BackupScheduleStore | None = None) -> None:
        self.store = store or BackupScheduleStore()

    def run_once(self, *, force: bool = False) -> bool:
        configuration = self.store.read()
        if not force and (not configuration.enabled or not self._is_due(configuration)):
            return False
        try:
            with Session(engine) as session:
                service = BackupService(session)
                service.create_backup(
                    upload_to_nextcloud=configuration.upload_to_nextcloud,
                    nextcloud_folder=configuration.nextcloud_folder,
                )
                self._apply_retention(service, configuration.retention_count)
            self.store.mark_result(success=True)
        except (BackupError, OSError) as exc:
            self.store.mark_result(success=False, message=str(exc))
        return True

    @staticmethod
    def _is_due(configuration: BackupScheduleRead) -> bool:
        if configuration.last_attempt_at is None:
            return True
        last_attempt = configuration.last_attempt_at
        if last_attempt.tzinfo is None:
            last_attempt = last_attempt.replace(tzinfo=UTC)
        interval = timedelta(hours=configuration.interval_hours)
        return datetime.now(UTC) >= last_attempt + interval

    @staticmethod
    def _apply_retention(service: BackupService, retention_count: int) -> None:
        records = service.list_backups()
        for record in records[retention_count:]:
            path = service.backup_dir / record.filename
            with suppress(FileNotFoundError):
                path.unlink()


async def backup_scheduler_loop() -> None:
    scheduler = BackupScheduler()
    while True:
        await asyncio.to_thread(scheduler.run_once)
        await asyncio.sleep(3600)
