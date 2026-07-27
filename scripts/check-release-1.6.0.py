"""Verify source contracts added for DocOfHome 1.6.0."""

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
    require("VERSION", ("1.6.0",))
    require(
        "frontend/src/pages/SetupWizardPage.vue",
        ("watch(currentStep", "integrationTestResult.value = null"),
    )
    require(
        "frontend/src/pages/GuidedSetupPage.vue",
        ("name: 'asset-detail'", "Asset öffnen", "Zur Übersicht", "redirectFailed"),
    )
    require(
        "backend/app/services/backups.py",
        (
            'CURRENT_BACKUP_PREFIX = "DocOfHome-backup-"',
            'LEGACY_BACKUP_PREFIXES = ("tectoryn-backup-",)',
        ),
    )
    require(
        "backend/app/services/product_images.py",
        ("DUCKDUCKGO_IMAGES", "DuckDuckGo Images", "_relevance_score"),
    )
    require(
        "frontend/src/pages/ElectricalDistributionLayoutPage.vue",
        (
            "isElectricalConsumptionMeterType",
            "isNonElectricalMeterAssetType",
            "cabinet-legend",
            "cabinet-type-smart-meter",
            "technical_short_label",
        ),
    )
    require(
        "frontend/src/pages/MasterDataPage.vue",
        (
            "Stromstoßschalter",
            "breaker_characteristic: 'B'",
            "rated_current_a: 16",
            "coil_voltage_v: 230",
            "contact_type: 'normally_open'",
        ),
    )
    require(
        "backend/app/services/smart_meter.py",
        ("SmartMeterMeasurementService", "connection_id", "entities"),
    )
    require(
        "frontend/src/components/SmartMeterMeasurementPointsCard.vue",
        ("Gemessene Verkabelung", "Home-Assistant-Entitäten", "Messrichtung"),
    )
    require(
        "frontend/src/content/handbook.ts",
        (
            "Nicht jede Sammelschiene ist eine Kammschiene",
            "Stromwandlerklemme / CT-Klemme",
        ),
    )
    require(
        "backend/migrations/versions/0037_release_1_6_electrical_measurements.py",
        (
            'revision: str = "0037"',
            'down_revision: str | None = "0036"',
            'sa.Column("coil_voltage_v"',
            'sa.Column("contact_type"',
        ),
    )
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    if not migrations[-1].name.startswith("0037_"):
        raise AssertionError("Alembic-Head muss für 1.6.0 bei 0037 liegen")

    lock = json.loads(read("frontend/package-lock.json"))
    if lock["version"] != "1.6.0" or lock["packages"][""]["version"] != "1.6.0":
        raise AssertionError("Eigene package-lock-Metadaten sind nicht 1.6.0")
    if lock["packages"]["node_modules/rfdc"]["version"] != "1.4.1":
        raise AssertionError("Transitive rfdc-Abhängigkeit wurde verändert")

    print("Release 1.6.0: zentrale Assistenten-, Elektro-, Backup- und CT-Verträge vorhanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
