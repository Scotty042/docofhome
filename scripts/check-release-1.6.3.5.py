"""Verify DocOfHome 1.6.3.5 release contracts."""
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
    version = "1.6.3.5"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    source = json.loads(read("SOURCE_INFO.json"))
    assert source["version"] == version
    assert source["release_notes"] == "RELEASE_NOTES_1.6.3.5.md"
    assert source["alembic_head"] == "0045"

    require("backend/app/electrical_phase_rail.py", (
        "def phase_rail_din_asset_phases(",
        "def active_line_pole_count(",
        "count -= 1",
    ))
    require("backend/app/services/phase_rail_connections.py", (
        "class PhaseRailContact",
        "ElectricalAssetPlacement",
        'target_kind="asset"',
        'target_kind="protective_device"',
        "def _sync_rail_contacts(",
        "def _contacts_for_distribution(",
        "phase_rail_din_asset_phases",
    ))
    require("backend/app/distribution_layout.py", (
        "visible_asset_ids",
        "Eine Phasen-/Kammschiene darf ein DIN-Gerät nicht nur",
        "PhaseRailConnectionService(self.session).sync_distribution(distribution_id)",
    ))
    require("backend/app/services/electrical_topology.py", (
        "def _phase_rail_phases_for_asset(",
        "ElectricalEndpointKind.ASSET",
        "target.kind in {",
    ))
    require("backend/app/services/electrical.py", (
        "Ein vierpoliger FI/RCD",
        "der vierte Pol bleibt für N frei",
    ))
    require("frontend/src/pages/ElectricalDistributionLayoutPage.vue", (
        "visibleDinAssetIds()",
        "verbindet automatisch jedes vollständig überdeckte DIN-Gerät",
        "der vierte Pol bleibt für N frei",
        "DIN-Gerät(en) verbunden",
    ))
    require("frontend/src/pages/ElectricalTopologyPage.vue", (
        "['protective_device', 'asset'].includes(connection.target.kind)",
    ))
    require("backend/migrations/versions/0045_phase_rail_all_din_contacts.py", (
        'revision: str = "0045"',
        'down_revision: str | None = "0044"',
        "electrical_asset_placements",
        "target_kind IN ('protective_device', 'asset')",
        "_protective_line_count",
    ))
    require("backend/app/services/about.py", (
        "(?:\\.\\d+)?",
        "tuple[int, int, int, int]",
    ))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0045_")
    require("README.md", ("DocOfHome 1.6.3.5", "Migration `0045`"))
    require("RELEASE_NOTES_1.6.3.5.md", ("allgemeine DIN-Assets", "vierpoligen FI/RCD"))
    print("Releasevertrag 1.6.3.5 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
