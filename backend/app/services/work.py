from __future__ import annotations

import json
from calendar import monthrange
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.models.application_setting import ApplicationSetting
from app.models.asset_engine import Asset, Location
from app.models.consumption import ConsumptionMeter, ConsumptionReading
from app.models.electrical import (
    ElectricalComponent,
    ElectricalDistribution,
    ElectricalProtectiveDevice,
)
from app.models.electrical_circuit import ElectricalCircuit
from app.models.work import WorkItem, WorkItemEvent
from app.schemas.knowledge import KnowledgeTargetType
from app.schemas.work import (
    RecurrenceMode,
    WorkCompletionWrite,
    WorkItemEventRead,
    WorkItemRead,
    WorkItemType,
    WorkItemWrite,
    WorkPriority,
    WorkStatus,
    WorkSummaryRead,
)
from app.services.knowledge import KnowledgeValidationError, require_domain_target


class WorkError(RuntimeError):
    pass


class WorkNotFoundError(WorkError):
    pass


class WorkValidationError(WorkError):
    pass


class WorkConflictError(WorkError):
    pass


class WorkService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(
        self,
        *,
        status: WorkStatus | None = None,
        item_type: WorkItemType | None = None,
        target_type: KnowledgeTargetType | None = None,
        target_id: UUID | None = None,
        include_archived: bool = False,
    ) -> list[WorkItemRead]:
        self._sync_monthly_meter_tasks()
        if (target_type is None) != (target_id is None):
            raise WorkValidationError("Zieltyp und Ziel-ID müssen gemeinsam angegeben werden")
        statement = select(WorkItem)
        if not include_archived:
            statement = statement.where(WorkItem.deleted_at.is_(None))
        if status is not None:
            statement = statement.where(WorkItem.status == status.value)
        if item_type is not None:
            statement = statement.where(WorkItem.item_type == item_type.value)
        if target_type is not None and target_id is not None:
            statement = statement.where(WorkItem.target_type == target_type.value).where(
                WorkItem.target_id == target_id
            )
        records = list(self.session.exec(statement).all())
        records.sort(
            key=lambda item: (
                item.status != WorkStatus.OPEN.value,
                item.due_at is None,
                self._aware(item.due_at).timestamp() if item.due_at else float("inf"),
                item.priority != WorkPriority.HIGH.value,
                item.title.casefold(),
            )
        )
        return [self._read(record) for record in records]

    def get(self, item_id: UUID) -> WorkItemRead:
        return self._read(self._require_item(item_id))

    def create(self, payload: WorkItemWrite) -> WorkItemRead:
        self._validate_target(payload.target_type, payload.target_id)
        record = WorkItem(
            item_type=payload.item_type.value,
            title=payload.title,
            description=payload.description,
            target_type=payload.target_type.value if payload.target_type else None,
            target_id=payload.target_id,
            due_at=payload.due_at,
            recurrence_days=payload.recurrence_days,
            recurrence_mode=payload.recurrence_mode.value,
            calendar_months=payload.calendar_months,
            calendar_day=payload.calendar_day,
            calendar_month=(
                payload.calendar_month
                or (
                    payload.due_at.month
                    if payload.due_at and payload.calendar_months == 12
                    else None
                )
            ),
            calendar_last_day=payload.calendar_last_day,
            priority=payload.priority.value,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._read(record)

    def update(self, item_id: UUID, payload: WorkItemWrite) -> WorkItemRead:
        record = self._require_item(item_id)
        self._require_user_managed(record)
        if record.status != WorkStatus.OPEN.value:
            raise WorkConflictError("Nur offene Einträge können bearbeitet werden")
        same_target = (
            record.target_type == (payload.target_type.value if payload.target_type else None)
            and record.target_id == payload.target_id
        )
        self._validate_target(
            payload.target_type,
            payload.target_id,
            include_deleted=same_target,
        )
        record.item_type = payload.item_type.value
        record.title = payload.title
        record.description = payload.description
        record.target_type = payload.target_type.value if payload.target_type else None
        record.target_id = payload.target_id
        record.due_at = payload.due_at
        record.recurrence_days = payload.recurrence_days
        record.recurrence_mode = payload.recurrence_mode.value
        record.calendar_months = payload.calendar_months
        record.calendar_day = payload.calendar_day
        record.calendar_month = payload.calendar_month or (
            payload.due_at.month if payload.due_at and payload.calendar_months == 12 else None
        )
        record.calendar_last_day = payload.calendar_last_day
        record.priority = payload.priority.value
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._read(record)

    def complete(self, item_id: UUID, payload: WorkCompletionWrite) -> WorkItemRead:
        record = self._require_item(item_id)
        self._require_user_managed(record)
        if record.status != WorkStatus.OPEN.value:
            raise WorkConflictError("Nur offene Einträge können abgeschlossen werden")
        now = datetime.now(UTC)
        due_before = record.due_at
        due_after: datetime | None = None
        if (
            record.item_type == WorkItemType.MAINTENANCE.value
            and record.recurrence_mode == RecurrenceMode.INTERVAL.value
            and record.recurrence_days
        ):
            base = self._aware(record.due_at) if record.due_at else now
            due_after = base + timedelta(days=record.recurrence_days)
            while due_after <= now:
                due_after += timedelta(days=record.recurrence_days)
            record.due_at = due_after
            record.completed_at = now
        elif (
            record.item_type == WorkItemType.MAINTENANCE.value
            and record.recurrence_mode == RecurrenceMode.CALENDAR.value
        ):
            due_after = self._next_calendar_due(record, now)
            record.due_at = due_after
            record.completed_at = now
        else:
            record.status = WorkStatus.COMPLETED.value
            record.completed_at = now
        record.updated_at = now
        event = WorkItemEvent(
            work_item_id=record.id,
            event_type="completed",
            note=payload.note,
            due_at_before=due_before,
            due_at_after=due_after,
        )
        self.session.add(record)
        self.session.add(event)
        self.session.commit()
        self.session.refresh(record)
        return self._read(record)

    def cancel(self, item_id: UUID) -> WorkItemRead:
        record = self._require_item(item_id)
        self._require_user_managed(record)
        if record.status != WorkStatus.OPEN.value:
            raise WorkConflictError("Nur offene Einträge können abgebrochen werden")
        now = datetime.now(UTC)
        record.status = WorkStatus.CANCELLED.value
        record.updated_at = now
        self.session.add(record)
        self.session.add(WorkItemEvent(work_item_id=record.id, event_type="cancelled"))
        self.session.commit()
        self.session.refresh(record)
        return self._read(record)

    def reopen(self, item_id: UUID) -> WorkItemRead:
        record = self._require_item(item_id)
        self._require_user_managed(record)
        if record.status == WorkStatus.OPEN.value:
            return self._read(record)
        now = datetime.now(UTC)
        record.status = WorkStatus.OPEN.value
        record.completed_at = None
        record.updated_at = now
        self.session.add(record)
        self.session.add(WorkItemEvent(work_item_id=record.id, event_type="reopened"))
        self.session.commit()
        self.session.refresh(record)
        return self._read(record)

    def delete(self, item_id: UUID) -> None:
        record = self._require_item(item_id)
        self._require_user_managed(record)
        now = datetime.now(UTC)
        record.deleted_at = now
        record.updated_at = now
        self.session.add(record)
        self.session.commit()

    def events(self, item_id: UUID) -> list[WorkItemEventRead]:
        self._require_item(item_id)
        records = self.session.exec(
            select(WorkItemEvent)
            .where(WorkItemEvent.work_item_id == item_id)
            .order_by(WorkItemEvent.created_at.desc())
        ).all()
        return [
            WorkItemEventRead(
                id=event.id,
                work_item_id=event.work_item_id,
                event_type=event.event_type,
                note=event.note,
                due_at_before=self._aware(event.due_at_before) if event.due_at_before else None,
                due_at_after=self._aware(event.due_at_after) if event.due_at_after else None,
                created_at=self._aware(event.created_at),
            )
            for event in records
        ]

    def summary(self) -> WorkSummaryRead:
        self._sync_monthly_meter_tasks()
        records = list(
            self.session.exec(select(WorkItem).where(WorkItem.deleted_at.is_(None))).all()
        )
        now = datetime.now(UTC)
        week = now + timedelta(days=7)
        zone = self._timezone()
        today = now.astimezone(zone).date()
        return WorkSummaryRead(
            open_total=sum(item.status == WorkStatus.OPEN.value for item in records),
            overdue=sum(
                item.status == WorkStatus.OPEN.value
                and item.due_at is not None
                and self._aware(item.due_at) < now
                for item in records
            ),
            due_next_7_days=sum(
                item.status == WorkStatus.OPEN.value
                and item.due_at is not None
                and now <= self._aware(item.due_at) <= week
                for item in records
            ),
            due_next_3_days=sum(
                item.status == WorkStatus.OPEN.value
                and item.due_at is not None
                and 0 <= (self._aware(item.due_at).astimezone(zone).date() - today).days <= 3
                for item in records
            ),
            due_today=sum(
                item.status == WorkStatus.OPEN.value
                and item.due_at is not None
                and self._aware(item.due_at).astimezone(zone).date() == today
                for item in records
            ),
            completed_total=sum(item.status == WorkStatus.COMPLETED.value for item in records),
        )

    def upcoming(self, *, days: int = 3) -> list[WorkItemRead]:
        if days < 0 or days > 31:
            raise WorkValidationError("Der Fälligkeitshorizont muss zwischen 0 und 31 Tagen liegen")
        return [
            item
            for item in self.list(status=WorkStatus.OPEN)
            if item.days_remaining is not None and item.days_remaining <= days
        ]


    @staticmethod
    def _automation_meter_id(automation_key: str) -> UUID | None:
        try:
            prefix, raw_id, _period = automation_key.split(":", 2)
            return UUID(raw_id) if prefix == "meter-reading" else None
        except (ValueError, TypeError):
            return None

    def _sync_monthly_meter_tasks(self) -> None:
        """Create exactly one task per active monthly meter plan and month.

        Repeated calls are idempotent through ``automation_key``. A reading in the
        planned month completes the generated task automatically; disabling a plan
        cancels an open generated task for the current month.
        """

        zone = self._timezone()
        now = datetime.now(UTC)
        today = now.astimezone(zone).date()
        period_start_local = datetime(today.year, today.month, 1, tzinfo=zone)
        if today.month == 12:
            period_end_local = datetime(today.year + 1, 1, 1, tzinfo=zone)
        else:
            period_end_local = datetime(today.year, today.month + 1, 1, tzinfo=zone)
        period_key = f"{today.year:04d}-{today.month:02d}"
        prefix = f"meter-reading:"
        existing = {
            item.automation_key: item
            for item in self.session.exec(
                select(WorkItem).where(WorkItem.deleted_at.is_(None))
            ).all()
            if item.automation_key and item.automation_key.startswith(prefix)
        }
        active_keys: set[str] = set()
        changed = False
        meters = list(
            self.session.exec(
                select(ConsumptionMeter).where(ConsumptionMeter.deleted_at.is_(None))
            ).all()
        )
        for meter in meters:
            if meter.reading_schedule_day is None and not meter.reading_schedule_last_day:
                continue
            key = f"meter-reading:{meter.id}:{period_key}"
            active_keys.add(key)
            record = existing.get(key)
            reading = self.session.exec(
                select(ConsumptionReading).where(
                    ConsumptionReading.meter_id == meter.id,
                    ConsumptionReading.measured_at >= period_start_local.astimezone(UTC),
                    ConsumptionReading.measured_at < period_end_local.astimezone(UTC),
                    col(ConsumptionReading.deleted_at).is_(None),
                )
            ).first()
            if reading is not None:
                if record is not None and record.status == WorkStatus.OPEN.value:
                    record.status = WorkStatus.COMPLETED.value
                    record.completed_at = now
                    record.updated_at = now
                    self.session.add(record)
                    self.session.add(
                        WorkItemEvent(
                            work_item_id=record.id,
                            event_type="completed",
                            note="Automatisch durch gespeicherte Zählerablesung erledigt.",
                            due_at_before=record.due_at,
                        )
                    )
                    changed = True
                continue
            maximum = monthrange(today.year, today.month)[1]
            due_day = maximum if meter.reading_schedule_last_day else min(
                meter.reading_schedule_day or maximum, maximum
            )
            due_date = date(today.year, today.month, due_day)
            due_at = datetime.combine(due_date, time(hour=12), tzinfo=zone).astimezone(UTC)
            reminder_days = []
            try:
                reminder_days = [
                    max(0, int(value))
                    for value in json.loads(meter.reminder_days_json or "[]")
                ]
            except (TypeError, ValueError, json.JSONDecodeError):
                reminder_days = []
            lead_days = max(reminder_days or [3])
            if today < due_date - timedelta(days=lead_days) and record is None:
                active_keys.discard(key)
                continue
            if record is None:
                record = WorkItem(
                    item_type=WorkItemType.TASK.value,
                    title=f"Zähler ablesen: {meter.name}",
                    description=(
                        f"Monatliche Ablesung für {meter.name}. "
                        "Die Aufgabe wird nach einer gespeicherten Ablesung automatisch erledigt."
                    ),
                    due_at=due_at,
                    recurrence_mode=RecurrenceMode.NONE.value,
                    priority=WorkPriority.NORMAL.value,
                    automation_key=key,
                )
                self.session.add(record)
                existing[key] = record
                changed = True
            else:
                expected_title = f"Zähler ablesen: {meter.name}"
                record_changed = False
                if record.status == WorkStatus.CANCELLED.value:
                    record.status = WorkStatus.OPEN.value
                    record.completed_at = None
                    self.session.add(
                        WorkItemEvent(
                            work_item_id=record.id,
                            event_type="reopened",
                            note="Ableseplan wurde wieder aktiviert.",
                            due_at_before=record.due_at,
                            due_at_after=due_at,
                        )
                    )
                    record_changed = True
                if record.title != expected_title or record.due_at != due_at:
                    record.title = expected_title
                    record.due_at = due_at
                    record_changed = True
                if record_changed:
                    record.updated_at = now
                    self.session.add(record)
                    changed = True

        for key, record in existing.items():
            if not key.endswith(f":{period_key}") or key in active_keys:
                continue
            if record.status == WorkStatus.OPEN.value:
                record.status = WorkStatus.CANCELLED.value
                record.updated_at = now
                self.session.add(record)
                self.session.add(
                    WorkItemEvent(
                        work_item_id=record.id,
                        event_type="cancelled",
                        note="Ableseplan wurde deaktiviert oder der Zähler archiviert.",
                        due_at_before=record.due_at,
                    )
                )
                changed = True
        if changed:
            try:
                self.session.commit()
            except IntegrityError:
                # Parallel API calls may try to create the same monthly task. The
                # partial unique index makes the operation idempotent at database
                # level; a retry on the next read will return the winning row.
                self.session.rollback()

    def _validate_target(
        self,
        target_type: KnowledgeTargetType | None,
        target_id: UUID | None,
        *,
        include_deleted: bool = False,
    ) -> None:
        if target_type is None and target_id is None:
            return
        if target_type is None or target_id is None:
            raise WorkValidationError("Zieltyp und Ziel-ID müssen gemeinsam angegeben werden")
        try:
            require_domain_target(
                self.session,
                target_type,
                target_id,
                include_deleted=include_deleted,
            )
        except KnowledgeValidationError as exc:
            raise WorkValidationError(str(exc)) from exc

    @staticmethod
    def _require_user_managed(record: WorkItem) -> None:
        if record.automation_key is not None:
            raise WorkConflictError(
                "Automatisch erzeugte Ableseaufgaben werden durch den Ableseplan verwaltet"
            )

    def _require_item(self, item_id: UUID) -> WorkItem:
        record = self.session.get(WorkItem, item_id)
        if record is None or record.deleted_at is not None:
            raise WorkNotFoundError("Aufgabe oder Wartung wurde nicht gefunden")
        return record

    def _read(self, record: WorkItem) -> WorkItemRead:
        target_type = KnowledgeTargetType(record.target_type) if record.target_type else None
        target_label, target_route = self._target_presentation(target_type, record.target_id)
        if record.automation_key and record.automation_key.startswith("meter-reading:"):
            meter_id = self._automation_meter_id(record.automation_key)
            meter = self.session.get(ConsumptionMeter, meter_id) if meter_id else None
            target_label = meter.name if meter else "Zählerablesung"
            target_route = f"/consumption?read={meter_id}" if meter_id else "/consumption"
        due_at = self._aware(record.due_at) if record.due_at else None
        zone = self._timezone()
        days_remaining = (
            (due_at.astimezone(zone).date() - datetime.now(zone).date()).days if due_at else None
        )
        due_status = None
        if days_remaining is not None:
            due_status = (
                "overdue" if days_remaining < 0 else "today" if days_remaining == 0 else "upcoming"
            )
        return WorkItemRead(
            id=record.id,
            item_type=WorkItemType(record.item_type),
            title=record.title,
            description=record.description,
            target_type=target_type,
            target_id=record.target_id,
            target_label=target_label,
            target_route=target_route,
            automation_key=record.automation_key,
            generated=record.automation_key is not None,
            due_at=due_at,
            recurrence_days=record.recurrence_days,
            recurrence_mode=RecurrenceMode(record.recurrence_mode),
            calendar_months=record.calendar_months,
            calendar_day=record.calendar_day,
            calendar_month=record.calendar_month,
            calendar_last_day=record.calendar_last_day,
            priority=WorkPriority(record.priority),
            status=WorkStatus(record.status),
            overdue=(
                record.status == WorkStatus.OPEN.value
                and due_at is not None
                and due_at < datetime.now(UTC)
            ),
            due_status=due_status,
            days_remaining=days_remaining,
            completed_at=self._aware(record.completed_at) if record.completed_at else None,
            created_at=self._aware(record.created_at),
            updated_at=self._aware(record.updated_at),
        )

    def _target_presentation(
        self,
        target_type: KnowledgeTargetType | None,
        target_id: UUID | None,
    ) -> tuple[str | None, str | None]:
        if target_type is None or target_id is None:
            return None, None
        if target_type == KnowledgeTargetType.ASSET:
            record = self.session.get(Asset, target_id)
            return (record.name if record else "Unbekanntes Asset", f"/assets/{target_id}")
        if target_type == KnowledgeTargetType.LOCATION:
            record = self.session.get(Location, target_id)
            return (record.name if record else "Unbekannter Bereich", f"/locations/{target_id}")
        if target_type == KnowledgeTargetType.CIRCUIT:
            record = self.session.get(ElectricalCircuit, target_id)
            return (
                record.name if record else "Unbekannter Stromkreis",
                f"/electrical/circuits/{target_id}",
            )
        component = self.session.get(ElectricalComponent, target_id)
        asset = self.session.get(Asset, component.asset_id) if component else None
        if target_type == KnowledgeTargetType.DISTRIBUTION:
            distribution = self.session.get(ElectricalDistribution, target_id)
            label = distribution.designation if distribution and distribution.designation else None
            return (
                label or (asset.name if asset else "Unbekannte Verteilung"),
                f"/electrical/distributions/{target_id}",
            )
        device = self.session.get(ElectricalProtectiveDevice, target_id)
        label = (
            asset.name if asset else (device.device_type if device else "Unbekanntes Schutzgerät")
        )
        return label, f"/electrical/protective-devices/{target_id}/edit"

    @staticmethod
    def _aware(value: datetime) -> datetime:
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)

    def _timezone(self) -> ZoneInfo:
        setting = self.session.get(ApplicationSetting, 1)
        name = setting.timezone if setting else "Europe/Berlin"
        try:
            return ZoneInfo(name)
        except ZoneInfoNotFoundError:
            return ZoneInfo("UTC")

    def _next_calendar_due(self, record: WorkItem, completed_at: datetime) -> datetime:
        if record.due_at is None or record.calendar_months not in {1, 2, 3, 6, 12}:
            raise WorkValidationError("Der Kalenderplan ist unvollständig")
        zone = self._timezone()
        current = self._aware(record.due_at).astimezone(zone)
        completed_local = completed_at.astimezone(zone)
        while current <= completed_local:
            absolute = current.year * 12 + current.month - 1 + record.calendar_months
            year, month_index = divmod(absolute, 12)
            month = month_index + 1
            maximum = monthrange(year, month)[1]
            day = (
                maximum
                if record.calendar_last_day
                else min(record.calendar_day or current.day, maximum)
            )
            current = current.replace(year=year, month=month, day=day)
        return current.astimezone(UTC)
