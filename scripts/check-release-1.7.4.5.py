"""Verify DocOfHome 1.7.4.5 cabinet and placement contracts."""
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


def main() -> int:
    version = "1.7.4.5"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    source = json.loads(read("SOURCE_INFO.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    assert source["version"] == version
    assert source["base_version"] == "1.7.4.4"
    assert source["release_notes"] == "RELEASE_NOTES_1.7.4.5.md"
    assert source["alembic_head"] == "0049"

    require("frontend/src/components/CabinetWiringOverlay.vue", (
        "entry.endpoint.kind === 'grid_connection'",
        "height.value - verticalPadding",
        "flowThrough",
        "label: 'IN'",
        "label: 'OUT'",
        "role === 'target' ? -horizontalOffset : horizontalOffset",
    ))
    require("frontend/src/pages/ElectricalDistributionLayoutPage.vue", (
        "allAssetPlacements",
        "allMeterPlacements",
        "loadAllProtectiveDevices",
        "matchesCurrentDistributionLocation",
        "meterPlacementEndpointKey(placement)",
        "data-electrical-flow-through",
    ))
    require("frontend/src/pages/ElectricalTopologyPage.vue", (
        "loadCabinetComponentFallbackEndpoints",
        "electricalApi.distributionTree()",
        "electricalApi.cabinetComponents(distribution.id)",
        "Phasenschiene / Kammschiene",
    ))
    require("backend/app/api/v1/electrical_layout.py", (
        '"/placements/assets"',
        '"/placements/meters"',
    ))
    require("RELEASE_NOTES_1.7.4.5.md", (
        "IN",
        "OUT",
        "Unterverteilung",
        "Alembic-Head bleibt `0049`",
    ))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0049_")
    print("Releasevertrag 1.7.4.5 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
