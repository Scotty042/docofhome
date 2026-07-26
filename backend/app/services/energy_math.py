from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EnergyBalanceValues:
    house_consumption_kwh: float
    self_consumption_kwh: float
    autonomy_percent: float | None
    self_consumption_rate_percent: float | None
    physically_inconsistent: bool


def calculate_energy_balance(
    grid_import_kwh: float,
    pv_generation_kwh: float,
    grid_export_kwh: float,
) -> EnergyBalanceValues:
    raw_house = grid_import_kwh + pv_generation_kwh - grid_export_kwh
    raw_self_consumption = pv_generation_kwh - grid_export_kwh
    physically_inconsistent = raw_house < -0.001 or raw_self_consumption < -0.001
    house_consumption = max(raw_house, 0.0)
    self_consumption = max(raw_self_consumption, 0.0)
    autonomy = (
        self_consumption / house_consumption * 100
        if house_consumption > 0
        else None
    )
    self_consumption_rate = (
        self_consumption / pv_generation_kwh * 100
        if pv_generation_kwh > 0
        else None
    )
    return EnergyBalanceValues(
        house_consumption_kwh=house_consumption,
        self_consumption_kwh=self_consumption,
        autonomy_percent=autonomy,
        self_consumption_rate_percent=self_consumption_rate,
        physically_inconsistent=physically_inconsistent,
    )
