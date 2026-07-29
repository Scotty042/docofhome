"""Verify DocOfHome 1.7.4.6 circuit-branch visibility contracts."""
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


def reject(relative: str, fragments: tuple[str, ...]) -> None:
    source = read(relative)
    present = [fragment for fragment in fragments if fragment in source]
    if present:
        raise AssertionError(f"{relative}: unerwünscht: {', '.join(present)}")


def main() -> int:
    version = "1.7.4.6"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    source = json.loads(read("SOURCE_INFO.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    assert source["version"] == version
    assert source["base_version"] == "1.7.4.5"
    assert source["release_notes"] == "RELEASE_NOTES_1.7.4.6.md"
    assert source["alembic_head"] == "0049"

    require("frontend/src/components/CabinetWiringOverlay.vue", (
        "function isIndividualCircuitBranch(",
        "connection.source.kind === 'circuit'",
        "connection.target.kind === 'circuit'",
        "Eine manuelle Einspeisung zu einem LS/MCB/RCBO",
        "if (isIndividualCircuitBranch(connection)) continue",
        "function isAutomaticBusbarContact(",
        "flowThrough",
        "label: 'IN'",
        "label: 'OUT'",
    ))
    reject("frontend/src/components/CabinetWiringOverlay.vue", (
        "function individualCircuitEndpointKeys(",
        "new Set(['mcb', 'rcbo'])",
        "hiddenCircuitEndpoints.has(connection.source.key)",
    ))
    require("frontend/src/components/CabinetWiringOverlay.test.ts", (
        "omits only the branch to an individual circuit while keeping manual breaker feeds",
        "expect(overlay).not.toContain('individualCircuitEndpointKeys')",
    ))
    require("frontend/src/pages/ElectricalDistributionLayoutPage.vue", (
        "Abgänge von LS-/RCBO-Geräten",
        "manuelle Einspeisungen zu den Schutzgeräten bleiben sichtbar",
        "allAssetPlacements",
        "allMeterPlacements",
        "meterPlacementEndpointKey(placement)",
    ))
    require("frontend/src/pages/ElectricalTopologyPage.vue", (
        "loadCabinetComponentFallbackEndpoints",
        "electricalApi.cabinetComponents(distribution.id)",
    ))
    require("RELEASE_NOTES_1.7.4.6.md", (
        "Phasenverteilerblock L1/L2/L3 → Sicherung Waschmaschine · L2",
        "Sicherung Waschmaschine → Stromkreis Waschmaschine",
        "Alembic-Head bleibt `0049`",
    ))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0049_")
    print("Releasevertrag 1.7.4.6 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
