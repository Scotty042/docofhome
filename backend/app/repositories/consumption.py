from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_
from sqlmodel import Session, col, select

from app.models.consumption import (
    ConsumptionMeter,
    ConsumptionNote,
    ConsumptionReading,
    ConsumptionSetting,
)


class ConsumptionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_meter(
        self, meter_id: UUID, *, include_archived: bool = False
    ) -> ConsumptionMeter | None:
        meter = self.session.get(ConsumptionMeter, meter_id)
        if meter is None:
            return None
        if not include_archived and meter.deleted_at is not None:
            return None
        return meter

    def list_meters(
        self,
        *,
        search: str | None = None,
        meter_type: str | None = None,
        asset_id: UUID | None = None,
        location_id: UUID | None = None,
        include_archived: bool = False,
    ) -> list[ConsumptionMeter]:
        statement = select(ConsumptionMeter)
        if not include_archived:
            statement = statement.where(col(ConsumptionMeter.deleted_at).is_(None))
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    col(ConsumptionMeter.name).ilike(pattern),
                    col(ConsumptionMeter.serial_number).ilike(pattern),
                    col(ConsumptionMeter.home_assistant_entity_id).ilike(pattern),
                    col(ConsumptionMeter.notes).ilike(pattern),
                )
            )
        if meter_type:
            statement = statement.where(ConsumptionMeter.meter_type == meter_type)
        if asset_id:
            statement = statement.where(ConsumptionMeter.asset_id == asset_id)
        if location_id:
            statement = statement.where(ConsumptionMeter.location_id == location_id)
        statement = statement.order_by(
            col(ConsumptionMeter.deleted_at).is_not(None),
            ConsumptionMeter.sort_order,
            ConsumptionMeter.name,
        )
        return list(self.session.exec(statement).all())

    def find_meter_by_name(
        self, name: str, *, include_archived: bool = False
    ) -> ConsumptionMeter | None:
        statement = select(ConsumptionMeter).where(
            func.lower(ConsumptionMeter.name) == name.casefold()
        )
        if not include_archived:
            statement = statement.where(col(ConsumptionMeter.deleted_at).is_(None))
        return self.session.exec(statement).first()

    def active_main_water_meter(self, *, exclude_id: UUID | None = None) -> ConsumptionMeter | None:
        statement = select(ConsumptionMeter).where(
            ConsumptionMeter.water_role == "main",
            col(ConsumptionMeter.deleted_at).is_(None),
        )
        if exclude_id:
            statement = statement.where(ConsumptionMeter.id != exclude_id)
        return self.session.exec(statement).first()

    def active_primary_meter(
        self,
        meter_type: str,
        *,
        exclude_id: UUID | None = None,
    ) -> ConsumptionMeter | None:
        statement = select(ConsumptionMeter).where(
            ConsumptionMeter.meter_type == meter_type,
            ConsumptionMeter.primary_for_dashboard.is_(True),
            col(ConsumptionMeter.deleted_at).is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(ConsumptionMeter.id != exclude_id)
        return self.session.exec(statement).first()

    def active_dashboard_meters(self, meter_type: str) -> list[ConsumptionMeter]:
        statement = (
            select(ConsumptionMeter)
            .where(
                ConsumptionMeter.meter_type == meter_type,
                ConsumptionMeter.primary_for_dashboard.is_(True),
                col(ConsumptionMeter.deleted_at).is_(None),
            )
            .order_by(ConsumptionMeter.sort_order, ConsumptionMeter.name)
        )
        return list(self.session.exec(statement).all())

    def first_active_meter_by_type(self, meter_type: str) -> ConsumptionMeter | None:
        statement = (
            select(ConsumptionMeter)
            .where(
                ConsumptionMeter.meter_type == meter_type,
                col(ConsumptionMeter.deleted_at).is_(None),
            )
            .order_by(ConsumptionMeter.sort_order, ConsumptionMeter.name)
        )
        return self.session.exec(statement).first()

    def clear_primary_for_type(
        self, meter_type: str, *, exclude_id: UUID | None = None
    ) -> None:
        statement = select(ConsumptionMeter).where(
            ConsumptionMeter.meter_type == meter_type,
            ConsumptionMeter.primary_for_dashboard.is_(True),
            col(ConsumptionMeter.deleted_at).is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(ConsumptionMeter.id != exclude_id)
        for record in self.session.exec(statement).all():
            record.primary_for_dashboard = False
            self.session.add(record)

    def get_reading(
        self, reading_id: UUID, *, include_archived: bool = False
    ) -> ConsumptionReading | None:
        reading = self.session.get(ConsumptionReading, reading_id)
        if reading is None:
            return None
        if not include_archived and reading.deleted_at is not None:
            return None
        return reading

    def list_readings(
        self,
        *,
        meter_id: UUID | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = 500,
        ascending: bool = False,
    ) -> list[ConsumptionReading]:
        statement = select(ConsumptionReading).where(col(ConsumptionReading.deleted_at).is_(None))
        if meter_id:
            statement = statement.where(ConsumptionReading.meter_id == meter_id)
        if start:
            statement = statement.where(ConsumptionReading.measured_at >= start)
        if end:
            statement = statement.where(ConsumptionReading.measured_at < end)
        order = (
            ConsumptionReading.measured_at.asc()
            if ascending
            else ConsumptionReading.measured_at.desc()
        )
        statement = statement.order_by(
            order,
            ConsumptionReading.id.asc() if ascending else ConsumptionReading.id.desc(),
        )
        if limit is not None:
            statement = statement.limit(limit)
        return list(self.session.exec(statement).all())

    def readings_for_calculation(
        self, meter_id: UUID, start: datetime, end: datetime
    ) -> list[ConsumptionReading]:
        previous = self.session.exec(
            select(ConsumptionReading)
            .where(
                ConsumptionReading.meter_id == meter_id,
                col(ConsumptionReading.deleted_at).is_(None),
                ConsumptionReading.measured_at <= start,
            )
            .order_by(ConsumptionReading.measured_at.desc(), ConsumptionReading.id.desc())
            .limit(1)
        ).first()
        inside = list(
            self.session.exec(
                select(ConsumptionReading)
                .where(
                    ConsumptionReading.meter_id == meter_id,
                    col(ConsumptionReading.deleted_at).is_(None),
                    ConsumptionReading.measured_at > start,
                    ConsumptionReading.measured_at < end,
                )
                .order_by(ConsumptionReading.measured_at, ConsumptionReading.id)
            ).all()
        )
        following = self.session.exec(
            select(ConsumptionReading)
            .where(
                ConsumptionReading.meter_id == meter_id,
                col(ConsumptionReading.deleted_at).is_(None),
                ConsumptionReading.measured_at >= end,
            )
            .order_by(ConsumptionReading.measured_at, ConsumptionReading.id)
            .limit(1)
        ).first()
        rows: list[ConsumptionReading] = []
        seen: set[UUID] = set()
        for row in [previous, *inside, following]:
            if row is not None and row.id not in seen:
                rows.append(row)
                seen.add(row.id)
        rows.sort(key=lambda item: (item.measured_at, item.id.int))
        return rows

    def previous_reading(
        self,
        meter_id: UUID,
        measured_at: datetime,
        *,
        exclude_id: UUID | None = None,
    ) -> ConsumptionReading | None:
        statement = (
            select(ConsumptionReading)
            .where(
                ConsumptionReading.meter_id == meter_id,
                col(ConsumptionReading.deleted_at).is_(None),
                ConsumptionReading.measured_at < measured_at,
            )
            .order_by(ConsumptionReading.measured_at.desc(), ConsumptionReading.id.desc())
            .limit(1)
        )
        if exclude_id:
            statement = statement.where(ConsumptionReading.id != exclude_id)
        return self.session.exec(statement).first()

    def duplicate_reading(
        self,
        meter_id: UUID,
        measured_at: datetime,
        *,
        exclude_id: UUID | None = None,
    ) -> ConsumptionReading | None:
        statement = select(ConsumptionReading).where(
            ConsumptionReading.meter_id == meter_id,
            ConsumptionReading.measured_at == measured_at,
            col(ConsumptionReading.deleted_at).is_(None),
        )
        if exclude_id:
            statement = statement.where(ConsumptionReading.id != exclude_id)
        return self.session.exec(statement).first()

    def reading_count(self, meter_id: UUID | None = None) -> int:
        statement = (
            select(func.count())
            .select_from(ConsumptionReading)
            .where(col(ConsumptionReading.deleted_at).is_(None))
        )
        if meter_id:
            statement = statement.where(ConsumptionReading.meter_id == meter_id)
        return int(self.session.exec(statement).one())

    def reading_count_since(self, start: datetime) -> int:
        statement = (
            select(func.count())
            .select_from(ConsumptionReading)
            .where(
                col(ConsumptionReading.deleted_at).is_(None),
                ConsumptionReading.measured_at >= start,
            )
        )
        return int(self.session.exec(statement).one())

    def latest_reading(self, meter_id: UUID | None = None) -> ConsumptionReading | None:
        statement = select(ConsumptionReading).where(col(ConsumptionReading.deleted_at).is_(None))
        if meter_id:
            statement = statement.where(ConsumptionReading.meter_id == meter_id)
        return self.session.exec(
            statement.order_by(
                ConsumptionReading.measured_at.desc(), ConsumptionReading.id.desc()
            ).limit(1)
        ).first()

    def recent_readings_before(
        self,
        meter_id: UUID,
        measured_at: datetime,
        *,
        limit: int = 14,
        exclude_id: UUID | None = None,
    ) -> list[ConsumptionReading]:
        statement = (
            select(ConsumptionReading)
            .where(
                ConsumptionReading.meter_id == meter_id,
                col(ConsumptionReading.deleted_at).is_(None),
                ConsumptionReading.measured_at < measured_at,
            )
            .order_by(ConsumptionReading.measured_at.desc(), ConsumptionReading.id.desc())
            .limit(limit)
        )
        if exclude_id:
            statement = statement.where(ConsumptionReading.id != exclude_id)
        rows = list(self.session.exec(statement).all())
        rows.reverse()
        return rows

    def get_note(self, note_id: UUID) -> ConsumptionNote | None:
        note = self.session.get(ConsumptionNote, note_id)
        if note is None or note.deleted_at is not None:
            return None
        return note

    def list_notes(self, *, limit: int = 250) -> list[ConsumptionNote]:
        return list(
            self.session.exec(
                select(ConsumptionNote)
                .where(col(ConsumptionNote.deleted_at).is_(None))
                .order_by(ConsumptionNote.note_date.desc(), ConsumptionNote.created_at.desc())
                .limit(limit)
            ).all()
        )

    def get_settings(self) -> ConsumptionSetting | None:
        return self.session.get(ConsumptionSetting, 1)
