from __future__ import annotations

import csv
import io
import json
import re
import sqlite3
import tempfile
import unicodedata
from calendar import monthrange
from collections.abc import Iterable
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.models.application_setting import ApplicationSetting
from app.models.asset_engine import Asset, Location
from app.models.consumption import (
    ConsumptionMeter,
    ConsumptionNote,
    ConsumptionReading,
    ConsumptionSetting,
)
from app.models.electrical import ElectricalMeterPlacement
from app.repositories.asset_engine import LocationRepository
from app.repositories.consumption import ConsumptionRepository
from app.schemas.consumption import (
    ConsumptionComparisonRead,
    ConsumptionDefaultSeedRead,
    ConsumptionImportPreviewRead,
    ConsumptionImportResultRead,
    ConsumptionMeterLiveRead,
    ConsumptionMeterRead,
    ConsumptionMeterReplacementWrite,
    ConsumptionMeterType,
    ConsumptionMeterWrite,
    ConsumptionNoteRead,
    ConsumptionNoteScope,
    ConsumptionNoteWrite,
    ConsumptionPeriodResult,
    ConsumptionReadingRead,
    ConsumptionReadingReminderRead,
    ConsumptionReadingSource,
    ConsumptionReadingWrite,
    ConsumptionSeries,
    ConsumptionSeriesPoint,
    ConsumptionSettingsRead,
    ConsumptionSettingsWrite,
    ConsumptionStatisticsRead,
    ConsumptionSummaryRead,
    ConsumptionVirtualResultRead,
    ConsumptionWaterRole,
)
from app.schemas.home_assistant import HomeAssistantSelectionScope
from app.services.consumption_reminders import interval_due_date
from app.services.home_assistant import (
    HomeAssistantConfigurationError,
    HomeAssistantConnectionError,
    HomeAssistantService,
)

DEFAULT_METERS: tuple[dict[str, object], ...] = (
    {
        "name": "Hauptwasser",
        "meter_type": ConsumptionMeterType.WATER,
        "unit": "m³",
        "decimals": 3,
        "sort_order": 10,
        "water_role": ConsumptionWaterRole.MAIN,
    },
    {
        "name": "Dusche",
        "meter_type": ConsumptionMeterType.WATER,
        "unit": "m³",
        "decimals": 3,
        "sort_order": 20,
        "water_role": ConsumptionWaterRole.EG_COMPONENT,
    },
    {
        "name": "Küche",
        "meter_type": ConsumptionMeterType.WATER,
        "unit": "m³",
        "decimals": 3,
        "sort_order": 30,
        "water_role": ConsumptionWaterRole.EG_COMPONENT,
    },
    {
        "name": "Heizraum",
        "meter_type": ConsumptionMeterType.WATER,
        "unit": "m³",
        "decimals": 3,
        "sort_order": 40,
        "water_role": ConsumptionWaterRole.NONE,
    },
    {
        "name": "Zählerraum",
        "meter_type": ConsumptionMeterType.WATER,
        "unit": "m³",
        "decimals": 3,
        "sort_order": 50,
        "water_role": ConsumptionWaterRole.EG_COMPONENT,
    },
    {
        "name": "Strom Netzbezug",
        "meter_type": ConsumptionMeterType.ELECTRICITY_GRID,
        "unit": "kWh",
        "decimals": 1,
        "sort_order": 60,
        "water_role": ConsumptionWaterRole.NONE,
    },
    {
        "name": "Strom Erzeugung (PV)",
        "meter_type": ConsumptionMeterType.ELECTRICITY_PV,
        "unit": "kWh",
        "decimals": 1,
        "sort_order": 70,
        "water_role": ConsumptionWaterRole.NONE,
    },
    {
        "name": "Strom Netzeinspeisung",
        "meter_type": ConsumptionMeterType.ELECTRICITY_FEED_IN,
        "unit": "kWh",
        "decimals": 1,
        "sort_order": 75,
        "water_role": ConsumptionWaterRole.NONE,
    },
    {
        "name": "Gas",
        "meter_type": ConsumptionMeterType.GAS,
        "unit": "m³",
        "decimals": 3,
        "sort_order": 80,
        "water_role": ConsumptionWaterRole.NONE,
    },
)

GERMAN_MONTHS = (
    "Jan",
    "Feb",
    "Mär",
    "Apr",
    "Mai",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Okt",
    "Nov",
    "Dez",
)


class ConsumptionError(RuntimeError):
    """Base class for safe consumption-module domain errors."""


class ConsumptionNotFoundError(ConsumptionError):
    pass


class ConsumptionValidationError(ConsumptionError):
    pass


class ConsumptionConflictError(ConsumptionError):
    pass


class ConsumptionImportError(ConsumptionError):
    pass


class ConsumptionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = ConsumptionRepository(session)

    # Settings
    def get_settings(self) -> ConsumptionSettingsRead:
        record = self.repository.get_settings()
        if record is None:
            record = ConsumptionSetting()
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
        return ConsumptionSettingsRead(
            reminder_days=record.reminder_days,
            plausibility_threshold_percent=record.plausibility_threshold_percent,
            updated_at=self._aware(record.updated_at),
        )

    def update_settings(self, payload: ConsumptionSettingsWrite) -> ConsumptionSettingsRead:
        record = self.repository.get_settings() or ConsumptionSetting()
        record.reminder_days = payload.reminder_days
        record.plausibility_threshold_percent = payload.plausibility_threshold_percent
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self.get_settings()

    # Meters
    def list_meters(
        self,
        *,
        search: str | None = None,
        meter_type: ConsumptionMeterType | None = None,
        asset_id: UUID | None = None,
        location_id: UUID | None = None,
        include_archived: bool = False,
    ) -> list[ConsumptionMeterRead]:
        records = self.repository.list_meters(
            search=search,
            meter_type=meter_type.value if meter_type else None,
            asset_id=asset_id,
            location_id=location_id,
            include_archived=include_archived,
        )
        return [self._meter_read(record) for record in records]

    def get_meter(self, meter_id: UUID, *, include_archived: bool = False) -> ConsumptionMeterRead:
        record = self.repository.get_meter(meter_id, include_archived=include_archived)
        if record is None:
            raise ConsumptionNotFoundError("Der Zähler wurde nicht gefunden")
        return self._meter_read(record)

    def create_meter(self, payload: ConsumptionMeterWrite) -> ConsumptionMeterRead:
        self._validate_meter(payload)
        if self.repository.find_meter_by_name(payload.name, include_archived=True):
            raise ConsumptionConflictError("Ein Zähler mit diesem Namen ist bereits vorhanden")
        if (
            payload.primary_for_dashboard
            and payload.meter_type != ConsumptionMeterType.ELECTRICITY_PV
        ):
            self.repository.clear_primary_for_type(payload.meter_type.value)
            self.session.flush()
        record = ConsumptionMeter(
            name=payload.name,
            meter_type=payload.meter_type.value,
            unit=payload.unit,
            decimals=payload.decimals,
            sort_order=payload.sort_order,
            serial_number=payload.serial_number,
            asset_id=payload.asset_id,
            location_id=payload.location_id,
            parent_meter_id=payload.parent_meter_id,
            home_assistant_entity_id=payload.home_assistant_entity_id,
            home_assistant_power_entity_id=payload.home_assistant_power_entity_id,
            home_assistant_voltage_entity_id=payload.home_assistant_voltage_entity_id,
            water_role=payload.water_role.value,
            primary_for_dashboard=payload.primary_for_dashboard,
            reading_schedule_day=payload.reading_schedule_day,
            reading_schedule_last_day=payload.reading_schedule_last_day,
            reminder_days_json=json.dumps(payload.reminder_days, separators=(",", ":")),
            notes=payload.notes,
        )
        return self._save_meter(record)

    def update_meter(self, meter_id: UUID, payload: ConsumptionMeterWrite) -> ConsumptionMeterRead:
        record = self.repository.get_meter(meter_id)
        if record is None:
            raise ConsumptionNotFoundError("Der Zähler wurde nicht gefunden")
        self._validate_meter(payload, record_id=meter_id)
        named = self.repository.find_meter_by_name(payload.name, include_archived=True)
        if named is not None and named.id != meter_id:
            raise ConsumptionConflictError("Ein Zähler mit diesem Namen ist bereits vorhanden")
        if (
            payload.primary_for_dashboard
            and payload.meter_type != ConsumptionMeterType.ELECTRICITY_PV
        ):
            self.repository.clear_primary_for_type(
                payload.meter_type.value, exclude_id=meter_id
            )
            self.session.flush()
        record.name = payload.name
        record.meter_type = payload.meter_type.value
        record.unit = payload.unit
        record.decimals = payload.decimals
        record.sort_order = payload.sort_order
        record.serial_number = payload.serial_number
        record.asset_id = payload.asset_id
        record.location_id = payload.location_id
        record.parent_meter_id = payload.parent_meter_id
        record.home_assistant_entity_id = payload.home_assistant_entity_id
        record.home_assistant_power_entity_id = payload.home_assistant_power_entity_id
        record.home_assistant_voltage_entity_id = payload.home_assistant_voltage_entity_id
        record.water_role = payload.water_role.value
        record.primary_for_dashboard = payload.primary_for_dashboard
        record.reading_schedule_day = payload.reading_schedule_day
        record.reading_schedule_last_day = payload.reading_schedule_last_day
        record.reminder_days_json = json.dumps(payload.reminder_days, separators=(",", ":"))
        record.notes = payload.notes
        record.updated_at = datetime.now(UTC)
        return self._save_meter(record)

    def replace_meter(
        self,
        meter_id: UUID,
        payload: ConsumptionMeterReplacementWrite,
    ) -> ConsumptionMeterRead:
        meter = self.repository.get_meter(meter_id)
        if meter is None:
            raise ConsumptionNotFoundError("Der aktive Zähler wurde nicht gefunden")
        replaced_at = self._as_utc(payload.replaced_at)
        old_measured_at = replaced_at - timedelta(microseconds=1)
        if (
            self.repository.duplicate_reading(meter.id, old_measured_at)
            or self.repository.duplicate_reading(meter.id, replaced_at)
        ):
            raise ConsumptionConflictError(
                "Zum Austauschzeitpunkt existiert bereits eine Ablesung"
            )
        self._validate_reading_value(
            meter,
            old_measured_at,
            payload.old_final_value,
            False,
        )
        old_serial = meter.serial_number or "nicht dokumentiert"
        note_suffix = f" · {payload.note}" if payload.note else ""
        old_reading = ConsumptionReading(
            meter_id=meter.id,
            measured_at=old_measured_at,
            value=payload.old_final_value,
            note=f"Letzter Stand vor Zählerwechsel ({old_serial}){note_suffix}",
            source=ConsumptionReadingSource.MANUAL.value,
            is_reset=False,
        )
        new_reading = ConsumptionReading(
            meter_id=meter.id,
            measured_at=replaced_at,
            value=payload.new_start_value,
            note=f"Startstand nach Zählerwechsel ({payload.new_serial_number}){note_suffix}",
            source=ConsumptionReadingSource.MANUAL.value,
            is_reset=True,
        )
        meter.serial_number = payload.new_serial_number
        meter.updated_at = datetime.now(UTC)
        try:
            self.session.add(old_reading)
            self.session.add(new_reading)
            self.session.add(meter)
            self.session.commit()
            self.session.refresh(meter)
        except IntegrityError as exc:
            self.session.rollback()
            raise ConsumptionConflictError(
                "Der Zählerwechsel konnte nicht widerspruchsfrei gespeichert werden"
            ) from exc
        return self._meter_read(meter)

    def meter_live_values(
        self, meter_id: UUID, *, refresh: bool = False
    ) -> ConsumptionMeterLiveRead:
        meter = self.repository.get_meter(meter_id)
        if meter is None:
            raise ConsumptionNotFoundError("Der aktive Zähler wurde nicht gefunden")
        entity_ids = [
            value
            for value in (
                meter.home_assistant_power_entity_id,
                meter.home_assistant_voltage_entity_id,
            )
            if value
        ]
        if not entity_ids:
            return ConsumptionMeterLiveRead(
                meter_id=meter.id,
                power_entity_id=None,
                voltage_entity_id=None,
                power_w=None,
                voltage_v=None,
                power_updated_at=None,
                voltage_updated_at=None,
                available=False,
                warning="Keine Home-Assistant-Live-Entitäten hinterlegt",
            )
        try:
            result = HomeAssistantService(self.session).entities(
                search=None,
                offset=0,
                limit=10000,
                refresh=refresh,
                selection_scope=HomeAssistantSelectionScope.ALL,
            )
        except (HomeAssistantConfigurationError, HomeAssistantConnectionError) as exc:
            return ConsumptionMeterLiveRead(
                meter_id=meter.id,
                power_entity_id=meter.home_assistant_power_entity_id,
                voltage_entity_id=meter.home_assistant_voltage_entity_id,
                power_w=None,
                voltage_v=None,
                power_updated_at=None,
                voltage_updated_at=None,
                available=False,
                warning=str(exc),
            )
        entities = {item.entity_id: item for item in result.items}

        def numeric(entity_id: str | None, expected: str) -> tuple[float | None, datetime | None]:
            if not entity_id:
                return None, None
            entity = entities.get(entity_id)
            if (
                entity is None
                or not entity.available
                or entity.state.casefold() in {"unknown", "unavailable"}
            ):
                return None, None
            try:
                value = float(entity.state.replace(",", "."))
            except ValueError:
                return None, None
            raw_unit = (entity.unit or "").strip()
            normalized_unit = raw_unit.casefold()
            if expected == "power":
                if raw_unit == "mW":
                    value /= 1000
                elif normalized_unit == "kw":
                    value *= 1000
                elif raw_unit == "MW":
                    value *= 1_000_000
            elif expected == "voltage":
                if raw_unit == "mV":
                    value /= 1000
                elif normalized_unit == "kv":
                    value *= 1000
            return value, self._as_utc(entity.last_updated or datetime.now(UTC))

        power, power_at = numeric(meter.home_assistant_power_entity_id, "power")
        voltage, voltage_at = numeric(meter.home_assistant_voltage_entity_id, "voltage")
        missing = []
        if meter.home_assistant_power_entity_id and power is None:
            missing.append("Leistung")
        if meter.home_assistant_voltage_entity_id and voltage is None:
            missing.append("Spannung")
        return ConsumptionMeterLiveRead(
            meter_id=meter.id,
            power_entity_id=meter.home_assistant_power_entity_id,
            voltage_entity_id=meter.home_assistant_voltage_entity_id,
            power_w=power,
            voltage_v=voltage,
            power_updated_at=power_at,
            voltage_updated_at=voltage_at,
            available=power is not None or voltage is not None,
            warning=(f"Keine nutzbaren Livewerte für {', '.join(missing)}" if missing else None),
        )

    def archive_meter(self, meter_id: UUID) -> None:
        record = self.repository.get_meter(meter_id)
        if record is None:
            raise ConsumptionNotFoundError("Der Zähler wurde nicht gefunden")
        children = self.repository.list_meters(include_archived=False)
        if any(item.parent_meter_id == meter_id for item in children):
            raise ConsumptionConflictError(
                "Der Zähler kann erst archiviert werden, wenn keine aktiven Unterzähler "
                "mehr darauf verweisen"
            )
        now = datetime.now(UTC)
        record.deleted_at = now
        record.updated_at = now
        placements = self.session.exec(
            select(ElectricalMeterPlacement).where(
                ElectricalMeterPlacement.meter_id == meter_id,
                col(ElectricalMeterPlacement.deleted_at).is_(None),
            )
        ).all()
        for placement in placements:
            placement.deleted_at = now
            placement.updated_at = now
            self.session.add(placement)
        self.session.add(record)
        self.session.commit()

    def seed_defaults(self) -> ConsumptionDefaultSeedRead:
        created = 0
        existing = 0
        for item in DEFAULT_METERS:
            name = str(item["name"])
            if self.repository.find_meter_by_name(name, include_archived=True):
                existing += 1
                continue
            record = ConsumptionMeter(
                name=name,
                meter_type=str(item["meter_type"].value),
                unit=str(item["unit"]),
                decimals=int(item["decimals"]),
                sort_order=int(item["sort_order"]),
                water_role=str(item["water_role"].value),
            )
            self.session.add(record)
            created += 1
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConsumptionConflictError(
                "Die Standardzähler konnten nicht angelegt werden"
            ) from exc
        return ConsumptionDefaultSeedRead(
            created=created,
            existing=existing,
            meters=self.list_meters(),
        )

    # Readings
    def list_readings(
        self,
        *,
        meter_id: UUID | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 500,
    ) -> list[ConsumptionReadingRead]:
        if meter_id and self.repository.get_meter(meter_id, include_archived=True) is None:
            raise ConsumptionNotFoundError("Der Zähler wurde nicht gefunden")
        records = self.repository.list_readings(
            meter_id=meter_id,
            start=self._as_utc(start) if start else None,
            end=self._as_utc(end) if end else None,
            limit=limit,
        )
        return [self._reading_read(record) for record in records]

    def create_reading(self, payload: ConsumptionReadingWrite) -> ConsumptionReadingRead:
        meter = self.repository.get_meter(payload.meter_id)
        if meter is None:
            raise ConsumptionNotFoundError("Der aktive Zähler wurde nicht gefunden")
        measured_at = self._as_utc(payload.measured_at)
        self._validate_reading_value(meter, measured_at, payload.value, payload.is_reset)
        if self.repository.duplicate_reading(meter.id, measured_at):
            raise ConsumptionConflictError(
                "Für diesen Zähler existiert zu diesem Zeitpunkt bereits eine Ablesung"
            )
        record = ConsumptionReading(
            meter_id=meter.id,
            measured_at=measured_at,
            value=payload.value,
            note=payload.note,
            source=payload.source.value,
            is_reset=payload.is_reset,
            immich_asset_id=str(payload.immich_asset_id) if payload.immich_asset_id else None,
            immich_original_file_name=payload.immich_original_file_name,
        )
        return self._save_reading(record)

    def update_reading(
        self, reading_id: UUID, payload: ConsumptionReadingWrite
    ) -> ConsumptionReadingRead:
        record = self.repository.get_reading(reading_id)
        if record is None:
            raise ConsumptionNotFoundError("Die Ablesung wurde nicht gefunden")
        meter = self.repository.get_meter(payload.meter_id)
        if meter is None:
            raise ConsumptionNotFoundError("Der aktive Zähler wurde nicht gefunden")
        measured_at = self._as_utc(payload.measured_at)
        self._validate_reading_value(
            meter,
            measured_at,
            payload.value,
            payload.is_reset,
            exclude_id=record.id,
        )
        duplicate = self.repository.duplicate_reading(
            meter.id,
            measured_at,
            exclude_id=record.id,
        )
        if duplicate:
            raise ConsumptionConflictError(
                "Für diesen Zähler existiert zu diesem Zeitpunkt bereits eine Ablesung"
            )
        record.meter_id = meter.id
        record.measured_at = measured_at
        record.value = payload.value
        record.note = payload.note
        record.source = payload.source.value
        record.is_reset = payload.is_reset
        record.immich_asset_id = str(payload.immich_asset_id) if payload.immich_asset_id else None
        record.immich_original_file_name = payload.immich_original_file_name
        record.updated_at = datetime.now(UTC)
        return self._save_reading(record)

    def archive_reading(self, reading_id: UUID) -> None:
        record = self.repository.get_reading(reading_id)
        if record is None:
            raise ConsumptionNotFoundError("Die Ablesung wurde nicht gefunden")
        record.deleted_at = datetime.now(UTC)
        record.updated_at = record.deleted_at
        self.session.add(record)
        self.session.commit()

    def capture_home_assistant(self, meter_id: UUID) -> ConsumptionReadingRead:
        meter = self.repository.get_meter(meter_id)
        if meter is None:
            raise ConsumptionNotFoundError("Der aktive Zähler wurde nicht gefunden")
        if not meter.home_assistant_entity_id:
            raise ConsumptionValidationError(
                "Für den Zähler ist keine Home-Assistant-Entität hinterlegt"
            )
        try:
            result = HomeAssistantService(self.session).entities(
                search=meter.home_assistant_entity_id,
                offset=0,
                limit=1000,
                refresh=True,
                selection_scope=HomeAssistantSelectionScope.ALL,
            )
        except (HomeAssistantConfigurationError, HomeAssistantConnectionError) as exc:
            raise ConsumptionValidationError(str(exc)) from exc
        entity = next(
            (item for item in result.items if item.entity_id == meter.home_assistant_entity_id),
            None,
        )
        if entity is None:
            raise ConsumptionNotFoundError(
                "Die hinterlegte Home-Assistant-Entität wurde nicht gefunden"
            )
        if not entity.available or entity.state.casefold() in {"unknown", "unavailable"}:
            raise ConsumptionValidationError(
                "Die Home-Assistant-Entität liefert aktuell keinen nutzbaren Wert"
            )
        try:
            value = float(entity.state.replace(",", "."))
        except ValueError as exc:
            raise ConsumptionValidationError(
                f"Der Home-Assistant-Zustand „{entity.state}“ ist kein numerischer Zählerstand"
            ) from exc
        measured_at = self._as_utc(entity.last_updated or datetime.now(UTC))
        if self.repository.duplicate_reading(meter.id, measured_at):
            measured_at = datetime.now(UTC)
        payload = ConsumptionReadingWrite(
            meter_id=meter.id,
            measured_at=measured_at,
            value=value,
            note=f"Aus Home Assistant übernommen: {entity.entity_id}",
            source=ConsumptionReadingSource.HOME_ASSISTANT,
            is_reset=False,
        )
        return self.create_reading(payload)

    # Notes
    def list_notes(self) -> list[ConsumptionNoteRead]:
        return [self._note_read(item) for item in self.repository.list_notes()]

    def create_note(self, payload: ConsumptionNoteWrite) -> ConsumptionNoteRead:
        record = ConsumptionNote(
            note_date=self._as_utc(payload.note_date),
            scope=payload.scope.value,
            title=payload.title,
            note=payload.note,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._note_read(record)

    def update_note(self, note_id: UUID, payload: ConsumptionNoteWrite) -> ConsumptionNoteRead:
        record = self.repository.get_note(note_id)
        if record is None:
            raise ConsumptionNotFoundError("Die Verbrauchsnotiz wurde nicht gefunden")
        record.note_date = self._as_utc(payload.note_date)
        record.scope = payload.scope.value
        record.title = payload.title
        record.note = payload.note
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._note_read(record)

    def archive_note(self, note_id: UUID) -> None:
        record = self.repository.get_note(note_id)
        if record is None:
            raise ConsumptionNotFoundError("Die Verbrauchsnotiz wurde nicht gefunden")
        record.deleted_at = datetime.now(UTC)
        record.updated_at = record.deleted_at
        self.session.add(record)
        self.session.commit()

    # Statistics
    def summary(self) -> ConsumptionSummaryRead:
        meters = self.repository.list_meters()
        settings = self.get_settings()
        now = datetime.now(UTC)
        due_before = now - timedelta(days=settings.reminder_days)
        latest_by_meter = {meter.id: self.repository.latest_reading(meter.id) for meter in meters}
        start, end = self._current_month_range()
        current_month = self._period_summary(meters, start, end)
        return ConsumptionSummaryRead(
            meter_count=len(meters),
            reading_count=self.repository.reading_count(),
            readings_last_30_days=self.repository.reading_count_since(now - timedelta(days=30)),
            meters_without_readings=sum(1 for item in latest_by_meter.values() if item is None),
            meters_due_for_reading=sum(
                1
                for item in latest_by_meter.values()
                if item is None or self._aware(item.measured_at) < due_before
            ),
            last_reading_at=(
                self._aware(self.repository.latest_reading().measured_at)
                if self.repository.latest_reading()
                else None
            ),
            current_month=current_month,
        )

    def statistics(self, *, months: int = 12) -> ConsumptionStatisticsRead:
        if months < 1 or months > 60:
            raise ConsumptionValidationError(
                "Es können zwischen 1 und 60 Monate ausgewertet werden"
            )
        meters = self.repository.list_meters()
        periods = self._month_ranges(months)
        series: list[ConsumptionSeries] = []
        for meter in meters:
            points = [
                ConsumptionSeriesPoint(
                    label=label,
                    period_start=start,
                    period_end=end,
                    result=self._consumption_for_meter(meter.id, start, end),
                )
                for label, start, end in periods
            ]
            series.append(
                ConsumptionSeries(
                    key=f"meter:{meter.id}",
                    name=meter.name,
                    meter_id=meter.id,
                    meter_type=ConsumptionMeterType(meter.meter_type),
                    unit=meter.unit,
                    decimals=meter.decimals,
                    virtual=False,
                    points=points,
                )
            )

        for key, name, description in (
            (
                "water_eg",
                "EG Verbrauch",
                "Dusche + Küche + Zählerraum bzw. alle als EG-Komponente markierten Wasserzähler",
            ),
            ("water_rest", "Restliches Haus", "Hauptwasser minus EG Verbrauch"),
        ):
            points: list[ConsumptionSeriesPoint] = []
            for label, start, end in periods:
                virtual = self._virtual_water(meters, start, end)[key]
                points.append(
                    ConsumptionSeriesPoint(
                        label=label,
                        period_start=start,
                        period_end=end,
                        result=virtual,
                    )
                )
            series.append(
                ConsumptionSeries(
                    key=key,
                    name=name,
                    meter_id=None,
                    meter_type=ConsumptionMeterType.WATER,
                    unit="m³",
                    decimals=3,
                    virtual=True,
                    description=description,
                    points=points,
                )
            )
        return ConsumptionStatisticsRead(months=months, series=series)

    def dashboard_comparisons(self) -> list[ConsumptionComparisonRead]:
        periods = self._month_ranges(2)
        if len(periods) != 2:
            return []
        _, previous_start, previous_end = periods[0]
        _, current_start, current_end = periods[1]
        rows: list[ConsumptionComparisonRead] = []
        for meter_type, medium, label in (
            (ConsumptionMeterType.WATER, "water", "Hauptwasser"),
            (ConsumptionMeterType.ELECTRICITY_GRID, "electricity", "Strombezug"),
            (ConsumptionMeterType.ELECTRICITY_PV, "pv_generation", "PV-Erzeugung"),
            (ConsumptionMeterType.ELECTRICITY_FEED_IN, "pv_feed_in", "PV eingespeist"),
            (ConsumptionMeterType.GAS, "gas", "Gas"),
        ):
            dashboard_meters = self.repository.active_dashboard_meters(meter_type.value)
            meter = dashboard_meters[0] if dashboard_meters else None
            if meter is None and meter_type == ConsumptionMeterType.WATER:
                meter = self.repository.active_main_water_meter()
            if meter is None and meter_type not in {
                ConsumptionMeterType.ELECTRICITY_PV,
                ConsumptionMeterType.ELECTRICITY_FEED_IN,
            }:
                meter = self.repository.first_active_meter_by_type(meter_type.value)
            if meter is None and meter_type in {
                ConsumptionMeterType.ELECTRICITY_PV,
                ConsumptionMeterType.ELECTRICITY_FEED_IN,
            }:
                continue
            if meter is None:
                rows.append(
                    ConsumptionComparisonRead(
                        medium=medium,
                        name=label,
                        meter_id=None,
                        unit=None,
                        decimals=2,
                        current_value=None,
                        previous_value=None,
                        difference=None,
                        percent_change=None,
                        trend="unavailable",
                        comparison_available=False,
                        incomplete=True,
                    )
                )
                continue
            selected_meters = (
                dashboard_meters
                if meter_type in {
                    ConsumptionMeterType.ELECTRICITY_PV,
                    ConsumptionMeterType.ELECTRICITY_FEED_IN,
                } and dashboard_meters
                else [meter]
            )
            current_results = [
                self._consumption_for_meter(item.id, current_start, current_end)
                for item in selected_meters
            ]
            previous_results = [
                self._consumption_for_meter(item.id, previous_start, previous_end)
                for item in selected_meters
            ]
            current = self._combine(current_results, require_all=True)
            previous = self._combine(previous_results, require_all=True)
            difference = (
                current.value - previous.value
                if current.value is not None and previous.value is not None
                else None
            )
            percent = (
                difference / previous.value * 100
                if difference is not None and previous.value not in (None, 0)
                else None
            )
            trend = "unavailable"
            if difference is not None:
                trend = (
                    "increased" if difference > 0 else "decreased" if difference < 0 else "equal"
                )
            rows.append(
                ConsumptionComparisonRead(
                    medium=medium,
                    name=label,
                    meter_id=meter.id if len(selected_meters) == 1 else None,
                    unit=meter.unit,
                    decimals=meter.decimals,
                    current_value=current.value,
                    previous_value=previous.value,
                    difference=difference,
                    percent_change=percent,
                    trend=trend,
                    comparison_available=difference is not None,
                    incomplete=current.incomplete or previous.incomplete,
                )
            )
        return rows

    def reading_reminders(self, *, days_ahead: int = 3) -> list[ConsumptionReadingReminderRead]:
        if days_ahead < 0 or days_ahead > 31:
            raise ConsumptionValidationError(
                "Der Erinnerungshorizont muss zwischen 0 und 31 liegen"
            )
        zone = self._timezone()
        local_now = datetime.now(zone)
        today = local_now.date()
        period_start = datetime(today.year, today.month, 1, tzinfo=zone)
        period_end = self._add_months(period_start, 1)
        fallback_interval_days = self.get_settings().reminder_days
        reminders: list[ConsumptionReadingReminderRead] = []
        for meter in self.repository.list_meters():
            has_monthly_schedule = (
                meter.reading_schedule_day is not None or meter.reading_schedule_last_day
            )
            if has_monthly_schedule:
                readings = self.repository.list_readings(
                    meter_id=meter.id,
                    start=period_start.astimezone(UTC),
                    end=period_end.astimezone(UTC),
                    limit=1,
                )
                if readings:
                    continue
                last_day = monthrange(today.year, today.month)[1]
                configured_days = json.loads(meter.reminder_days_json or "[]")
                primary_day = (
                    last_day if meter.reading_schedule_last_day else meter.reading_schedule_day
                )
                days = sorted(
                    {
                        min(int(day), last_day)
                        for day in [primary_day, *configured_days]
                        if day is not None
                    }
                )
                dates = [date(today.year, today.month, day) for day in days]
                upcoming = [candidate for candidate in dates if candidate >= today]
                due_date = upcoming[0] if upcoming else dates[-1]
            else:
                latest = self.repository.latest_reading(meter.id)
                due_date = interval_due_date(
                    today=today,
                    latest_measured_at=latest.measured_at if latest else None,
                    reminder_days=fallback_interval_days,
                    zone=zone,
                )

            remaining = (due_date - today).days
            if remaining > days_ahead:
                continue
            status = "upcoming" if remaining > 0 else "today" if remaining == 0 else "overdue"
            due_local = datetime.combine(due_date, time(hour=12), tzinfo=zone)
            reminders.append(
                ConsumptionReadingReminderRead(
                    meter_id=meter.id,
                    meter_name=meter.name,
                    unit=meter.unit,
                    due_at=due_local.astimezone(UTC),
                    days_remaining=remaining,
                    status=status,
                )
            )
        return sorted(reminders, key=lambda item: (item.due_at, item.meter_name.casefold()))

    # Import
    def preview_import(self, *, file_name: str, content: bytes) -> ConsumptionImportPreviewRead:
        self._validate_upload(file_name, content)
        if self._is_sqlite(file_name, content):
            snapshot = self._read_legacy_sqlite(content)
            names = [str(item.get("name") or "").strip() for item in snapshot["meters"]]
            matched, missing = self._match_meter_names(names)
            warnings = list(snapshot["warnings"])
            if not snapshot["meters"] and not snapshot["readings"]:
                warnings.append(
                    "Die Datei enthält keine Zähler- oder Ablesungstabellen. Bei einer "
                    "laufenden WAL-Datenbank bitte auch die WAL-Datei sichern oder vorher "
                    "den Container stoppen."
                )
            return ConsumptionImportPreviewRead(
                format="legacy_sqlite",
                file_name=file_name,
                meter_count=len(snapshot["meters"]),
                reading_count=len(snapshot["readings"]),
                note_count=len(snapshot["notes"]),
                matched_meters=matched,
                missing_meters=missing,
                warnings=warnings,
            )
        parsed = self._read_csv(content, file_name=file_name)
        matched, missing = self._match_meter_names(sorted(parsed["meter_names"]))
        return ConsumptionImportPreviewRead(
            format="csv",
            file_name=file_name,
            meter_count=len(parsed["meter_names"]),
            reading_count=len(parsed["rows"]),
            matched_meters=matched,
            missing_meters=missing,
            warnings=list(parsed["warnings"]),
        )

    def import_file(
        self,
        *,
        file_name: str,
        content: bytes,
        create_missing_meters: bool,
        overwrite: bool,
    ) -> ConsumptionImportResultRead:
        self._validate_upload(file_name, content)
        if self._is_sqlite(file_name, content):
            return self._import_legacy_sqlite(
                file_name=file_name,
                content=content,
                create_missing_meters=create_missing_meters,
                overwrite=overwrite,
            )
        return self._import_csv(
            file_name=file_name,
            content=content,
            create_missing_meters=create_missing_meters,
            overwrite=overwrite,
        )

    # Internal validation and projection
    def _validate_meter(
        self, payload: ConsumptionMeterWrite, *, record_id: UUID | None = None
    ) -> None:
        if payload.water_role == ConsumptionWaterRole.MAIN:
            existing = self.repository.active_main_water_meter(exclude_id=record_id)
            if existing is not None:
                raise ConsumptionConflictError("Es kann nur einen aktiven Hauptwasserzähler geben")
        if payload.asset_id:
            asset = self.session.get(Asset, payload.asset_id)
            if asset is None or asset.deleted_at is not None:
                raise ConsumptionValidationError(
                    "Das zugeordnete Asset wurde nicht gefunden oder ist archiviert"
                )
        if payload.location_id:
            location = self.session.get(Location, payload.location_id)
            if location is None or location.deleted_at is not None:
                raise ConsumptionValidationError(
                    "Der zugeordnete Ort wurde nicht gefunden oder ist archiviert"
                )
        if payload.parent_meter_id:
            if payload.parent_meter_id == record_id:
                raise ConsumptionValidationError(
                    "Ein Zähler kann nicht sein eigener übergeordneter Zähler sein"
                )
            parent = self.repository.get_meter(payload.parent_meter_id)
            if parent is None:
                raise ConsumptionValidationError("Der übergeordnete Zähler wurde nicht gefunden")
            visited = {record_id} if record_id else set()
            while parent.parent_meter_id:
                if parent.parent_meter_id in visited:
                    raise ConsumptionValidationError(
                        "Die Zählerhierarchie würde einen Kreis bilden"
                    )
                visited.add(parent.id)
                next_parent = self.repository.get_meter(parent.parent_meter_id)
                if next_parent is None:
                    break
                parent = next_parent
        for entity_id in (
            payload.home_assistant_entity_id,
            payload.home_assistant_power_entity_id,
            payload.home_assistant_voltage_entity_id,
        ):
            if entity_id and "." not in entity_id:
                raise ConsumptionValidationError(
                    "Eine Home-Assistant-Entitäts-ID muss einen Punkt enthalten"
                )

    def _validate_reading_value(
        self,
        meter: ConsumptionMeter,
        measured_at: datetime,
        value: float,
        is_reset: bool,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        previous = self.repository.previous_reading(
            meter.id,
            measured_at,
            exclude_id=exclude_id,
        )
        if previous and value < previous.value and not is_reset:
            raise ConsumptionValidationError(
                "Der Zählerstand ist kleiner als die vorherige Ablesung. Markiere einen "
                "Zählerwechsel/Reset oder korrigiere den Wert."
            )

    def _save_meter(self, record: ConsumptionMeter) -> ConsumptionMeterRead:
        try:
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
        except IntegrityError as exc:
            self.session.rollback()
            raise ConsumptionConflictError("Der Zähler verletzt eine Eindeutigkeitsregel") from exc
        return self._meter_read(record)

    def _save_reading(self, record: ConsumptionReading) -> ConsumptionReadingRead:
        try:
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
        except IntegrityError as exc:
            self.session.rollback()
            raise ConsumptionConflictError("Die Ablesung ist bereits vorhanden") from exc
        return self._reading_read(record)

    def _meter_read(self, record: ConsumptionMeter) -> ConsumptionMeterRead:
        asset = self.session.get(Asset, record.asset_id) if record.asset_id else None
        effective_location_id = record.location_id or (asset.location_id if asset else None)
        location = (
            self.session.get(Location, effective_location_id)
            if effective_location_id
            else None
        )
        location_path = None
        if location is not None:
            projection = LocationRepository(self.session).get_projection(
                location.id, include_deleted=True
            )
            location_path = projection.path if projection else location.name
        parent = (
            self.repository.get_meter(record.parent_meter_id, include_archived=True)
            if record.parent_meter_id
            else None
        )
        latest = self.repository.latest_reading(record.id)
        reminder_days = self.get_settings().reminder_days
        due = latest is None or self._aware(latest.measured_at) < datetime.now(UTC) - timedelta(
            days=reminder_days
        )
        return ConsumptionMeterRead(
            id=record.id,
            name=record.name,
            meter_type=ConsumptionMeterType(record.meter_type),
            unit=record.unit,
            decimals=record.decimals,
            sort_order=record.sort_order,
            serial_number=record.serial_number,
            asset_id=record.asset_id,
            asset_name=asset.name if asset else None,
            asset_code=asset.jarvis_code if asset else None,
            location_id=effective_location_id,
            location_name=location.name if location else None,
            location_path=location_path,
            parent_meter_id=record.parent_meter_id,
            parent_meter_name=parent.name if parent else None,
            home_assistant_entity_id=record.home_assistant_entity_id,
            home_assistant_power_entity_id=record.home_assistant_power_entity_id,
            home_assistant_voltage_entity_id=record.home_assistant_voltage_entity_id,
            water_role=ConsumptionWaterRole(record.water_role),
            primary_for_dashboard=record.primary_for_dashboard,
            reading_schedule_day=record.reading_schedule_day,
            reading_schedule_last_day=record.reading_schedule_last_day,
            reminder_days=list(json.loads(record.reminder_days_json or "[]")),
            notes=record.notes,
            latest_value=latest.value if latest else None,
            latest_measured_at=self._aware(latest.measured_at) if latest else None,
            reading_count=self.repository.reading_count(record.id),
            due_for_reading=due,
            archived=record.deleted_at is not None,
            created_at=self._aware(record.created_at),
            updated_at=self._aware(record.updated_at),
        )

    def _reading_read(self, record: ConsumptionReading) -> ConsumptionReadingRead:
        meter = self.repository.get_meter(record.meter_id, include_archived=True)
        if meter is None:
            raise ConsumptionNotFoundError("Der Zähler der Ablesung wurde nicht gefunden")
        previous = self.repository.previous_reading(
            record.meter_id,
            self._aware(record.measured_at),
            exclude_id=record.id,
        )
        delta = None
        if previous and not record.is_reset and record.value >= previous.value:
            delta = record.value - previous.value
        warning, message = self._plausibility(record, previous)
        external_id = None
        if record.immich_asset_id:
            try:
                external_id = UUID(record.immich_asset_id)
            except ValueError:
                external_id = None
        return ConsumptionReadingRead(
            id=record.id,
            meter_id=record.meter_id,
            meter_name=meter.name,
            unit=meter.unit,
            decimals=meter.decimals,
            measured_at=self._aware(record.measured_at),
            value=record.value,
            previous_value=previous.value if previous else None,
            delta=delta,
            note=record.note,
            source=ConsumptionReadingSource(record.source),
            is_reset=record.is_reset,
            immich_asset_id=external_id,
            immich_original_file_name=record.immich_original_file_name,
            immich_thumbnail_url=(
                f"/api/v1/immich/assets/{external_id}/thumbnail" if external_id else None
            ),
            plausibility_warning=warning,
            plausibility_message=message,
            created_at=self._aware(record.created_at),
            updated_at=self._aware(record.updated_at),
        )

    def _note_read(self, record: ConsumptionNote) -> ConsumptionNoteRead:
        return ConsumptionNoteRead(
            id=record.id,
            note_date=self._aware(record.note_date),
            scope=ConsumptionNoteScope(record.scope),
            title=record.title,
            note=record.note,
            created_at=self._aware(record.created_at),
            updated_at=self._aware(record.updated_at),
        )

    def _plausibility(
        self,
        record: ConsumptionReading,
        previous: ConsumptionReading | None,
    ) -> tuple[bool, str | None]:
        if previous is None or record.is_reset or record.value < previous.value:
            return False, None
        current_days = max(
            (self._aware(record.measured_at) - self._aware(previous.measured_at)).total_seconds()
            / 86400,
            1 / 1440,
        )
        current_rate = (record.value - previous.value) / current_days
        history = self.repository.recent_readings_before(
            record.meter_id,
            self._aware(record.measured_at),
            limit=14,
            exclude_id=record.id,
        )
        rates: list[float] = []
        for left, right in zip(history, history[1:], strict=False):
            if right.is_reset or right.value < left.value:
                continue
            days = (
                self._aware(right.measured_at) - self._aware(left.measured_at)
            ).total_seconds() / 86400
            if days > 0:
                rates.append((right.value - left.value) / days)
        if len(rates) < 2:
            return False, None
        average = sum(rates) / len(rates)
        if average <= 0:
            return False, None
        threshold = self.get_settings().plausibility_threshold_percent / 100
        if current_rate <= average * threshold:
            return False, None
        return (
            True,
            "Der Tagesverbrauch liegt über "
            f"{self.get_settings().plausibility_threshold_percent}% "
            "des bisherigen Durchschnitts.",
        )

    # Calculation helpers
    def _consumption_for_meter(
        self,
        meter_id: UUID,
        start: datetime,
        end: datetime,
    ) -> ConsumptionPeriodResult:
        if end <= start:
            return ConsumptionPeriodResult(
                value=None,
                estimated=False,
                incomplete=True,
                reset_detected=False,
            )
        ordered = self.repository.readings_for_calculation(meter_id, start, end)
        if len(ordered) < 2:
            return ConsumptionPeriodResult(
                value=None,
                estimated=False,
                incomplete=True,
                reset_detected=False,
            )
        total = 0.0
        has_value = False
        estimated = False
        reset_detected = False
        covered_start: datetime | None = None
        covered_end: datetime | None = None
        for current, following in zip(ordered, ordered[1:], strict=False):
            current_at = self._aware(current.measured_at)
            following_at = self._aware(following.measured_at)
            if following_at <= current_at:
                continue
            if following.is_reset or following.value < current.value:
                reset_detected = True
                continue
            overlap_start = max(start, current_at)
            overlap_end = min(end, following_at)
            if overlap_end <= overlap_start:
                continue
            seconds_total = (following_at - current_at).total_seconds()
            seconds_overlap = (overlap_end - overlap_start).total_seconds()
            if seconds_total <= 0 or seconds_overlap <= 0:
                continue
            factor = seconds_overlap / seconds_total
            total += (following.value - current.value) * factor
            has_value = True
            if factor < 0.999999 or overlap_start != current_at or overlap_end != following_at:
                estimated = True
            covered_start = (
                overlap_start if covered_start is None else min(covered_start, overlap_start)
            )
            covered_end = overlap_end if covered_end is None else max(covered_end, overlap_end)
        if not has_value:
            return ConsumptionPeriodResult(
                value=None,
                estimated=estimated,
                incomplete=True,
                reset_detected=reset_detected,
            )
        zone = self._timezone()
        end_gap_seconds = (end - covered_end).total_seconds() if covered_end else float("inf")
        end_is_covered = end_gap_seconds <= 1
        if covered_end is not None and end_gap_seconds > 1:
            end_is_covered = (
                end.astimezone(zone).date() == covered_end.astimezone(zone).date()
                and end.astimezone(zone).date() == datetime.now(zone).date()
            )
        incomplete = (
            covered_start is None
            or covered_end is None
            or (covered_start - start).total_seconds() > 1
            or not end_is_covered
        )
        return ConsumptionPeriodResult(
            value=total,
            estimated=estimated,
            incomplete=incomplete,
            reset_detected=reset_detected,
        )

    @staticmethod
    def _combine(
        results: Iterable[ConsumptionPeriodResult], *, require_all: bool = False
    ) -> ConsumptionPeriodResult:
        rows = list(results)
        values = [row.value for row in rows if row.value is not None]
        return ConsumptionPeriodResult(
            value=sum(values) if values else None,
            estimated=any(row.estimated for row in rows),
            incomplete=(
                any(row.incomplete for row in rows)
                or (require_all and any(row.value is None for row in rows))
            ),
            reset_detected=any(row.reset_detected for row in rows),
        )

    def _virtual_water(
        self,
        meters: list[ConsumptionMeter],
        start: datetime,
        end: datetime,
    ) -> dict[str, ConsumptionPeriodResult]:
        eg_meters = [
            item
            for item in meters
            if item.meter_type == ConsumptionMeterType.WATER.value
            and item.water_role == ConsumptionWaterRole.EG_COMPONENT.value
        ]
        eg_result = self._combine(
            [self._consumption_for_meter(item.id, start, end) for item in eg_meters],
            require_all=True,
        )
        main = next(
            (
                item
                for item in meters
                if item.meter_type == ConsumptionMeterType.WATER.value
                and item.water_role == ConsumptionWaterRole.MAIN.value
            ),
            None,
        )
        if main is None:
            rest = ConsumptionPeriodResult(
                value=None,
                estimated=eg_result.estimated,
                incomplete=True,
                reset_detected=eg_result.reset_detected,
            )
        else:
            main_result = self._consumption_for_meter(main.id, start, end)
            rest_value = (
                main_result.value - eg_result.value
                if main_result.value is not None and eg_result.value is not None
                else None
            )
            rest = ConsumptionPeriodResult(
                value=rest_value,
                estimated=main_result.estimated or eg_result.estimated,
                incomplete=main_result.incomplete or eg_result.incomplete or rest_value is None,
                reset_detected=main_result.reset_detected or eg_result.reset_detected,
            )
        return {"water_eg": eg_result, "water_rest": rest}

    def _period_summary(
        self,
        meters: list[ConsumptionMeter],
        start: datetime,
        end: datetime,
    ) -> list[ConsumptionVirtualResultRead]:
        results: list[ConsumptionVirtualResultRead] = []
        main = next(
            (item for item in meters if item.water_role == ConsumptionWaterRole.MAIN.value),
            None,
        )
        if main:
            results.append(
                ConsumptionVirtualResultRead(
                    key="water_main",
                    name="Hauptwasser",
                    description="Verbrauch am Hauptwasserzähler",
                    unit=main.unit,
                    decimals=main.decimals,
                    result=self._consumption_for_meter(main.id, start, end),
                )
            )
        virtual = self._virtual_water(meters, start, end)
        results.extend(
            [
                ConsumptionVirtualResultRead(
                    key="water_eg",
                    name="EG Verbrauch",
                    description="Dusche + Küche + Zählerraum bzw. markierte EG-Komponenten",
                    unit="m³",
                    decimals=3,
                    result=virtual["water_eg"],
                ),
                ConsumptionVirtualResultRead(
                    key="water_rest",
                    name="Restliches Haus",
                    description="Hauptwasser minus EG Verbrauch",
                    unit="m³",
                    decimals=3,
                    result=virtual["water_rest"],
                ),
            ]
        )
        for meter_type, name in (
            (ConsumptionMeterType.ELECTRICITY_GRID, "Strom Netzbezug"),
            (ConsumptionMeterType.ELECTRICITY_PV, "PV-Erzeugung"),
            (ConsumptionMeterType.ELECTRICITY_FEED_IN, "Netzeinspeisung"),
            (ConsumptionMeterType.GAS, "Gas"),
            (ConsumptionMeterType.HEAT, "Wärme"),
            (ConsumptionMeterType.OIL, "Heizöl"),
        ):
            matching = [item for item in meters if item.meter_type == meter_type.value]
            if not matching:
                continue
            combined = self._combine(
                [self._consumption_for_meter(item.id, start, end) for item in matching]
            )
            results.append(
                ConsumptionVirtualResultRead(
                    key=f"type:{meter_type.value}",
                    name=name,
                    description=f"Summe aller aktiven Zähler des Typs {name}",
                    unit=matching[0].unit,
                    decimals=max(item.decimals for item in matching),
                    result=combined,
                )
            )
        return results

    def _current_month_range(self) -> tuple[datetime, datetime]:
        zone = self._timezone()
        local_now = datetime.now(zone)
        start_local = datetime(local_now.year, local_now.month, 1, tzinfo=zone)
        return start_local.astimezone(UTC), local_now.astimezone(UTC)

    def _month_ranges(self, months: int) -> list[tuple[str, datetime, datetime]]:
        zone = self._timezone()
        local_now = datetime.now(zone)
        current = datetime(local_now.year, local_now.month, 1, tzinfo=zone)
        first = self._add_months(current, -(months - 1))
        result: list[tuple[str, datetime, datetime]] = []
        for index in range(months):
            start_local = self._add_months(first, index)
            end_local = self._add_months(start_local, 1)
            if start_local.year == local_now.year and start_local.month == local_now.month:
                end_local = local_now
            label = f"{GERMAN_MONTHS[start_local.month - 1]} {start_local.year}"
            result.append((label, start_local.astimezone(UTC), end_local.astimezone(UTC)))
        return result

    @staticmethod
    def _add_months(value: datetime, amount: int) -> datetime:
        absolute = value.year * 12 + value.month - 1 + amount
        year, month_index = divmod(absolute, 12)
        return value.replace(year=year, month=month_index + 1, day=1)

    def _timezone(self) -> ZoneInfo:
        application = self.session.get(ApplicationSetting, 1)
        name = application.timezone if application else "Europe/Berlin"
        try:
            return ZoneInfo(name)
        except ZoneInfoNotFoundError:
            return ZoneInfo("UTC")

    # Import helpers
    @staticmethod
    def _validate_upload(file_name: str, content: bytes) -> None:
        if not file_name.strip():
            raise ConsumptionImportError("Der Dateiname fehlt")
        if not content:
            raise ConsumptionImportError("Die Importdatei ist leer")
        if len(content) > 50 * 1024 * 1024:
            raise ConsumptionImportError("Die Importdatei darf höchstens 50 MB groß sein")

    @staticmethod
    def _is_sqlite(file_name: str, content: bytes) -> bool:
        return content.startswith(b"SQLite format 3\x00") or file_name.casefold().endswith(
            (".sqlite", ".sqlite3", ".db")
        )

    def _read_legacy_sqlite(self, content: bytes) -> dict[str, object]:
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=True) as temporary:
            temporary.write(content)
            temporary.flush()
            uri = f"file:{Path(temporary.name).as_posix()}?mode=ro"
            try:
                connection = sqlite3.connect(uri, uri=True)
            except sqlite3.Error as exc:
                raise ConsumptionImportError(
                    "Die SQLite-Datei konnte nicht geöffnet werden"
                ) from exc
            connection.row_factory = sqlite3.Row
            try:
                integrity = connection.execute("PRAGMA integrity_check").fetchone()
                if integrity is None or integrity[0] != "ok":
                    raise ConsumptionImportError("Die SQLite-Datei ist beschädigt")
                tables = {
                    str(row[0])
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
                meters = (
                    [dict(row) for row in connection.execute("SELECT * FROM meters ORDER BY id")]
                    if "meters" in tables
                    else []
                )
                readings = (
                    [dict(row) for row in connection.execute("SELECT * FROM readings ORDER BY id")]
                    if "readings" in tables
                    else []
                )
                notes = (
                    [dict(row) for row in connection.execute("SELECT * FROM notes ORDER BY id")]
                    if "notes" in tables
                    else []
                )
                settings = (
                    {
                        str(row["key"]): str(row["value"])
                        for row in connection.execute("SELECT key, value FROM app_settings")
                    }
                    if "app_settings" in tables
                    else {}
                )
            except sqlite3.Error as exc:
                raise ConsumptionImportError(
                    "Das Altdatenbankschema konnte nicht gelesen werden"
                ) from exc
            finally:
                connection.close()
        warnings: list[str] = []
        if "meters" not in tables:
            warnings.append("Tabelle meters fehlt")
        if "readings" not in tables:
            warnings.append("Tabelle readings fehlt")
        return {
            "meters": meters,
            "readings": readings,
            "notes": notes,
            "settings": settings,
            "warnings": warnings,
        }

    def _import_legacy_sqlite(
        self,
        *,
        file_name: str,
        content: bytes,
        create_missing_meters: bool,
        overwrite: bool,
    ) -> ConsumptionImportResultRead:
        snapshot = self._read_legacy_sqlite(content)
        meters_created = 0
        readings_created = 0
        readings_updated = 0
        duplicates_skipped = 0
        rows_skipped = 0
        notes_created = 0
        errors: list[str] = []
        meter_map: dict[int, ConsumptionMeter] = {}
        try:
            for source in snapshot["meters"]:
                legacy_id = int(source.get("id"))
                name = str(source.get("name") or "").strip()
                if not name:
                    rows_skipped += 1
                    continue
                target = self.repository.find_meter_by_name(name, include_archived=True)
                if target is None and create_missing_meters:
                    meter_type = self._legacy_meter_type(str(source.get("kind") or ""), name)
                    target = ConsumptionMeter(
                        name=name,
                        meter_type=meter_type.value,
                        unit=str(source.get("unit") or self._default_unit(meter_type)),
                        decimals=self._bounded_int(source.get("decimals"), 3, 0, 6),
                        sort_order=self._bounded_int(source.get("sort_order"), 100, 0, 100000),
                        water_role=self._water_role_for_name(name, meter_type).value,
                    )
                    self.session.add(target)
                    self.session.flush()
                    meters_created += 1
                    if not bool(source.get("active", 1)):
                        target.deleted_at = datetime.now(UTC)
                if target is not None:
                    meter_map[legacy_id] = target
                else:
                    errors.append(f"Zähler „{name}“ fehlt und wurde nicht automatisch angelegt")

            for source in snapshot["readings"]:
                try:
                    legacy_meter_id = int(source.get("meter_id"))
                    meter = meter_map.get(legacy_meter_id)
                    if meter is None:
                        rows_skipped += 1
                        continue
                    measured_at = self._parse_datetime(source.get("measured_at"))
                    value = float(source.get("value"))
                    duplicate = self.repository.duplicate_reading(meter.id, measured_at)
                    if duplicate is not None:
                        if overwrite:
                            duplicate.value = value
                            duplicate.note = self._optional_text(source.get("note"))
                            duplicate.source = ConsumptionReadingSource.LEGACY_SQLITE.value
                            duplicate.is_reset = bool(source.get("is_reset", 0))
                            duplicate.immich_asset_id = self._optional_text(
                                source.get("immich_asset_id")
                            )
                            duplicate.immich_original_file_name = self._optional_text(
                                source.get("immich_image_url")
                            )
                            duplicate.updated_at = datetime.now(UTC)
                            self.session.add(duplicate)
                            readings_updated += 1
                        else:
                            duplicates_skipped += 1
                        continue
                    self.session.add(
                        ConsumptionReading(
                            meter_id=meter.id,
                            measured_at=measured_at,
                            value=value,
                            note=self._optional_text(source.get("note")),
                            source=ConsumptionReadingSource.LEGACY_SQLITE.value,
                            is_reset=bool(source.get("is_reset", 0)),
                            immich_asset_id=self._optional_text(source.get("immich_asset_id")),
                            immich_original_file_name=self._optional_text(
                                source.get("immich_image_url")
                            ),
                        )
                    )
                    readings_created += 1
                except (TypeError, ValueError, ConsumptionImportError) as exc:
                    rows_skipped += 1
                    if len(errors) < 50:
                        errors.append(f"Ablesung {source.get('id', '?')}: {exc}")

            for source in snapshot["notes"]:
                try:
                    self.session.add(
                        ConsumptionNote(
                            note_date=self._parse_datetime(source.get("note_date")),
                            scope=self._legacy_note_scope(source.get("scope")),
                            title=str(source.get("title") or "Verbrauchsnotiz").strip(),
                            note=self._optional_text(source.get("note")),
                        )
                    )
                    notes_created += 1
                except (TypeError, ValueError, ConsumptionImportError) as exc:
                    rows_skipped += 1
                    if len(errors) < 50:
                        errors.append(f"Notiz {source.get('id', '?')}: {exc}")

            settings_imported = self._apply_legacy_settings(snapshot["settings"])
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConsumptionImportError("Der Altdatenimport verletzt eine Datenbankregel") from exc
        except Exception:
            self.session.rollback()
            raise
        return ConsumptionImportResultRead(
            format="legacy_sqlite",
            file_name=file_name,
            meters_created=meters_created,
            readings_created=readings_created,
            readings_updated=readings_updated,
            duplicates_skipped=duplicates_skipped,
            rows_skipped=rows_skipped,
            notes_created=notes_created,
            settings_imported=settings_imported,
            errors=errors,
        )

    def _read_csv(self, content: bytes, *, file_name: str) -> dict[str, object]:
        text = self._decode_text(content)
        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=";,\t,")
        except csv.Error:
            dialect = csv.excel
            dialect.delimiter = ";"
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        if not reader.fieldnames:
            raise ConsumptionImportError("Die CSV-Datei enthält keine Spaltenüberschrift")
        field_map = {self._slug(name): name for name in reader.fieldnames if name}
        date_field = self._first_field(
            field_map, "datum", "date", "zeitpunkt", "measuredat", "timestamp"
        )
        meter_field = self._first_field(field_map, "zahler", "zaehler", "meter", "name")
        value_field = self._first_field(field_map, "wert", "value", "zahlerstand", "zaehlerstand")
        note_field = self._first_field(field_map, "notiz", "note", "bemerkung")
        reset_field = self._first_field(
            field_map, "reset", "isreset", "zahlerwechsel", "zaehlerwechsel"
        )
        if not date_field:
            raise ConsumptionImportError("Die CSV-Datei benötigt eine Datumsspalte")
        rows: list[dict[str, object]] = []
        meter_names: set[str] = set()
        warnings: list[str] = []
        generic_fields = {date_field, meter_field, value_field, note_field, reset_field, None}
        wide_fields = [name for name in reader.fieldnames if name not in generic_fields]
        for index, row in enumerate(reader, start=2):
            try:
                measured_at = self._parse_datetime(row.get(date_field))
            except ConsumptionImportError as exc:
                warnings.append(f"Zeile {index}: {exc}")
                continue
            note = self._optional_text(row.get(note_field)) if note_field else None
            is_reset = self._truthy(row.get(reset_field)) if reset_field else False
            if meter_field and value_field:
                name = str(row.get(meter_field) or "").strip()
                raw_value = str(row.get(value_field) or "").strip()
                if not name or not raw_value:
                    continue
                try:
                    value = self._parse_number(raw_value)
                except ValueError:
                    warnings.append(f"Zeile {index}: ungültiger Zahlenwert")
                    continue
                rows.append(
                    {
                        "meter_name": name,
                        "measured_at": measured_at,
                        "value": value,
                        "note": note,
                        "is_reset": is_reset,
                    }
                )
                meter_names.add(name)
                continue
            for column in wide_fields:
                raw_value = str(row.get(column) or "").strip()
                if not raw_value:
                    continue
                try:
                    value = self._parse_number(raw_value)
                except ValueError:
                    warnings.append(f"Zeile {index}, Spalte {column}: ungültiger Zahlenwert")
                    continue
                rows.append(
                    {
                        "meter_name": column,
                        "measured_at": measured_at,
                        "value": value,
                        "note": note,
                        "is_reset": is_reset,
                    }
                )
                meter_names.add(column)
        if not rows and len(wide_fields) == 1:
            warnings.append(
                "Keine Werte erkannt. Die einzige Wertespalte "
                f"„{wide_fields[0]}“ konnte nicht verarbeitet werden."
            )
        return {
            "rows": rows,
            "meter_names": meter_names,
            "warnings": warnings,
            "file_name": file_name,
        }

    def _import_csv(
        self,
        *,
        file_name: str,
        content: bytes,
        create_missing_meters: bool,
        overwrite: bool,
    ) -> ConsumptionImportResultRead:
        parsed = self._read_csv(content, file_name=file_name)
        meters_created = 0
        readings_created = 0
        readings_updated = 0
        duplicates_skipped = 0
        rows_skipped = 0
        errors: list[str] = list(parsed["warnings"][:50])
        meter_map: dict[str, ConsumptionMeter] = {}
        try:
            for name in sorted(parsed["meter_names"]):
                target = self.repository.find_meter_by_name(name, include_archived=True)
                if target is None and create_missing_meters:
                    meter_type = self._legacy_meter_type("", name)
                    target = ConsumptionMeter(
                        name=name.strip(),
                        meter_type=meter_type.value,
                        unit=self._default_unit(meter_type),
                        decimals=3
                        if meter_type in {ConsumptionMeterType.WATER, ConsumptionMeterType.GAS}
                        else 1,
                        sort_order=100 + meters_created,
                        water_role=self._water_role_for_name(name, meter_type).value,
                    )
                    self.session.add(target)
                    self.session.flush()
                    meters_created += 1
                if target is not None:
                    meter_map[self._slug(name)] = target
                else:
                    errors.append(f"Zähler „{name}“ fehlt und wurde nicht automatisch angelegt")

            for row in parsed["rows"]:
                meter = meter_map.get(self._slug(str(row["meter_name"])))
                if meter is None:
                    rows_skipped += 1
                    continue
                measured_at = row["measured_at"]
                duplicate = self.repository.duplicate_reading(meter.id, measured_at)
                if duplicate:
                    if overwrite:
                        duplicate.value = float(row["value"])
                        duplicate.note = row["note"]
                        duplicate.is_reset = bool(row["is_reset"])
                        duplicate.source = ConsumptionReadingSource.CSV.value
                        duplicate.updated_at = datetime.now(UTC)
                        self.session.add(duplicate)
                        readings_updated += 1
                    else:
                        duplicates_skipped += 1
                    continue
                self.session.add(
                    ConsumptionReading(
                        meter_id=meter.id,
                        measured_at=measured_at,
                        value=float(row["value"]),
                        note=row["note"],
                        source=ConsumptionReadingSource.CSV.value,
                        is_reset=bool(row["is_reset"]),
                    )
                )
                readings_created += 1
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConsumptionImportError("Der CSV-Import verletzt eine Datenbankregel") from exc
        except Exception:
            self.session.rollback()
            raise
        return ConsumptionImportResultRead(
            format="csv",
            file_name=file_name,
            meters_created=meters_created,
            readings_created=readings_created,
            readings_updated=readings_updated,
            duplicates_skipped=duplicates_skipped,
            rows_skipped=rows_skipped,
            errors=errors,
        )

    def _match_meter_names(self, names: list[str]) -> tuple[list[str], list[str]]:
        matched: list[str] = []
        missing: list[str] = []
        for name in names:
            if not name:
                continue
            if self.repository.find_meter_by_name(name, include_archived=True):
                matched.append(name)
            else:
                missing.append(name)
        return sorted(set(matched)), sorted(set(missing))

    def _apply_legacy_settings(self, settings: dict[str, str]) -> bool:
        if not settings:
            return False
        record = self.repository.get_settings() or ConsumptionSetting()
        changed = False
        if "reminder_days" in settings:
            record.reminder_days = self._bounded_int(settings["reminder_days"], 31, 1, 3650)
            changed = True
        if "plausibility_threshold_percent" in settings:
            record.plausibility_threshold_percent = self._bounded_int(
                settings["plausibility_threshold_percent"], 150, 100, 10000
            )
            changed = True
        if changed:
            record.updated_at = datetime.now(UTC)
            self.session.add(record)
        return changed

    @classmethod
    def _legacy_meter_type(cls, kind: str, name: str) -> ConsumptionMeterType:
        normalized = cls._slug(f"{kind} {name}")
        if "wasser" in normalized or kind.casefold() == "water":
            return ConsumptionMeterType.WATER
        if "einspeis" in normalized or "feed in" in normalized or "export" in normalized:
            return ConsumptionMeterType.ELECTRICITY_FEED_IN
        if any(value in normalized for value in ("pv", "solar", "erzeugung")):
            return ConsumptionMeterType.ELECTRICITY_PV
        if any(value in normalized for value in ("strom", "electric", "netzbezug")):
            return ConsumptionMeterType.ELECTRICITY_GRID
        if "gas" in normalized:
            return ConsumptionMeterType.GAS
        if any(value in normalized for value in ("warme", "waerme", "heat")):
            return ConsumptionMeterType.HEAT
        if any(value in normalized for value in ("ol", "oel", "oil")):
            return ConsumptionMeterType.OIL
        return ConsumptionMeterType.OTHER

    @classmethod
    def _water_role_for_name(
        cls,
        name: str,
        meter_type: ConsumptionMeterType,
    ) -> ConsumptionWaterRole:
        if meter_type != ConsumptionMeterType.WATER:
            return ConsumptionWaterRole.NONE
        slug = cls._slug(name)
        if "haupt" in slug or "gesamt" in slug:
            return ConsumptionWaterRole.MAIN
        if slug in {"dusche", "kuche", "kueche", "zahlerraum", "zaehlerraum"}:
            return ConsumptionWaterRole.EG_COMPONENT
        return ConsumptionWaterRole.NONE

    @staticmethod
    def _default_unit(meter_type: ConsumptionMeterType) -> str:
        if meter_type in {
            ConsumptionMeterType.WATER,
            ConsumptionMeterType.GAS,
            ConsumptionMeterType.OIL,
        }:
            return "m³"
        if meter_type in {
            ConsumptionMeterType.ELECTRICITY_GRID,
            ConsumptionMeterType.ELECTRICITY_PV,
            ConsumptionMeterType.ELECTRICITY_FEED_IN,
            ConsumptionMeterType.HEAT,
        }:
            return "kWh"
        return "Einheit"

    @staticmethod
    def _legacy_note_scope(value: object) -> str:
        normalized = str(value or "month").casefold()
        return normalized if normalized in {"general", "month", "year"} else "month"

    @staticmethod
    def _decode_text(content: bytes) -> str:
        for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise ConsumptionImportError("Die Textkodierung der CSV-Datei ist unbekannt")

    @staticmethod
    def _first_field(mapping: dict[str, str], *names: str) -> str | None:
        return next((mapping[name] for name in names if name in mapping), None)

    @staticmethod
    def _parse_number(value: str) -> float:
        normalized = value.strip().replace(" ", "")
        if "," in normalized and "." in normalized:
            if normalized.rfind(",") > normalized.rfind("."):
                normalized = normalized.replace(".", "").replace(",", ".")
            else:
                normalized = normalized.replace(",", "")
        else:
            normalized = normalized.replace(",", ".")
        result = float(normalized)
        if result < 0:
            raise ValueError("negative values are not allowed")
        return result

    @classmethod
    def _parse_datetime(cls, value: object) -> datetime:
        if value is None or not str(value).strip():
            raise ConsumptionImportError("Datum oder Zeitpunkt fehlt")
        raw = str(value).strip()
        normalized = raw.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            parsed = None
            for pattern in (
                "%d.%m.%Y %H:%M:%S",
                "%d.%m.%Y %H:%M",
                "%d.%m.%Y",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
            ):
                try:
                    parsed = datetime.strptime(raw, pattern)
                    break
                except ValueError:
                    continue
            if parsed is None:
                raise ConsumptionImportError(f"Ungültiger Zeitpunkt: {raw}") from None
        return cls._as_utc(parsed)

    @staticmethod
    def _truthy(value: object) -> bool:
        return str(value or "").strip().casefold() in {"1", "true", "ja", "yes", "on", "x"}

    @staticmethod
    def _optional_text(value: object) -> str | None:
        normalized = str(value or "").strip()
        return normalized or None

    @staticmethod
    def _bounded_int(value: object, default: int, minimum: int, maximum: int) -> int:
        try:
            parsed = int(str(value))
        except (TypeError, ValueError):
            parsed = default
        return min(max(parsed, minimum), maximum)

    @staticmethod
    def _slug(value: str) -> str:
        normalized = unicodedata.normalize(
            "NFKD", (value or "").strip().casefold().replace("ß", "ss")
        )
        normalized = "".join(
            character for character in normalized if not unicodedata.combining(character)
        )
        return re.sub(r"[^a-z0-9]+", "", normalized)

    @staticmethod
    def _aware(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
