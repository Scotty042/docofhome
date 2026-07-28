"""Verify DocOfHome 1.6.3.8 FI/RCD DIN-Asset release contracts."""
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
    version = "1.6.3.8"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    source = json.loads(read("SOURCE_INFO.json"))
    assert source["version"] == version
    assert source["release_notes"] == "RELEASE_NOTES_1.6.3.8.md"
    assert source["alembic_head"] == "0047"

    require("backend/app/electrical_device_classification.py", (
        "def is_rcd_asset_type_name",
        '"rcd" in tokens',
        '"fi" in tokens',
    ))
    require("backend/app/models/electrical.py", (
        'foreign_key="assets.id"',
        "ck_electrical_cabinet_components_single_rcd_reference",
    ))
    require("backend/app/schemas/electrical_layout.py", (
        "linked_rcd_asset_id: UUID | None",
        "is_rcd: bool = False",
        "Es darf nur ein FI/RCD ausgewählt werden",
    ))
    require("backend/app/distribution_layout.py", (
        "_validate_rcd_asset",
        "is_rcd_asset_type_name",
        "linked_rcd_asset_id=record.linked_rcd_asset_id",
        "Der FI/RCD ist noch einer Phasen-/Kammschiene oder N-Schiene ",
    ))
    require("frontend/src/pages/ElectricalDistributionLayoutPage.vue", (
        "placement.is_rcd === true",
        "linkedRcdSelection",
        "linked_rcd_asset_id",
        "Zugehöriger FI/RCD (optional)",
    ))
    require("backend/migrations/versions/0047_link_cabinet_rails_to_din_rcd_assets.py", (
        'revision: str = "0047"',
        'down_revision: str | None = "0046"',
        "linked_rcd_asset_id",
    ))
    require("RELEASE_NOTES_1.6.3.8.md", (
        "FI/RCD-Zuordnung",
        "DIN-Asset-Platzierungen",
        "Migration `0047`",
    ))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0047_")
    print("Releasevertrag 1.6.3.8 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
