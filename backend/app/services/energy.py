from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.models.asset_engine import Asset
from app.models.energy import EnergyComponent, EnergyConfiguration
from app.repositories.energy import EnergyRepository
from app.schemas.consumption import ConsumptionMeterType
from app.schemas.energy import (
    EnergyBalancePeriodRead,
    EnergyBalanceRead,
    EnergyComponentRead,
    EnergyComponentType,
    EnergyComponentWrite,
    EnergyConfigurationRead,
    EnergyConfigurationWrite,
)
from app.services.consumption import ConsumptionService
from app.services.energy_math import calculate_energy_balance


class EnergyError(RuntimeError):
    pass


class EnergyNotFoundError(EnergyError):
    pass


class EnergyConflictError(EnergyError):
    pass


class EnergyValidationError(EnergyError):
    pass


class EnergyService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = EnergyRepository(session)
        self.consumption = ConsumptionService(session)

    def get_configuration(self) -> EnergyConfigurationRead:
        record = self.repository.configuration()
        if record is None:
            return EnergyConfigurationRead(
                grid_connection_name=None,
                grid_operator=None,
                energy_supplier=None,
                metering_point_id=None,
                connection_capacity_kw=None,
                grid_import_meter_id=None,
                pv_generation_meter_id=None,
                grid_export_meter_id=None,
                notes=None,
                grid_import_meter_name=None,
                pv_generation_meter_name=None,
                grid_export_meter_name=None,
                complete_for_balance=False,
                updated_at=datetime.now(UTC),
            )
        return self._configuration_read(record)

    def update_configuration(
        self, payload: EnergyConfigurationWrite
    ) -> EnergyConfigurationRead:
        self._validate_meter(
            payload.grid_import_meter_id, ConsumptionMeterType.ELECTRICITY_GRID
        )
        self._validate_meter(
            payload.pv_generation_meter_id, ConsumptionMeterType.ELECTRICITY_PV
        )
        self._validate_meter(
            payload.grid_export_meter_id, ConsumptionMeterType.ELECTRICITY_FEED_IN
        )
        record = self.repository.configuration()
        values = payload.model_dump()
        now = datetime.now(UTC)
        if record is None:
            record = EnergyConfiguration(id=1, **values, created_at=now, updated_at=now)
            self.session.add(record)
        else:
            record.sqlmodel_update(values)
            record.updated_at = now
        self._commit()
        return self._configuration_read(record)

    def list_components(self, *, include_archived: bool = False) -> list[EnergyComponentRead]:
        return [
            self._component_read(item)
            for item in self.repository.list_components(include_archived=include_archived)
        ]

    def create_component(self, payload: EnergyComponentWrite) -> EnergyComponentRead:
        self._validate_asset(payload.asset_id)
        record = EnergyComponent(**payload.model_dump())
        self.session.add(record)
        self._commit()
        return self._component_read(record)

    def update_component(
        self, component_id: UUID, payload: EnergyComponentWrite
    ) -> EnergyComponentRead:
        record = self.repository.component(component_id)
        if record is None:
            raise EnergyNotFoundError("Energiekomponente wurde nicht gefunden")
        self._validate_asset(payload.asset_id)
        record.sqlmodel_update(payload.model_dump())
        record.updated_at = datetime.now(UTC)
        self._commit()
        return self._component_read(record)

    def archive_component(self, component_id: UUID) -> None:
        record = self.repository.component(component_id)
        if record is None:
            raise EnergyNotFoundError("Energiekomponente wurde nicht gefunden")
        now = datetime.now(UTC)
        record.deleted_at = now
        record.updated_at = now
        self._commit()

    def balance(self, *, months: int = 12) -> EnergyBalanceRead:
        if months < 1 or months > 60:
            raise EnergyValidationError("Der Zeitraum muss zwischen 1 und 60 Monaten liegen")
        configuration = self.repository.configuration()
        complete = bool(
            configuration
            and configuration.grid_import_meter_id
            and configuration.pv_generation_meter_id
            and configuration.grid_export_meter_id
        )
        periods: list[EnergyBalancePeriodRead] = []
        for label, start, end in self.consumption._month_ranges(months):
            if not complete or configuration is None:
                periods.append(
                    EnergyBalancePeriodRead(
                        label=label,
                        period_start=start,
                        period_end=end,
                        grid_import_kwh=None,
                        pv_generation_kwh=None,
                        grid_export_kwh=None,
                        house_consumption_kwh=None,
                        self_consumption_kwh=None,
                        autonomy_percent=None,
                        self_consumption_rate_percent=None,
                        estimated=False,
                        incomplete=True,
                    )
                )
                continue
            grid_import_meter_id = configuration.grid_import_meter_id
            pv_generation_meter_id = configuration.pv_generation_meter_id
            grid_export_meter_id = configuration.grid_export_meter_id
            assert grid_import_meter_id is not None
            assert pv_generation_meter_id is not None
            assert grid_export_meter_id is not None
            grid_import = self.consumption._consumption_for_meter(
                grid_import_meter_id, start, end
            )
            pv_generation = self.consumption._consumption_for_meter(
                pv_generation_meter_id, start, end
            )
            grid_export = self.consumption._consumption_for_meter(
                grid_export_meter_id, start, end
            )
            values = (grid_import.value, pv_generation.value, grid_export.value)
            available = all(value is not None for value in values)
            house = self_consumption = autonomy = self_rate = None
            physically_inconsistent = False
            if available:
                imported = float(grid_import.value or 0)
                generated = float(pv_generation.value or 0)
                exported = float(grid_export.value or 0)
                calculated = calculate_energy_balance(imported, generated, exported)
                physically_inconsistent = calculated.physically_inconsistent
                house = calculated.house_consumption_kwh
                self_consumption = calculated.self_consumption_kwh
                autonomy = calculated.autonomy_percent
                self_rate = calculated.self_consumption_rate_percent
            periods.append(
                EnergyBalancePeriodRead(
                    label=label,
                    period_start=start,
                    period_end=end,
                    grid_import_kwh=grid_import.value,
                    pv_generation_kwh=pv_generation.value,
                    grid_export_kwh=grid_export.value,
                    house_consumption_kwh=house,
                    self_consumption_kwh=self_consumption,
                    autonomy_percent=autonomy,
                    self_consumption_rate_percent=self_rate,
                    estimated=(
                        grid_import.estimated
                        or pv_generation.estimated
                        or grid_export.estimated
                    ),
                    incomplete=(
                        not available
                        or grid_import.incomplete
                        or pv_generation.incomplete
                        or grid_export.incomplete
                        or physically_inconsistent
                    ),
                )
            )
        return EnergyBalanceRead(
            months=months,
            configuration_complete=complete,
            periods=periods,
        )

    def _validate_meter(self, meter_id: UUID | None, expected: ConsumptionMeterType) -> None:
        if meter_id is None:
            return
        meter = self.consumption.repository.get_meter(meter_id)
        if meter is None:
            raise EnergyValidationError("Der ausgewählte Energiezähler wurde nicht gefunden")
        if meter.meter_type != expected.value:
            raise EnergyValidationError(
                f"Der Zähler „{meter.name}“ hat nicht die erwartete Art {expected.value}"
            )
        if meter.unit.casefold() != "kwh":
            raise EnergyValidationError(
                "Energiezähler für die Bilanz müssen die Einheit kWh verwenden"
            )

    def _validate_asset(self, asset_id: UUID | None) -> None:
        if asset_id is None:
            return
        asset = self.session.get(Asset, asset_id)
        if asset is None or asset.deleted_at is not None:
            raise EnergyValidationError(
                "Das zugeordnete Asset wurde nicht gefunden oder ist archiviert"
            )

    def _configuration_read(self, record: EnergyConfiguration) -> EnergyConfigurationRead:
        grid = (
            self.consumption.repository.get_meter(
                record.grid_import_meter_id, include_archived=True
            )
            if record.grid_import_meter_id
            else None
        )
        pv = (
            self.consumption.repository.get_meter(
                record.pv_generation_meter_id, include_archived=True
            )
            if record.pv_generation_meter_id
            else None
        )
        export = (
            self.consumption.repository.get_meter(
                record.grid_export_meter_id, include_archived=True
            )
            if record.grid_export_meter_id
            else None
        )
        return EnergyConfigurationRead(
            grid_connection_name=record.grid_connection_name,
            grid_operator=record.grid_operator,
            energy_supplier=record.energy_supplier,
            metering_point_id=record.metering_point_id,
            connection_capacity_kw=record.connection_capacity_kw,
            grid_import_meter_id=record.grid_import_meter_id,
            pv_generation_meter_id=record.pv_generation_meter_id,
            grid_export_meter_id=record.grid_export_meter_id,
            notes=record.notes,
            grid_import_meter_name=grid.name if grid else None,
            pv_generation_meter_name=pv.name if pv else None,
            grid_export_meter_name=export.name if export else None,
            complete_for_balance=bool(grid and pv and export),
            updated_at=self._aware(record.updated_at),
        )

    def _component_read(self, record: EnergyComponent) -> EnergyComponentRead:
        asset = self.session.get(Asset, record.asset_id) if record.asset_id else None
        return EnergyComponentRead(
            id=record.id,
            component_type=EnergyComponentType(record.component_type),
            name=record.name,
            asset_id=record.asset_id,
            asset_name=asset.name if asset else None,
            manufacturer=record.manufacturer,
            model=record.model,
            serial_number=record.serial_number,
            rated_power_kw=record.rated_power_kw,
            capacity_kwh=record.capacity_kwh,
            sort_order=record.sort_order,
            notes=record.notes,
            archived=record.deleted_at is not None,
            created_at=self._aware(record.created_at),
            updated_at=self._aware(record.updated_at),
        )

    @staticmethod
    def _aware(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise EnergyConflictError(
                "Eine aktive Energiekomponente mit diesem Namen und Typ existiert bereits"
            ) from exc
