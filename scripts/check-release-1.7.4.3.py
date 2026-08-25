"""Verify DocOfHome 1.7.4.3 free cabinet wiring contracts."""
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
    version = "1.7.4.3"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    source = json.loads(read("SOURCE_INFO.json"))
    assert source["version"] == version
    assert source["base_version"] == "1.7.4.2"
    assert source["release_notes"] == "RELEASE_NOTES_1.7.4.3.md"
    assert source["alembic_head"] == "0049"

    require("frontend/src/components/CabinetWiringOverlay.vue", (
        "function individualCircuitEndpointKeys(",
        "function connectionPortOffsets(",
        "function laneAssignments(",
        "function orthogonalPath(",
        "const conductorOffset = (phaseIndex - center) * 8",
        "const trackY = baseMidY + lane + conductorOffset",
        "Mehrere Datensätze zwischen denselben Hauptkomponenten",
        "wiring-path-halo",
    ))
    reject("frontend/src/components/CabinetWiringOverlay.vue", (
        "function sectionBounds(",
        "function crossSectionOrthogonalPath(",
        "upper card borders as a shared trunk",
    ))
    require("frontend/src/pages/ElectricalDistributionLayoutPage.vue", (
        "innerhalb der Schrankdarstellung",
        "festem Abstand",
        "LS-/RCBO-Abgänge",
    ))
    require("frontend/src/components/CabinetWiringOverlay.test.ts", (
        "routes freely inside the cabinet",
        "conductorOffset = (phaseIndex - center) * 8",
    ))
    require("RELEASE_NOTES_1.7.4.3.md", (
        "Freie Leitungsführung",
        "festen Abstand von 8 Pixeln",
        "Alembic-Head bleibt `0049`",
    ))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0049_")
    print("Releasevertrag 1.7.4.3 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
