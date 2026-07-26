import pytest

from app.services.energy_math import calculate_energy_balance


def test_energy_balance_formulas() -> None:
    result = calculate_energy_balance(
        grid_import_kwh=200,
        pv_generation_kwh=500,
        grid_export_kwh=300,
    )

    assert result.house_consumption_kwh == pytest.approx(400)
    assert result.self_consumption_kwh == pytest.approx(200)
    assert result.autonomy_percent == pytest.approx(50)
    assert result.self_consumption_rate_percent == pytest.approx(40)
    assert result.physically_inconsistent is False


def test_energy_balance_marks_physical_inconsistency() -> None:
    result = calculate_energy_balance(
        grid_import_kwh=100,
        pv_generation_kwh=500,
        grid_export_kwh=600,
    )

    assert result.house_consumption_kwh == pytest.approx(0)
    assert result.self_consumption_kwh == pytest.approx(0)
    assert result.physically_inconsistent is True
