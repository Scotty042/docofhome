from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401
from app.schemas.consumption import (
    ConsumptionMeterType,
    ConsumptionMeterWrite,
    ConsumptionReadingWrite,
)
from app.schemas.energy import (
    EnergyComponentType,
    EnergyComponentWrite,
    EnergyConfigurationWrite,
)
from app.services.consumption import ConsumptionService
from app.services.energy import EnergyService


@pytest.fixture
def energy_session(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'energy.sqlite3'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def meter(name: str, meter_type: ConsumptionMeterType, *, primary: bool = False):
    return ConsumptionMeterWrite(
        name=name,
        meter_type=meter_type,
        unit="kWh" if meter_type != ConsumptionMeterType.GAS else "m³",
        decimals=1,
        primary_for_dashboard=primary,
    )


def test_energy_balance_uses_grid_pv_and_export_meters(energy_session: Session) -> None:
    consumption = ConsumptionService(energy_session)
    grid = consumption.create_meter(meter("Netzbezug", ConsumptionMeterType.ELECTRICITY_GRID))
    pv = consumption.create_meter(meter("PV Erzeugung", ConsumptionMeterType.ELECTRICITY_PV))
    export = consumption.create_meter(
        meter("Netzeinspeisung", ConsumptionMeterType.ELECTRICITY_FEED_IN)
    )
    start = datetime(2026, 7, 1, tzinfo=UTC)
    end = datetime(2026, 8, 1, tzinfo=UTC)
    for meter_id, first, last in (
        (grid.id, 100.0, 130.0),
        (pv.id, 200.0, 250.0),
        (export.id, 20.0, 35.0),
    ):
        consumption.create_reading(
            ConsumptionReadingWrite(meter_id=meter_id, measured_at=start, value=first)
        )
        consumption.create_reading(
            ConsumptionReadingWrite(meter_id=meter_id, measured_at=end, value=last)
        )

    service = EnergyService(energy_session)
    configuration = service.update_configuration(
        EnergyConfigurationWrite(
            grid_connection_name="Hausanschluss",
            grid_operator="Netz GmbH",
            energy_supplier="Energie GmbH",
            grid_import_meter_id=grid.id,
            pv_generation_meter_id=pv.id,
            grid_export_meter_id=export.id,
        )
    )
    assert configuration.complete_for_balance is True
    service.consumption._month_ranges = (  # type: ignore[method-assign]
        lambda months: [("Jul 2026", start, end)]
    )
    period = service.balance(months=1).periods[0]
    assert period.grid_import_kwh == pytest.approx(30.0)
    assert period.pv_generation_kwh == pytest.approx(50.0)
    assert period.grid_export_kwh == pytest.approx(15.0)
    assert period.house_consumption_kwh == pytest.approx(65.0)
    assert period.self_consumption_kwh == pytest.approx(35.0)
    assert period.autonomy_percent == pytest.approx(53.846, rel=1e-3)
    assert period.self_consumption_rate_percent == pytest.approx(70.0)
    assert period.incomplete is False


def test_multiple_energy_components_are_supported(energy_session: Session) -> None:
    service = EnergyService(energy_session)
    first = service.create_component(
        EnergyComponentWrite(
            component_type=EnergyComponentType.PV_SOURCE,
            name="Süddach",
            rated_power_kw=8.5,
        )
    )
    second = service.create_component(
        EnergyComponentWrite(
            component_type=EnergyComponentType.PV_SOURCE,
            name="Garage",
            rated_power_kw=2.1,
        )
    )
    inverter = service.create_component(
        EnergyComponentWrite(
            component_type=EnergyComponentType.INVERTER,
            name="Wechselrichter 1",
            rated_power_kw=10.0,
        )
    )
    storage = service.create_component(
        EnergyComponentWrite(
            component_type=EnergyComponentType.STORAGE,
            name="Hausspeicher",
            capacity_kwh=15.0,
        )
    )
    assert {item.id for item in service.list_components()} == {
        first.id,
        second.id,
        inverter.id,
        storage.id,
    }


def test_primary_dashboard_assignment_transfers_and_falls_back(energy_session: Session) -> None:
    service = ConsumptionService(energy_session)
    first = service.create_meter(
        meter("Stromzähler alt", ConsumptionMeterType.ELECTRICITY_GRID, primary=True)
    )
    second = service.create_meter(
        meter("Stromzähler neu", ConsumptionMeterType.ELECTRICITY_GRID, primary=True)
    )
    refreshed_first = service.get_meter(first.id)
    assert refreshed_first.primary_for_dashboard is False
    assert service.get_meter(second.id).primary_for_dashboard is True

    updated = meter("Stromzähler neu", ConsumptionMeterType.ELECTRICITY_GRID, primary=False)
    service.update_meter(second.id, updated)
    gas_first = service.create_meter(
        meter("Gaszähler A", ConsumptionMeterType.GAS, primary=False)
    )
    gas_primary = service.create_meter(
        meter("Gaszähler B", ConsumptionMeterType.GAS, primary=True)
    )

    comparisons = {item.medium: item for item in service.dashboard_comparisons()}
    assert comparisons["electricity"].meter_id == first.id
    assert comparisons["gas"].meter_id == gas_primary.id

    service.update_meter(
        gas_primary.id,
        meter("Gaszähler B", ConsumptionMeterType.GAS, primary=False),
    )
    comparisons = {item.medium: item for item in service.dashboard_comparisons()}
    assert comparisons["gas"].meter_id == gas_first.id
