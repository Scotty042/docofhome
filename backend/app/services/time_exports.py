"""Opt-in monthly work-time CSV snapshots, stored locally and optionally in Nextcloud."""

import asyncio
import csv
import io
import re
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session, col, select

from app.core.settings import settings
from app.db.session import engine
from app.models.application_setting import ApplicationSetting
from app.models.time_tracking import WorkInterval
from app.services.backups import BackupError, BackupService

_LOCK = threading.RLock()
_MONTH = r"\d{4}-(?:0[1-9]|1[0-2])"
_FILENAME = re.compile(rf"docofhome-zeiten-({_MONTH})\.csv")


class TimeExportWrite(BaseModel):
    enabled: bool = False
    upload_to_nextcloud: bool = False
    nextcloud_folder: str = Field(default="DocOfHome/Zeiterfassung", max_length=500)

    @field_validator("nextcloud_folder")
    @classmethod
    def valid_folder(cls, value: str) -> str:
        try:
            return "/".join(BackupService._clean_folder_parts(value))
        except BackupError as exc:
            raise ValueError("Ungültiger Nextcloud-Ordner.") from exc


class TimeExportState(TimeExportWrite):
    first_month: str | None = Field(default=None, pattern=rf"^{_MONTH}$")
    last_exported_month: str | None = Field(default=None, pattern=rf"^{_MONTH}$")
    last_attempt_at: datetime | None = None
    last_success_at: datetime | None = None
    last_error: str | None = None


def shifted_month(month: str, offset: int) -> str:
    date = datetime.strptime(month, "%Y-%m")
    index = date.year * 12 + date.month - 1 + offset
    year, month_index = divmod(index, 12)
    return f"{year:04d}-{month_index + 1:02d}"


def spreadsheet_text(value: str) -> str:
    # User-supplied ticket/customer/info must remain literal spreadsheet cells.
    return (
        "'" + value
        if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n"))
        else value
    )


class TimeExportService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.root = settings.data_dir / "exports" / "time-tracking"
        self.config = self.root / "config.json"

    def read(self) -> TimeExportState:
        if not self.config.exists():
            return TimeExportState()
        try:
            return TimeExportState.model_validate_json(self.config.read_text())
        except (OSError, ValueError) as exc:
            raise ValueError("Die CSV-Exportkonfiguration konnte nicht gelesen werden.") from exc

    def _persist(self, state: TimeExportState) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.config.with_suffix(".tmp")
        temporary.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(self.config)

    def _zone(self) -> ZoneInfo:
        row = self.session.get(ApplicationSetting, 1)
        return ZoneInfo(row.timezone if row else "Europe/Berlin")

    def write(self, data: TimeExportWrite, now: datetime | None = None) -> TimeExportState:
        with _LOCK:
            state = self.read().model_copy(update=data.model_dump())
            if state.enabled and state.first_month is None:
                month = (now or datetime.now(UTC)).astimezone(self._zone()).strftime("%Y-%m")
                state.first_month = shifted_month(month, -1)
            self._persist(state)
            return state

    def files(self) -> list[dict[str, Any]]:
        if not self.root.is_dir():
            return []
        return [
            {"filename": path.name, "month": match.group(1), "size_bytes": path.stat().st_size}
            for path in sorted(self.root.glob("*.csv"), reverse=True)
            if (match := _FILENAME.fullmatch(path.name)) and not path.is_symlink()
        ]

    def download(self, filename: str) -> Path:
        if not _FILENAME.fullmatch(filename):
            raise ValueError("Ungültiger CSV-Dateiname.")
        path = self.root / filename
        if path.is_symlink() or not path.is_file():
            raise FileNotFoundError("CSV-Export nicht gefunden.")
        return path

    def create(self, month: str) -> Path:
        zone = self._zone()
        start = datetime.strptime(month, "%Y-%m").replace(tzinfo=zone).timestamp()
        end = datetime.strptime(shifted_month(month, 1), "%Y-%m").replace(tzinfo=zone).timestamp()
        query = select(WorkInterval).where(
            col(WorkInterval.started_at) < end,
            col(WorkInterval.ended_at).is_(None) | (col(WorkInterval.ended_at) > start),
        )
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, delimiter=";")
        writer.writerow(
            [
                "Arbeitslauf-ID",
                "Tätigkeit/Ticketnr",
                "Kunde",
                "Weitere Info",
                "Anfang",
                "Ende",
                "DauerSekunden",
                "Dauer",
                "BCS",
                "Status",
            ]
        )
        for row in self.session.exec(
            query.order_by(col(WorkInterval.started_at), col(WorkInterval.id))
        ):
            left, right = (
                max(start, row.started_at),
                min(end, row.ended_at if row.ended_at is not None else end),
            )
            if right <= left:
                continue
            seconds = right - left
            integer = int(seconds)
            writer.writerow(
                [
                    row.id,
                    spreadsheet_text(row.ticket),
                    spreadsheet_text(row.customer),
                    spreadsheet_text(row.info),
                    datetime.fromtimestamp(left, zone).isoformat(),
                    datetime.fromtimestamp(right, zone).isoformat(),
                    f"{seconds:.3f}".rstrip("0").rstrip("."),
                    f"{integer // 3600:02d}:{integer // 60 % 60:02d}:{integer % 60:02d}",
                    int(row.bcs),
                    "läuft" if row.running else "beendet" if row.completed else "pausiert",
                ]
            )
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"docofhome-zeiten-{month}.csv"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(buffer.getvalue(), encoding="utf-8-sig", newline="")
        temporary.replace(path)
        return path

    def run_once(self, *, force: bool = False, now: datetime | None = None) -> TimeExportState:
        with _LOCK:
            state = self.read()
            if not force and not state.enabled:
                return state
            current = (now or datetime.now(UTC)).astimezone(self._zone())
            last_month = shifted_month(current.strftime("%Y-%m"), -1)
            month = (
                last_month
                if force
                else shifted_month(state.last_exported_month, 1)
                if state.last_exported_month
                else state.first_month or last_month
            )
            # Bounded catch-up; another hourly run continues after long downtime.
            for _ in range(1 if force else 12):
                if month > last_month:
                    break
                state.last_attempt_at = now or datetime.now(UTC)
                try:
                    path = self.root / f"docofhome-zeiten-{month}.csv"
                    if force or not path.exists():
                        path = self.create(month)
                    if path.is_symlink():
                        raise ValueError("Ungültiger CSV-Exportpfad.")
                    if state.upload_to_nextcloud:
                        BackupService(self.session).upload_to_nextcloud(
                            path, state.nextcloud_folder
                        )
                    if not force:
                        state.last_exported_month = month
                    state.last_success_at = now or datetime.now(UTC)
                    state.last_error = None
                except (BackupError, OSError, ValueError) as exc:
                    state.last_error = str(exc)
                    self._persist(state)
                    break
                self._persist(state)
                month = shifted_month(month, 1)
            return state


async def time_export_scheduler_loop() -> None:
    def run() -> None:
        try:
            with Session(engine) as session:
                TimeExportService(session).run_once()
        except Exception:
            # Keep this independent from all other maintenance tasks.
            import logging

            logging.getLogger(__name__).exception("Monatlicher CSV-Export fehlgeschlagen")

    while True:
        await asyncio.to_thread(run)
        await asyncio.sleep(3600)
