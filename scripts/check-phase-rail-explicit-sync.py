"""Dependency-free phase-pattern regression for generic DIN devices and 4P FI."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.electrical_phase_rail import (  # noqa: E402
    phase_rail_device_phases,
    phase_rail_din_asset_phases,
)


def values(phases):
    return [phase.value for phase in phases]


def main() -> int:
    generic = [
        phase_rail_din_asset_phases(
            rail_start=1,
            rail_width=10,
            phase_l1=True,
            phase_l2=True,
            phase_l3=True,
            start_phase="L1",
            asset_start=position,
            asset_width=1,
        )
        for position in (1, 2, 3, 4)
    ]
    assert [values(item) for item in generic] == [["L1"], ["L2"], ["L3"], ["L1"]]

    four_pole_rcd = phase_rail_device_phases(
        rail_start=1,
        rail_width=4,
        phase_l1=True,
        phase_l2=True,
        phase_l3=True,
        start_phase="L1",
        device_start=1,
        device_width=4,
        device_type="rcd",
        poles=4,
    )
    assert values(four_pole_rcd) == ["L1", "L2", "L3"]
    assert "N" not in values(four_pole_rcd)

    print("Phasenmuster: DIN-Assets und vierpoliger FI korrekt berechnet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
