"""Verify release and electrical-integrity contracts for DocOfHome 1.6.3.4."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(relative: str, fragments: tuple[str, ...]) -> None:
    source = read(relative)
    missing = [fragment for fragment in fragments if fragment not in source]
    if missing:
        raise AssertionError(f"{relative}: fehlt: {', '.join(missing)}")


def require_absent(relative: str, fragments: tuple[str, ...]) -> None:
    source = read(relative)
    present = [fragment for fragment in fragments if fragment in source]
    if present:
        raise AssertionError(f"{relative}: unerwünschte Altlogik: {', '.join(present)}")


def main() -> int:
    if read("VERSION").strip() != "1.6.3.4":
        raise AssertionError("VERSION ist nicht 1.6.3.4")
    require("backend/pyproject.toml", ('version = "1.6.3.4"',))

    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    if package["version"] != "1.6.3.4":
        raise AssertionError("frontend/package.json ist nicht 1.6.3.4")
    if lock["version"] != "1.6.3.4" or lock["packages"][""]["version"] != "1.6.3.4":
        raise AssertionError("Eigene package-lock-Metadaten sind nicht 1.6.3.4")

    source_info = json.loads(read("SOURCE_INFO.json"))
    expected = {
        "version": "1.6.3.4",
        "base_version": "1.6.3",
        "release_notes": "RELEASE_NOTES_1.6.3.4.md",
        "alembic_head": "0044",
    }
    for key, value in expected.items():
        if source_info.get(key) != value:
            raise AssertionError(f"SOURCE_INFO.json: {key} ist nicht {value}")

    require(
        "backend/app/electrical_phase_rail.py",
        (
            "def phase_pattern(",
            "def rail_fully_covers_device(",
            "def active_line_pole_count(",
            "def phase_rail_device_phases(",
        ),
    )
    require(
        "backend/app/services/electrical_placement.py",
        (
            "def validate_protective_device_placement(",
            "Eine Phasen-/Kammschiene darf ein Schutzgerät nicht nur teilweise",
            "Ein Schutzgerät darf nur von einer Phasen-/Kammschiene versorgt werden",
        ),
    )
    require(
        "backend/app/services/phase_rail_connections.py",
        (
            "class PhaseRailConnectionService",
            "Protective device -> phase rail is a legitimate upstream supply",
            "source.component_type == \"phase_rail\"",
            "_synchronize_device_outputs",
            "_synchronize_measurement_phase",
            "_verify_distribution_connections",
            "sync_rail_with_visible_devices",
            "visible_device_ids",
            "direct-table fallback",
            "effective_asset_module_width",
            "_device_module_width",
            "Phase-rail synchronization",
            "deleted_at=now",
        ),
    )
    require(
        "backend/app/services/electrical_topology.py",
        (
            "phase_locked=bool(locked_line_phases)",
            "locked_line_phases=locked_line_phases",
            "_circuit_incoming_phase_sets",
            "Ausgänge einer Phasen-/Kammschiene zu Schutzgeräten werden",
            "kann nicht manuell bearbeitet werden",
            "_append_cabinet_supply_warnings",
        ),
    )
    require(
        "backend/app/services/smart_meter.py",
        (
            "_validate_measurement_phase",
            "liegt auf der ausgewählten Verbindung nicht an",
            "if selected is None and len(line_phases) == 1",
        ),
    )
    require(
        "backend/app/services/electrical_circuit.py",
        (
            'not in {"fuse", "mcb", "rcbo"}',
            "Der Stromkreis ist noch in der Versorgungstopologie verkabelt",
        ),
    )
    require(
        "backend/app/services/asset_engine.py",
        (
            "_validate_topology_lifecycle",
            "_require_no_electrical_connections",
        ),
    )
    require(
        "backend/app/distribution_layout.py",
        (
            "Die N-Schiene ist noch Schutzgeräten zugeordnet",
            "PhaseRailConnectionService(self.session).sync_distribution",
            "automatic_connection_count=automatic_connection_count",
            "verify=False",
        ),
    )
    require(
        "backend/app/schemas/electrical_layout.py",
        ("automatic_connection_count: int", "visible_protective_device_ids: list[UUID]"),
    )
    require(
        "backend/app/services/electrical.py",
        (
            "Felder und Bereiche archiviert werden",
            "Das Schutzgerät ist noch manuell verkabelt",
        ),
    )
    require(
        "frontend/src/pages/ElectricalTopologyPage.vue",
        (
            "Fest vorgegebene Außenleiterphase",
            "v-if=\"!automaticEditingConnection\"",
            "endpoint.kind === 'protective_device' || endpoint.kind === 'circuit'",
        ),
    )
    require(
        "frontend/src/pages/ElectricalDistributionLayoutPage.vue",
        (
            "Phasenschiene / Kammschiene (Sicherungsreihe)",
            "Zugehöriger FI/RCD (optional)",
            "verbindet automatisch alle bereits vorhandenen und später platzierten",
            "Automatische Kontakte",
            "automatic_connection_count",
            "visible_protective_device_ids: visibleProtectiveDeviceIds()",
        ),
    )
    require_absent(
        "frontend/src/pages/ElectricalDistributionLayoutPage.vue",
        ("noch keinem FI/RCD zugeordnet",),
    )
    require(
        "frontend/src/pages/phaseRailAutoWiring.test.ts",
        ("ElectricalDistributionLayoutPage.vue?raw",),
    )
    require_absent(
        "frontend/src/pages/phaseRailAutoWiring.test.ts",
        ("node:fs", "readFileSync"),
    )
    require(
        "backend/migrations/versions/0043_release_1_6_3_electrical_integrity.py",
        (
            'revision: str = "0043"',
            'down_revision: str | None = "0042"',
            "_normalize_components",
            "_repair_derived_connections",
            "smart_meter_measurement_points",
            "ck_electrical_cabinet_components_phase_rail_conductors",
            "ck_electrical_cabinet_components_phase_metadata",
            "ck_electrical_cabinet_components_rcd_link_type",
            "_repair_circuit_outputs",
        ),
    )
    require(
        "scripts/check-phase-rail-runtime-sync.py",
        (
            "Kammschiene erzeugt verifizierte Kontakte nach dem Speichern",
            "sync_component(record, verify=False)",
        ),
    )
    require(
        "scripts/check-phase-rail-explicit-sync.py",
        (
            "uq_legacy_active_target",
            "phase_rail_device_phases",
            "UPDATE smart_meter_measurement_points",
            "UPDATE electrical_connections SET deleted_at=NULL",
        ),
    )
    require(
        "backend/migrations/versions/0044_reconcile_phase_rail_contacts.py",
        (
            'revision: str = "0044"',
            'down_revision: str | None = "0043"',
            "_repair_derived_connections(op.get_bind())",
        ),
    )
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    if not migrations[-1].name.startswith("0044_"):
        raise AssertionError("Alembic-Head muss bei 0044 liegen")
    require(
        "frontend/src/services/electricalTopology.ts",
        ("L1: 'brown'", "L2: 'black'", "L3: 'grey'"),
    )
    require("README.md", ("DocOfHome 1.6.3.4", "Update von 1.6.3.3 auf 1.6.3.4"))
    require("RELEASE_NOTES_1.6.3.4.md", ("geerbte DIN-Breiten", "effective_asset_module_width", "0044"))
    require("frontend/src/pages/ElectricalDistributionLayoutPage.vue", ("synchronizePhaseRailContacts", "protective_devices ?? []).map((device) => device.id"))
    require("frontend/src/services/electricalApi.ts", ("/synchronize", "protective_device_ids"))
    require("backend/app/api/v1/electrical_layout.py", ("synchronize_phase_rail_contacts", "PhaseRailSynchronizationWrite"))
    require("backend/app/services/phase_rail_connections.py", ("_explicit_device_candidate", "Keines der von der Verteilerschrankansicht gemeldeten Schutzgeräte"))
    print("Release 1.6.3.4: Versions-, Elektro-, Migrations- und Paketverträge vorhanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
