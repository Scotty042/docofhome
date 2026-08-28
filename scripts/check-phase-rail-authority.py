"""Dependency-free contracts for authoritative phase-rail assignment."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def phase_at(start_phase: str, position: int, rail_start: int = 1) -> str:
    standard = ["L1", "L2", "L3"]
    index = standard.index(start_phase)
    pattern = standard[index:] + standard[:index]
    return pattern[(position - rail_start) % len(pattern)]


def main() -> int:
    assert [phase_at("L1", position) for position in (1, 2, 3, 4)] == [
        "L1", "L2", "L3", "L1"
    ]
    assert [phase_at("L2", position) for position in (1, 2, 3, 4)] == [
        "L2", "L3", "L1", "L2"
    ]

    repository = read("backend/app/repositories/electrical_topology.py")
    service = read("backend/app/services/electrical.py")
    topology_service = read("backend/app/services/electrical_topology.py")
    schema = read("backend/app/schemas/electrical_layout.py")
    topology_page = read("frontend/src/pages/ElectricalTopologyPage.vue")
    layout_page = read("frontend/src/pages/ElectricalDistributionLayoutPage.vue")

    assert 'component.component_type == "phase_rail"' in repository
    assert 'component.component_type != "phase_rail"' in service
    assert "self.component_type == ElectricalCabinetComponentType.PHASE_RAIL" in schema
    assert "return connection.effective_phases" in topology_page
    assert "directPhaseRailConnection" in topology_page
    assert "Fest vorgegebene Außenleiterphase" in topology_page
    assert 'label="Zusätzliche Leiter"' in topology_page
    assert "_phase_rail_phases_for_device" in topology_service
    assert "Sammelschiene (allgemeiner Verteiler)" in layout_page
    assert "Phasenschiene / Kammschiene (Sicherungsreihe)" in layout_page
    assert "every active phase rail is matched against its" in topology_service
    auto_service = read("backend/app/services/phase_rail_connections.py")
    assert "class PhaseRailConnectionService" in auto_service
    assert "sync_distribution" in auto_service
    assert "sync_rail" in auto_service
    assert 'connection_type="busbar"' in auto_service
    assert "Zugehöriger FI/RCD (optional)" in layout_page
    assert "verbindet automatisch jedes vollständig überdeckte DIN-Gerät" in layout_page

    print("Phasenschienenlogik: Typtrennung, TE-Muster und wirksame Phase geprüft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
