#!/usr/bin/env python3
"""Dependency-light electrical integrity contracts for DocOfHome 1.6.3."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from pydantic import ValidationError

from app.electrical_phase_rail import (
    active_line_pole_count,
    phase_pattern,
    phase_rail_device_phases,
    rail_fully_covers_device,
    spans_overlap,
)
from app.schemas.electrical_layout import ElectricalCabinetComponentWrite
from app.schemas.electrical_topology import ElectricalPhase


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def expect_text(relative: str, *needles: str) -> None:
    text = source(relative)
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{relative}: fehlende Verträge: {missing}")


def expect_absent(relative: str, *needles: str) -> None:
    text = source(relative)
    present = [needle for needle in needles if needle in text]
    if present:
        raise AssertionError(f"{relative}: unerwünschte Altlogik: {present}")


def validate_phase_math() -> None:
    assert phase_pattern(
        phase_l1=True, phase_l2=True, phase_l3=True, start_phase="L1"
    ) == (ElectricalPhase.L1, ElectricalPhase.L2, ElectricalPhase.L3)
    assert phase_pattern(
        phase_l1=True, phase_l2=True, phase_l3=True, start_phase="L2"
    ) == (ElectricalPhase.L2, ElectricalPhase.L3, ElectricalPhase.L1)
    assert phase_pattern(
        phase_l1=True, phase_l2=False, phase_l3=True, start_phase="L3"
    ) == (ElectricalPhase.L3, ElectricalPhase.L1)
    assert rail_fully_covers_device(
        rail_start=1, rail_width=12, device_start=12, device_width=1
    )
    assert not rail_fully_covers_device(
        rail_start=1, rail_width=4, device_start=4, device_width=2
    )
    assert spans_overlap(1, 4, 4, 2)
    assert not spans_overlap(1, 3, 4, 1)
    assert active_line_pole_count("rcd", 4) == 3
    assert active_line_pole_count("rcbo", 2) == 1
    assert active_line_pole_count("mcb", 3) == 3
    assert phase_rail_device_phases(
        rail_start=1,
        rail_width=12,
        phase_l1=True,
        phase_l2=True,
        phase_l3=True,
        start_phase="L1",
        device_start=2,
        device_width=1,
        device_type="mcb",
        poles=1,
    ) == (ElectricalPhase.L2,)


def validate_component_contracts() -> None:
    base = dict(
        name="Test",
        area_id=None,
        row_number=1,
        start_position=1,
        module_width=4,
        rated_current_a=None,
        max_cross_section_mm2=None,
        outgoing_connections=None,
        linked_rcd_device_id=None,
        description=None,
        notes=None,
    )
    rail = ElectricalCabinetComponentWrite(
        **base,
        component_type="phase_rail",
        phases=["L1", "L2", "L3"],
        start_phase="L2",
        mounting_side="below",
    )
    assert rail.phases == [ElectricalPhase.L1, ElectricalPhase.L2, ElectricalPhase.L3]
    for phases in (["L1", "N"], ["PE"], []):
        try:
            ElectricalCabinetComponentWrite(
                **base,
                component_type="phase_rail",
                phases=phases,
                start_phase="L1",
                mounting_side="below",
            )
        except ValidationError:
            pass
        else:
            raise AssertionError(f"Ungültige Phasenschiene akzeptiert: {phases}")
    assert ElectricalCabinetComponentWrite(
        **base,
        component_type="neutral_rail",
        phases=["N"],
        start_phase=None,
        mounting_side=None,
    ).phases == [ElectricalPhase.N]
    assert ElectricalCabinetComponentWrite(
        **base,
        component_type="protective_earth_rail",
        phases=["PE"],
        start_phase=None,
        mounting_side=None,
    ).phases == [ElectricalPhase.PE]


def validate_source_contracts() -> None:
    expect_text(
        "backend/app/services/electrical.py",
        "validate_protective_device_placement(",
        "Das Schutzgerät ist noch manuell verkabelt",
        "payload.device_type.value not in {\"fuse\", \"mcb\", \"rcbo\"}",
        "Felder und Bereiche archiviert werden",
    )
    expect_text(
        "backend/app/distribution_layout.py",
        "PhaseRailConnectionService(self.session).sync_distribution",
        "Eine Phasen-/Kammschiene darf ein Schutzgerät nicht nur ",
        "Die N-Schiene ist noch Schutzgeräten zugeordnet",
    )
    expect_text(
        "backend/app/services/phase_rail_connections.py",
        "source.component_type == \"phase_rail\"",
        "previous_component_type",
        "class PhaseRailContact",
        "_synchronize_endpoint_outputs",
        "_synchronize_measurement_phase",
        "self.session.flush()",
        "archive_component_connections",
    )
    expect_text(
        "backend/app/services/electrical_topology.py",
        "Ausgänge einer Phasen-/Kammschiene",
        "_circuit_incoming_phase_sets",
        "locked_line_phases",
        "_append_cabinet_supply_warnings",
        "kann nicht manuell bearbeitet werden",
        "_reconcile_phase_rail_connections",
        "Automatische Phasenschienen-Verbindungen konnten nicht abgeglichen werden",
    )
    expect_text(
        "backend/app/services/smart_meter.py",
        "_validate_measurement_phase",
        "liegt auf der ausgewählten Verbindung nicht an",
    )
    expect_text(
        "backend/app/services/asset_engine.py",
        "_validate_topology_lifecycle",
        "_require_no_electrical_connections",
    )
    expect_text(
        "frontend/src/pages/ElectricalTopologyPage.vue",
        "['protective_device', 'asset', 'circuit'].includes(endpoint.kind)",
        "Fest vorgegebene Außenleiterphase",
        "v-if=\"!automaticEditingConnection\"",
    )
    expect_text(
        "frontend/src/pages/ElectricalDistributionLayoutPage.vue",
        "Phasenschiene / Kammschiene (Sicherungsreihe)",
        "Zugehöriger FI/RCD (optional)",
        "verbindet automatisch jedes vollständig überdeckte DIN-Gerät",
        "archiveDetailDevice",
        "archiveDetailComponent",
        "vierpoligen FI",
        "der vierte Pol bleibt für N frei",
        "max-width=\"720\" scrollable",
    )
    expect_text(
        "backend/app/models/electrical.py",
        "ck_electrical_cabinet_components_phase_metadata",
        "ck_electrical_cabinet_components_rcd_link_type",
    )
    expect_text(
        "backend/migrations/versions/0043_release_1_6_3_electrical_integrity.py",
        "_repair_circuit_outputs",
        "SET start_phase=NULL, mounting_side=NULL",
    )
    expect_text(
        "frontend/src/services/electricalTopology.ts",
        "L1: 'brown'",
        "L2: 'black'",
        "L3: 'grey'",
    )
    expect_absent(
        "frontend/src/pages/ElectricalDistributionLayoutPage.vue",
        "noch keinem FI/RCD zugeordnet",
    )


def main() -> int:
    validate_phase_math()
    validate_component_contracts()
    validate_source_contracts()
    print("Elektro-Integritätsverträge 1.6.3: erfolgreich geprüft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
