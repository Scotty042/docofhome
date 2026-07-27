"""Verify source contracts added for DocOfHome 1.6.1."""

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
    require("VERSION", ("1.6.1",))
    require(
        "backend/app/services/consumption.py",
        ("def replace_meter(", "active_dashboard_meters", "pv_generation"),
    )
    require(
        "backend/app/services/product_images.py",
        (
            "product_image_source_wikimedia_enabled",
            "product_image_source_duckduckgo_enabled",
            "_relevance_score",
        ),
    )
    require(
        "backend/app/services/protective_devices.py",
        ("PROTECTIVE_DEVICE_TYPES", "is_protective_asset_type"),
    )
    require(
        "backend/migrations/versions/0038_release_1_6_1_corrections.py",
        (
            'revision: str = "0038"',
            'down_revision: str | None = "0037"',
            "Smartes Relais / DIN-Schaltaktor",
            "Shelly Pro 1",
        ),
    )
    require(
        "frontend/src/pages/ConsumptionPage.vue",
        ("Zählerwechsel", "1.8.0", "2.8.0"),
    )
    require(
        "frontend/src/services/electricalTopology.ts",
        ("phaseDistributionGroups", "walkPath", "cycleDetected", "Mehrphasig"),
    )
    require(
        "frontend/src/components/PhaseSupplyPathsCard.vue",
        (
            "Vollständige Reihenfolge ab Phasenverteilerblock",
            "phase-supply-flow",
            "Phasenwechsel oder Phasenerweiterung im dokumentierten Weg",
        ),
    )
    require(
        "frontend/src/pages/ElectricalDistributionLayoutPage.vue",
        ("PhaseSupplyPathsCard", "Versorgungswege im Zählerschrank"),
    )
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    if not migrations[-1].name.startswith("0038_"):
        raise AssertionError("Alembic-Head muss für 1.6.1 bei 0038 liegen")

    lock = json.loads(read("frontend/package-lock.json"))
    if lock["version"] != "1.6.1" or lock["packages"][""]["version"] != "1.6.1":
        raise AssertionError("Eigene package-lock-Metadaten sind nicht 1.6.1")

    print("Release 1.6.1: zentrale Zähler-, Elektro-, Bild- und Netzwerkverträge vorhanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
