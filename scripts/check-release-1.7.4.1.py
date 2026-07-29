"""Verify DocOfHome 1.7.4.1 main-wiring presentation contracts."""
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
    version = "1.7.4.1"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    source = json.loads(read("SOURCE_INFO.json"))
    assert source["version"] == version
    assert source["release_notes"] == "RELEASE_NOTES_1.7.4.1.md"
    assert source["alembic_head"] == "0049"

    require("frontend/src/components/CabinetWiringOverlay.vue", (
        "function individualCircuitEndpointKeys(",
        "endpoint.kind === 'circuit'",
        "individualCircuitDeviceTypes",
        "connection.target.kind === 'circuit'",
        "function connectionPortOffsets(",
        "function laneAssignments(",
        "function routeCategory(",
        "wiring-path-halo",
        "stroke-width: 2.35",
        "function isAutomaticBusbarContact(",
    ))
    require("frontend/src/pages/ElectricalDistributionLayoutPage.vue", (
        "Die Ansicht zeigt nur die Hauptverkabelung.",
        "Einzelne Stromkreise und ihre LS-/RCBO-Abgänge",
        "Kamm-/Sammelschienen erscheinen je Leiter einmal",
    ))
    require("frontend/src/components/CabinetWiringOverlay.test.ts", (
        "shows only main wiring and separates cable tracks",
        "individualCircuitEndpointKeys",
        "connectionPortOffsets",
        "laneAssignments",
    ))
    require("RELEASE_NOTES_1.7.4.1.md", (
        "Reduzierte Hauptverkabelung",
        "Verbesserte Linienführung",
        "Alembic-Head bleibt `0049`",
    ))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0049_")
    print("Releasevertrag 1.7.4.1 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
