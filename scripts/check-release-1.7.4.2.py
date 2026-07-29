"""Verify DocOfHome 1.7.4.2 schematic wiring contracts."""
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
    version = "1.7.4.2"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    source = json.loads(read("SOURCE_INFO.json"))
    assert source["version"] == version
    assert source["release_notes"] == "RELEASE_NOTES_1.7.4.2.md"
    assert source["alembic_head"] == "0049"

    require("frontend/src/components/CabinetWiringOverlay.vue", (
        "function isCompactBranchEndpoint(",
        "element.classList.contains('narrow-module-device')",
        "rect.width < 84",
        "Parallel database records",
        "function sectionBounds(",
        "function localOrthogonalPath(",
        "function crossSectionOrthogonalPath(",
        "upper card borders as a shared trunk",
        "function externalOrthogonalPath(",
        "stroke-width: 2.05",
    ))
    require("frontend/src/pages/ElectricalDistributionLayoutPage.vue", (
        "schematische Hauptverkabelung",
        "LS-/RCBO-Abgänge werden ausgeblendet",
        "gebündelt an den Feldrändern",
    ))
    require("frontend/src/components/CabinetWiringOverlay.test.ts", (
        "routes them through cabinet gutters",
        "isCompactBranchEndpoint",
        "crossSectionOrthogonalPath",
    ))
    require("RELEASE_NOTES_1.7.4.2.md", (
        "Schematische Hauptverkabelung",
        "oberen Feldränder",
        "Alembic-Head bleibt `0049`",
    ))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0049_")
    print("Releasevertrag 1.7.4.2 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
