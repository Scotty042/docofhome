"""Verify DocOfHome 1.7.2 N/PE rail release contracts."""
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
    version = "1.7.2"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    source = json.loads(read("SOURCE_INFO.json"))
    assert source["version"] == version
    assert source["release_notes"] == "RELEASE_NOTES_1.7.2.md"
    assert source["alembic_head"] == "0049"

    require("backend/app/distribution_layout.py", (
        "def _ensure_area_rail_component(",
        "DistributionAreaType.NEUTRAL_RAIL.value",
        "DistributionAreaType.PROTECTIVE_EARTH_RAIL.value",
        "Automatisch aus dem Schienenbereich erzeugter elektrischer Endpunkt.",
        "In einem N-Schienenbereich kann ausschließlich eine N-Schiene",
        "In einem PE-Schienenbereich kann ausschließlich eine PE-Schiene",
    ))
    require("backend/app/services/electrical_topology.py", (
        "def _restricted_conductor_phases(",
        'endpoint.device_type == "neutral_rail"',
        'endpoint.device_type == "protective_earth_rail"',
        "N- und PE-Schienen können nicht direkt miteinander verbunden werden.",
        "restricted_phases is None",
    ))
    require("frontend/src/pages/ElectricalDistributionLayoutPage.vue", (
        "cabinetComponentAreaOptions",
        "Diesen Bereich als verkabelbare Schiene anlegen",
        "Noch nicht als elektrischer Endpunkt angelegt.",
        "Schiene anlegen",
    ))
    require("frontend/src/pages/ElectricalTopologyPage.vue", (
        "restrictedEndpointConductors",
        "restrictedConnectionConductors",
        "Der Leiter wird durch die ausgewählte N- oder PE-Schiene festgelegt.",
        "Eine N-Schiene und eine PE-Schiene können nicht direkt miteinander verbunden werden.",
    ))
    require("backend/migrations/versions/0049_materialize_n_pe_rail_endpoints.py", (
        'revision: str = "0049"',
        'down_revision: str | None = "0048"',
        "electrical_distribution_areas",
        "electrical_cabinet_components",
        "neutral_rail",
        "protective_earth_rail",
    ))
    require("backend/tests/test_electrical_topology.py", (
        "test_n_and_pe_rails_are_selectable_and_keep_auxiliary_conductors_separate",
        'assert neutral_feed.json()["phases"] == ["N"]',
        'assert pe_feed.json()["phases"] == ["PE"]',
    ))
    require("backend/tests/test_electrical_layout.py", (
        "rail_components[\"neutral_rail\"]",
        "rail_components[\"protective_earth_rail\"]",
    ))
    require("RELEASE_NOTES_1.7.2.md", ("Alembic-Head: `0049`", "FI/RCD → N-Schiene"))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0049_")
    print("Releasevertrag 1.7.2 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
