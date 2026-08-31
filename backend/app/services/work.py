from __future__ import annotations

import json
from calendar import monthrange
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
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
from app.models.integration_setting import IntegrationSetting
from app.models.work import (
    WorkItem,
    WorkItemEvent,
    WorkItemEventAttachment,
    WorkItemEventPaperlessLink,
    WorkSubject,
)
from app.schemas.knowledge import KnowledgeTargetType
from app.schemas.work import (
    RecurrenceMode,
    WorkActivityKind,
    WorkCompletionWrite,
    WorkEventAttachmentRead,
    WorkHistoryEntryWrite,
    WorkHistoryRead,
    WorkHistoryStatsRead,
    WorkItemEventRead,
    WorkItemRead,
    WorkItemType,
    WorkItemWrite,
    WorkPaperlessLinkRead,
    WorkPriority,
    WorkStatus,
    WorkSubjectRead,
    WorkSubjectTimelineEntryRead,
    WorkSubjectTimelineRead,
    WorkSubjectWrite,
    WorkSubjectType,
    WorkSummaryRead,
)
from app.services.consumption_reminders import monthly_reading_window, shift_month
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
        subject_id: UUID | None = None,
        include_archived: bool = False,
    ) -> list[WorkItemRead]:
        self._sync_monthly_meter_tasks()
        if (target_type is None) != (target_id is None):
            raise WorkValidationError("Zieltyp und Ziel-ID müssen gemeinsam angegeben werden")
        if subject_id is not None and target_id is not None:
            raise WorkValidationError("Bezugsobjekt und bestehendes Ziel können nicht gleichzeitig gefiltert werden")
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
        if subject_id is not None:
            statement = statement.where(WorkItem.subject_id == subject_id)
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
        self._validate_subject(payload.subject_id)
        record = WorkItem(
            item_type=payload.item_type.value,
            activity_kind=payload.activity_kind.value,
            title=payload.title,
            description=payload.description,
            target_type=payload.target_type.value if payload.target_type else None,
            target_id=payload.target_id,
            subject_id=payload.subject_id,
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
        same_subject = record.subject_id == payload.subject_id
        self._validate_subject(payload.subject_id, include_deleted=same_subject)
        record.item_type = payload.item_type.value
        record.activity_kind = payload.activity_kind.value
        record.title = payload.title
        record.description = payload.description
        record.target_type = payload.target_type.value if payload.target_type else None
        record.target_id = payload.target_id
        record.subject_id = payload.subject_id
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
        performed_at = self._aware(payload.occurred_at) if payload.occurred_at else now
        due_before = record.due_at
        due_after: datetime | None = None
        if (
            record.item_type == WorkItemType.MAINTENANCE.value
            and record.recurrence_mode == RecurrenceMode.INTERVAL.value
            and record.recurrence_days
        ):
            base = performed_at
            due_after = base + timedelta(days=record.recurrence_days)
            record.due_at = due_after
            record.completed_at = now
        elif (
            record.item_type == WorkItemType.MAINTENANCE.value
            and record.recurrence_mode == RecurrenceMode.CALENDAR.value
        ):
            due_after = self._next_calendar_due(record, performed_at)
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
            occurred_at=performed_at,
            cost_amount=payload.cost_amount,
            cost_currency=payload.cost_currency if payload.cost_amount is not None else None,
            reading_value=payload.reading_value,
            reading_unit=payload.reading_unit if payload.reading_value is not None else None,
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
            .order_by(WorkItemEvent.occurred_at.desc(), WorkItemEvent.created_at.desc())
        ).all()
        completed = [event for event in records if event.event_type == "completed"]
        interval_by_id = self._interval_map(completed)
        return [self._event_read(event, interval_by_id.get(event.id)) for event in records]

    def history(self, item_id: UUID) -> WorkHistoryRead:
        self._require_item(item_id)
        events = list(self.session.exec(
            select(WorkItemEvent)
            .where(WorkItemEvent.work_item_id == item_id)
            .where(WorkItemEvent.event_type == "completed")
            .order_by(WorkItemEvent.occurred_at.desc(), WorkItemEvent.created_at.desc())
        ).all())
        interval_by_id = self._interval_map(events)
        ordered_asc = sorted(
            events,
            key=lambda event: (self._aware(event.occurred_at).date(), event.created_at),
        )
        intervals = [
            (self._aware(current.occurred_at).date() - self._aware(previous.occurred_at).date()).days
            for previous, current in zip(ordered_asc, ordered_asc[1:], strict=False)
        ]
        stats = WorkHistoryStatsRead(
            count=len(events),
            last_performed_at=self._aware(events[0].occurred_at) if events else None,
            previous_performed_at=self._aware(events[1].occurred_at) if len(events) > 1 else None,
            last_interval_days=interval_by_id.get(events[0].id) if events else None,
            average_interval_days=(round(sum(intervals) / len(intervals), 1) if intervals else None),
            shortest_interval_days=min(intervals) if intervals else None,
            longest_interval_days=max(intervals) if intervals else None,
        )
        return WorkHistoryRead(
            item_id=item_id,
            stats=stats,
            entries=[self._event_read(event, interval_by_id.get(event.id)) for event in events],
        )

    def add_history(self, item_id: UUID, payload: WorkHistoryEntryWrite) -> WorkItemEventRead:
        record = self._require_item(item_id)
        self._require_user_managed(record)
        event = WorkItemEvent(
            work_item_id=item_id,
            event_type="completed",
            note=payload.note,
            occurred_at=self._aware(payload.occurred_at),
            cost_amount=payload.cost_amount,
            cost_currency=payload.cost_currency if payload.cost_amount is not None else None,
            reading_value=payload.reading_value,
            reading_unit=payload.reading_unit if payload.reading_value is not None else None,
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return self._event_read(event, self._interval_for_event(event))

    def update_history(
        self, item_id: UUID, event_id: UUID, payload: WorkHistoryEntryWrite
    ) -> WorkItemEventRead:
        record = self._require_item(item_id)
        self._require_user_managed(record)
        event = self._require_history_event(item_id, event_id)
        event.note = payload.note
        event.occurred_at = self._aware(payload.occurred_at)
        event.cost_amount = payload.cost_amount
        event.cost_currency = payload.cost_currency if payload.cost_amount is not None else None
        event.reading_value = payload.reading_value
        event.reading_unit = payload.reading_unit if payload.reading_value is not None else None
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return self._event_read(event, self._interval_for_event(event))

    def delete_history(self, item_id: UUID, event_id: UUID) -> None:
        record = self._require_item(item_id)
        self._require_user_managed(record)
        event = self._require_history_event(item_id, event_id)
        attachments = self.session.exec(
            select(WorkItemEventAttachment).where(WorkItemEventAttachment.event_id == event.id)
        ).all()
        for attachment in attachments:
            self.session.delete(attachment)
        paperless_links = self.session.exec(
            select(WorkItemEventPaperlessLink).where(
                WorkItemEventPaperlessLink.event_id == event.id
            )
        ).all()
        for link in paperless_links:
            self.session.delete(link)
        self.session.delete(event)
        self.session.commit()

    def add_attachment(
        self, item_id: UUID, event_id: UUID, file_name: str, content_type: str, content: bytes
    ) -> WorkEventAttachmentRead:
        record = self._require_item(item_id)
        self._require_user_managed(record)
        event = self._require_history_event(item_id, event_id)
        if not content or len(content) > 20 * 1024 * 1024:
            raise WorkValidationError("Anhang muss zwischen 1 Byte und 20 MB groß sein")
        safe_name = Path(file_name).name.strip()
        if not safe_name or safe_name in {".", ".."}:
            raise WorkValidationError("Ungültiger Dateiname")
        normalized_type = (content_type or "application/octet-stream").strip()[:120]
        attachment = WorkItemEventAttachment(
            event_id=event.id,
            file_name=safe_name,
            content_type=normalized_type,
            size_bytes=len(content),
            content=content,
        )
        self.session.add(attachment)
        self.session.commit()
        self.session.refresh(attachment)
        return self._attachment_read(attachment)

    def attachment(
        self, item_id: UUID, event_id: UUID, attachment_id: UUID
    ) -> tuple[WorkItemEventAttachment, bytes]:
        self._require_item(item_id)
        event = self._require_history_event(item_id, event_id)
        attachment = self.session.get(WorkItemEventAttachment, attachment_id)
        if attachment is None or attachment.event_id != event.id:
            raise WorkNotFoundError("Anhang wurde nicht gefunden")
        return attachment, attachment.content

    def delete_attachment(self, item_id: UUID, event_id: UUID, attachment_id: UUID) -> None:
        record = self._require_item(item_id)
        self._require_user_managed(record)
        event = self._require_history_event(item_id, event_id)
        attachment = self.session.get(WorkItemEventAttachment, attachment_id)
        if attachment is None or attachment.event_id != event.id:
            raise WorkNotFoundError("Anhang wurde nicht gefunden")
        self.session.delete(attachment)
        self.session.commit()

    def list_subjects(self) -> list[WorkSubjectRead]:
        subjects = list(self.session.exec(
            select(WorkSubject).where(WorkSubject.deleted_at.is_(None)).order_by(WorkSubject.name)
        ).all())
        return [self._subject_read(subject) for subject in subjects]

    def create_subject(self, payload: WorkSubjectWrite) -> WorkSubjectRead:
        existing = self.session.exec(
            select(WorkSubject)
            .where(WorkSubject.deleted_at.is_(None))
            .where(WorkSubject.name == payload.name)
            .where(WorkSubject.subject_type == payload.subject_type.value)
        ).first()
        if existing is not None:
            raise WorkConflictError("Ein Bezugsobjekt mit diesem Namen und Typ existiert bereits")
        subject = WorkSubject(
            name=payload.name,
            subject_type=payload.subject_type.value,
            description=payload.description,
            profile_json=json.dumps(payload.profile, ensure_ascii=False),
        )
        self.session.add(subject)
        self.session.commit()
        self.session.refresh(subject)
        return self._subject_read(subject)

    def update_subject(self, subject_id: UUID, payload: WorkSubjectWrite) -> WorkSubjectRead:
        subject = self._require_subject(subject_id)
        duplicate = self.session.exec(
            select(WorkSubject)
            .where(WorkSubject.deleted_at.is_(None))
            .where(WorkSubject.id != subject_id)
            .where(WorkSubject.name == payload.name)
            .where(WorkSubject.subject_type == payload.subject_type.value)
        ).first()
        if duplicate is not None:
            raise WorkConflictError("Ein Bezugsobjekt mit diesem Namen und Typ existiert bereits")
        subject.name = payload.name
        subject.subject_type = payload.subject_type.value
        subject.description = payload.description
        subject.profile_json = json.dumps(payload.profile, ensure_ascii=False)
        subject.updated_at = datetime.now(UTC)
        self.session.add(subject)
        self.session.commit()
        self.session.refresh(subject)
        return self._subject_read(subject)

    def delete_subject(self, subject_id: UUID) -> None:
        subject = self._require_subject(subject_id)
        active_item = self.session.exec(
            select(WorkItem)
            .where(WorkItem.subject_id == subject_id)
            .where(WorkItem.deleted_at.is_(None))
        ).first()
        if active_item is not None:
            raise WorkConflictError("Bezugsobjekt wird noch von Aufgaben oder Wartungen verwendet")
        subject.deleted_at = datetime.now(UTC)
        subject.updated_at = subject.deleted_at
        self.session.add(subject)
        self.session.commit()

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

    def _sync_monthly_meter_tasks(self, *, _today: date | None = None) -> None:
        """Create exactly one task per active monthly meter plan and month.

        Repeated calls are idempotent through ``automation_key``. The shared
        monthly reading window decides both when a task appears and which reading
        completes it. Open tasks from the previous month remain active until a
        valid (possibly late) reading is stored.
        """

        zone = self._timezone()
        now = (
            datetime.now(UTC)
            if _today is None
            else datetime.combine(_today, time(hour=12), tzinfo=zone).astimezone(UTC)
        )
        today = _today or now.astimezone(zone).date()
        prefix = "meter-reading:"
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
            try:
                reminder_days = [
                    int(value) for value in json.loads(meter.reminder_days_json or "[]")
                ]
            except (TypeError, ValueError, json.JSONDecodeError):
                reminder_days = []

            periods = {shift_month(today.year, today.month, offset) for offset in (-1, 0)}
            for key, record in existing.items():
                if (
                    self._automation_meter_id(key) != meter.id
                    or record.status != WorkStatus.OPEN.value
                ):
                    continue
                try:
                    raw_period = key.rsplit(":", 1)[1]
                    year, month = (int(part) for part in raw_period.split("-", 1))
                    periods.add((year, month))
                except (ValueError, IndexError):
                    continue

            created_at = (
                meter.created_at.replace(tzinfo=UTC)
                if meter.created_at.tzinfo is None
                else meter.created_at
            )
            created_on = created_at.astimezone(zone).date()
            for year, month in sorted(periods):
                window = monthly_reading_window(
                    year=year,
                    month=month,
                    schedule_day=meter.reading_schedule_day,
                    last_day=meter.reading_schedule_last_day,
                    reminder_days=reminder_days,
                )
                if window.due_date < created_on:
                    continue
                key = f"meter-reading:{meter.id}:{year:04d}-{month:02d}"
                record = existing.get(key)
                active_keys.add(key)
                start_local = datetime.combine(window.starts_on, time.min, tzinfo=zone)
                end_local = datetime.combine(window.ends_before, time.min, tzinfo=zone)
                reading = self.session.exec(
                    select(ConsumptionReading).where(
                        ConsumptionReading.meter_id == meter.id,
                        ConsumptionReading.measured_at >= start_local.astimezone(UTC),
                        ConsumptionReading.measured_at < end_local.astimezone(UTC),
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
                if today < window.starts_on and record is None:
                    active_keys.discard(key)
                    continue

                due_at = datetime.combine(
                    window.due_date, time(hour=12), tzinfo=zone
                ).astimezone(UTC)
                if record is None:
                    record = WorkItem(
                        item_type=WorkItemType.TASK.value,
                        title=f"Zähler ablesen: {meter.name}",
                        description=(
                            f"Monatliche Ablesung für {meter.name}. "
                            "Die Aufgabe wird nur durch eine Ablesung im gültigen "
                            "Ablesefenster automatisch erledigt."
                        ),
                        due_at=due_at,
                        recurrence_mode=RecurrenceMode.NONE.value,
                        priority=WorkPriority.NORMAL.value,
                        automation_key=key,
                    )
                    self.session.add(record)
                    existing[key] = record
                    changed = True
                    continue

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
            if key in active_keys:
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

    def _validate_subject(self, subject_id: UUID | None, *, include_deleted: bool = False) -> None:
        if subject_id is None:
            return
        subject = self.session.get(WorkSubject, subject_id)
        if subject is None or (subject.deleted_at is not None and not include_deleted):
            raise WorkValidationError("Bezugsobjekt wurde nicht gefunden")

    def _require_subject(self, subject_id: UUID) -> WorkSubject:
        subject = self.session.get(WorkSubject, subject_id)
        if subject is None or subject.deleted_at is not None:
            raise WorkNotFoundError("Bezugsobjekt wurde nicht gefunden")
        return subject

    def _subject_read(self, subject: WorkSubject) -> WorkSubjectRead:
        activity_count = len(self.session.exec(
            select(WorkItem)
            .where(WorkItem.subject_id == subject.id)
            .where(WorkItem.deleted_at.is_(None))
        ).all())
        return WorkSubjectRead(
            id=subject.id,
            name=subject.name,
            subject_type=WorkSubjectType(subject.subject_type),
            description=subject.description,
            profile=self._subject_profile(subject),
            created_at=self._aware(subject.created_at),
            updated_at=self._aware(subject.updated_at),
            activity_count=activity_count,
        )

    def _require_history_event(self, item_id: UUID, event_id: UUID) -> WorkItemEvent:
        event = self.session.get(WorkItemEvent, event_id)
        if event is None or event.work_item_id != item_id or event.event_type != "completed":
            raise WorkNotFoundError("Historieneintrag wurde nicht gefunden")
        return event

    def _event_read(self, event: WorkItemEvent, interval_days: int | None = None) -> WorkItemEventRead:
        attachments = self.session.exec(
            select(WorkItemEventAttachment)
            .where(WorkItemEventAttachment.event_id == event.id)
            .order_by(WorkItemEventAttachment.created_at)
        ).all()
        paperless_links = self._paperless_links(event.id)
        return WorkItemEventRead(
            id=event.id,
            work_item_id=event.work_item_id,
            event_type=event.event_type,
            note=event.note,
            due_at_before=self._aware(event.due_at_before) if event.due_at_before else None,
            due_at_after=self._aware(event.due_at_after) if event.due_at_after else None,
            occurred_at=self._aware(event.occurred_at),
            cost_amount=event.cost_amount,
            cost_currency=event.cost_currency,
            reading_value=event.reading_value,
            reading_unit=event.reading_unit,
            interval_days=interval_days,
            attachments=[self._attachment_read(attachment) for attachment in attachments],
            paperless_links=paperless_links,
            created_at=self._aware(event.created_at),
        )

    def _attachment_read(self, attachment: WorkItemEventAttachment) -> WorkEventAttachmentRead:
        return WorkEventAttachmentRead(
            id=attachment.id,
            event_id=attachment.event_id,
            file_name=attachment.file_name,
            content_type=attachment.content_type,
            size_bytes=attachment.size_bytes,
            created_at=self._aware(attachment.created_at),
        )

    def _interval_map(self, events: list[WorkItemEvent]) -> dict[UUID, int]:
        ordered = sorted(events, key=lambda event: self._aware(event.occurred_at))
        result: dict[UUID, int] = {}
        for previous, current in zip(ordered, ordered[1:]):
            result[current.id] = (
                self._aware(current.occurred_at).date()
                - self._aware(previous.occurred_at).date()
            ).days
        return result

    def _interval_for_event(self, event: WorkItemEvent) -> int | None:
        events = list(self.session.exec(
            select(WorkItemEvent)
            .where(WorkItemEvent.work_item_id == event.work_item_id)
            .where(WorkItemEvent.event_type == "completed")
        ).all())
        return self._interval_map(events).get(event.id)


    @staticmethod
    def _subject_profile(subject: WorkSubject) -> dict[str, str | int | float | bool | None]:
        try:
            value = json.loads(subject.profile_json or "{}")
            return value if isinstance(value, dict) else {}
        except (TypeError, json.JSONDecodeError):
            return {}

    def _paperless_links(self, event_id: UUID) -> list[WorkPaperlessLinkRead]:
        records = self.session.exec(
            select(WorkItemEventPaperlessLink)
            .where(WorkItemEventPaperlessLink.event_id == event_id)
            .order_by(WorkItemEventPaperlessLink.created_at)
        ).all()
        setting = self.session.exec(
            select(IntegrationSetting).where(IntegrationSetting.kind == "paperless")
        ).first()
        configured_url = setting.browser_url or setting.base_url if setting else None
        base_url = configured_url.rstrip("/") if configured_url else None
        return [
            WorkPaperlessLinkRead(
                id=record.id,
                event_id=record.event_id,
                document_id=record.document_id,
                title=record.title,
                created_date=record.created_date,
                original_file_name=record.original_file_name,
                source_url=(
                    f"{base_url}/documents/{record.document_id}/details"
                    if base_url
                    else None
                ),
                created_at=self._aware(record.created_at),
            )
            for record in records
        ]

    def subject_timeline(self, subject_id: UUID) -> WorkSubjectTimelineRead:
        subject = self._require_subject(subject_id)
        items = list(
            self.session.exec(
                select(WorkItem)
                .where(WorkItem.subject_id == subject_id)
                .where(WorkItem.deleted_at.is_(None))
            ).all()
        )
        entries: list[WorkSubjectTimelineEntryRead] = []
        for item in items:
            events = self.session.exec(
                select(WorkItemEvent)
                .where(WorkItemEvent.work_item_id == item.id)
                .where(WorkItemEvent.event_type == "completed")
            ).all()
            for event in events:
                event_read = self._event_read(event)
                entries.append(
                    WorkSubjectTimelineEntryRead(
                        id=f"event:{event.id}",
                        entry_type="history",
                        work_item_id=item.id,
                        title=item.title,
                        item_type=WorkItemType(item.item_type),
                        activity_kind=WorkActivityKind(item.activity_kind),
                        at=self._aware(event.occurred_at),
                        note=event.note,
                        cost_amount=event.cost_amount,
                        cost_currency=event.cost_currency,
                        reading_value=event.reading_value,
                        reading_unit=event.reading_unit,
                        status=WorkStatus.COMPLETED,
                        paperless_links=event_read.paperless_links,
                    )
                )
            if item.status == WorkStatus.OPEN.value and item.due_at is not None:
                entries.append(
                    WorkSubjectTimelineEntryRead(
                        id=f"due:{item.id}",
                        entry_type="due",
                        work_item_id=item.id,
                        title=item.title,
                        item_type=WorkItemType(item.item_type),
                        activity_kind=WorkActivityKind(item.activity_kind),
                        at=self._aware(item.due_at),
                        note=item.description,
                        status=WorkStatus.OPEN,
                    )
                )
        entries.sort(key=lambda entry: entry.at, reverse=True)
        return WorkSubjectTimelineRead(subject=self._subject_read(subject), entries=entries)

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
        subject = self.session.get(WorkSubject, record.subject_id) if record.subject_id else None
        if subject is not None:
            target_label = subject.name
            target_route = f"/maintenance?subject={subject.id}"
        completed_events = list(self.session.exec(
            select(WorkItemEvent)
            .where(WorkItemEvent.work_item_id == record.id)
            .where(WorkItemEvent.event_type == "completed")
            .order_by(WorkItemEvent.occurred_at.desc())
        ).all())
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
            activity_kind=WorkActivityKind(record.activity_kind),
            title=record.title,
            description=record.description,
            target_type=target_type,
            target_id=record.target_id,
            subject_id=record.subject_id,
            subject_name=subject.name if subject else None,
            subject_type=WorkSubjectType(subject.subject_type) if subject else None,
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
            history_count=len(completed_events),
            last_performed_at=(self._aware(completed_events[0].occurred_at) if completed_events else None),
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
        if record.calendar_months is None or not 1 <= record.calendar_months <= 120:
            raise WorkValidationError("Der Kalenderplan ist unvollständig")
        zone = self._timezone()
        completed_local = completed_at.astimezone(zone)
        absolute = completed_local.year * 12 + completed_local.month - 1 + record.calendar_months
        year, month_index = divmod(absolute, 12)
        month = month_index + 1
        maximum = monthrange(year, month)[1]
        day = maximum if record.calendar_last_day else min(completed_local.day, maximum)
        return completed_local.replace(year=year, month=month, day=day).astimezone(UTC)
