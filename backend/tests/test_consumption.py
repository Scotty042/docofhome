from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401
from app.schemas.consumption import (
    ConsumptionMeterType,
    ConsumptionMeterWrite,
    ConsumptionReadingWrite,
    ConsumptionWaterRole,
)
from app.services.consumption import ConsumptionConflictError, ConsumptionService


@pytest.fixture
def consumption_session(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'consumption.sqlite3'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def meter_payload(name: str, role: ConsumptionWaterRole) -> ConsumptionMeterWrite:
    return ConsumptionMeterWrite(
        name=name,
        meter_type=ConsumptionMeterType.WATER,
        unit="m³",
        decimals=3,
        water_role=role,
    )


def reading(meter_id, measured_at: datetime, value: float) -> ConsumptionReadingWrite:
    return ConsumptionReadingWrite(meter_id=meter_id, measured_at=measured_at, value=value)


def test_virtual_water_groups_use_marked_eg_components(consumption_session: Session) -> None:
    service = ConsumptionService(consumption_session)
    main = service.create_meter(meter_payload("Hauptwasser", ConsumptionWaterRole.MAIN))
    shower = service.create_meter(meter_payload("Dusche", ConsumptionWaterRole.EG_COMPONENT))
    kitchen = service.create_meter(meter_payload("Küche", ConsumptionWaterRole.EG_COMPONENT))
    meter_room = service.create_meter(
        meter_payload("Zählerraum", ConsumptionWaterRole.EG_COMPONENT)
    )
    heating = service.create_meter(meter_payload("Heizraum", ConsumptionWaterRole.NONE))

    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 7, 1, tzinfo=UTC)
    values = {
        main.id: (100.0, 130.0),
        shower.id: (10.0, 14.0),
        kitchen.id: (20.0, 23.0),
        meter_room.id: (5.0, 7.0),
        heating.id: (8.0, 18.0),
    }
    for meter_id, (first, last) in values.items():
        service.create_reading(reading(meter_id, start, first))
        service.create_reading(reading(meter_id, end, last))

    virtual = service._virtual_water(service.repository.list_meters(), start, end)
    assert virtual["water_eg"].value == pytest.approx(9.0)
    assert virtual["water_rest"].value == pytest.approx(21.0)


def test_duplicate_reading_is_rejected(consumption_session: Session) -> None:
    service = ConsumptionService(consumption_session)
    meter = service.create_meter(meter_payload("Wasser", ConsumptionWaterRole.NONE))
    measured_at = datetime(2026, 7, 1, tzinfo=UTC)
    service.create_reading(reading(meter.id, measured_at, 12.5))
    with pytest.raises(ConsumptionConflictError):
        service.create_reading(reading(meter.id, measured_at, 12.6))


def test_default_seed_keeps_heating_room_outside_eg(consumption_session: Session) -> None:
    result = ConsumptionService(consumption_session).seed_defaults()
    roles = {meter.name: meter.water_role for meter in result.meters}
    assert roles["Dusche"] == ConsumptionWaterRole.EG_COMPONENT
    assert roles["Küche"] == ConsumptionWaterRole.EG_COMPONENT
    assert roles["Zählerraum"] == ConsumptionWaterRole.EG_COMPONENT
    assert roles["Heizraum"] == ConsumptionWaterRole.NONE


def test_meter_keeps_asset_location_and_live_entity_assignments(
    consumption_session: Session,
) -> None:
    from app.models.asset_engine import Asset, AssetType, Location

    asset_type = AssetType(name="Zähler", code_prefix="MET")
    building = Location(name="Home", location_type="building")
    consumption_session.add(asset_type)
    consumption_session.add(building)
    consumption_session.flush()
    location = Location(
        name="Meter cabinet",
        location_type="cabinet",
        parent_id=building.id,
    )
    consumption_session.add(location)
    consumption_session.flush()
    linked_asset = Asset(
        name="Shelly 3EM",
        jarvis_code="MET-0001",
        asset_type_id=asset_type.id,
        location_id=location.id,
    )
    consumption_session.add(linked_asset)
    consumption_session.commit()

    meter = ConsumptionService(consumption_session).create_meter(
        ConsumptionMeterWrite(
            name="Grid consumption",
            meter_type=ConsumptionMeterType.ELECTRICITY_GRID,
            unit="kWh",
            decimals=1,
            asset_id=linked_asset.id,
            location_id=None,
            home_assistant_entity_id="sensor.grid_energy",
            home_assistant_power_entity_id="sensor.grid_power",
            home_assistant_voltage_entity_id="sensor.grid_voltage",
        )
    )

    assert meter.asset_id == linked_asset.id
    assert meter.asset_name == "Shelly 3EM"
    assert meter.location_id == location.id
    assert meter.location_path == "Home / Meter cabinet"
    assert meter.home_assistant_power_entity_id == "sensor.grid_power"
    assert meter.home_assistant_voltage_entity_id == "sensor.grid_voltage"


def test_current_month_is_complete_after_a_reading_today(
    consumption_session: Session,
) -> None:
    from datetime import timedelta

    service = ConsumptionService(consumption_session)
    meter = service.create_meter(
        meter_payload("Tagesaktueller Wasserzähler", ConsumptionWaterRole.NONE)
    )
    start, end = service._current_month_range()
    latest = end - timedelta(minutes=1)
    if latest.astimezone(service._timezone()).date() != end.astimezone(
        service._timezone()
    ).date():
        latest = end - timedelta(seconds=1)

    service.create_reading(reading(meter.id, start, 100.0))
    service.create_reading(reading(meter.id, latest, 112.0))

    result = service._consumption_for_meter(meter.id, start, end)
    assert result.value == pytest.approx(12.0)
    assert result.incomplete is False
    assert end < service._add_months(start.astimezone(service._timezone()), 1).astimezone(UTC)
