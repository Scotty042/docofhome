"""Verify source contracts added for DocOfHome 1.6.2."""

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
    require("VERSION", ("1.6.2",))
    require(
        "frontend/src/pages/ConsumptionPage.vue",
        (
            "Letzter Wert:",
            "OBIS 1.8.0",
            "OBIS 2.8.0",
            "Zähler austauschen",
        ),
    )
    require(
        "frontend/src/pages/SettingsPage.vue",
        ("DuckDuckGo Images", "Wikimedia Commons"),
    )
    require(
        "backend/app/services/product_images.py",
        ("_search_duckduckgo", "_search_wikimedia", "_relevance_score"),
    )
    require(
        "frontend/src/pages/AssetDetailPage.vue",
        ("Einspeisung von", "Weiterführung zu"),
    )
    require(
        "backend/migrations/versions/0038_release_1_6_1_corrections.py",
        ("Smartes Relais / DIN-Schaltaktor", "Shelly Pro 1"),
    )
    require(
        "frontend/src/pages/ElectricalDistributionLayoutPage.vue",
        ("writing-mode: vertical-rl", "Nicht zugeordnet"),
    )
    require(
        "frontend/src/pages/ElectricalListPage.vue",
        ("aktive Sicherungs-/Schutzgeräte",),
    )
    require(
        "backend/app/services/work.py",
        (
            "_sync_monthly_meter_tasks",
            "meter-reading:",
            "Automatisch durch gespeicherte Zählerablesung erledigt.",
            "Ableseplan wurde wieder aktiviert.",
            "Automatisch erzeugte Ableseaufgaben werden durch den Ableseplan verwaltet",
        ),
    )
    require(
        "backend/app/services/consumption.py",
        (
            'ConsumptionMeterType.ELECTRICITY_PV, "pv_generation"',
            'ConsumptionMeterType.ELECTRICITY_FEED_IN, "pv_feed_in"',
            "active_dashboard_meters",
        ),
    )
    require(
        "backend/app/services/electrical_topology.py",
        (
            "effective_phases",
            "phase_warnings",
            "Gespeicherte Verbindung enthält abweichende Phasen",
            "Verteilungen sind strukturelle Behälter",
            "_enforce_protective_device_line_phases",
            "widersprüchliche wirksame Phasen",
        ),
    )
    require(
        "frontend/src/pages/ElectricalTopologyPage.vue",
        (
            "forcedLinePhases",
            "Durch Sammel-/Phasenschiene fest vorgegeben",
            "updateConnectionPhases",
            "dialogError",
            "L1/L2/L3 werden aus Position und Startphase der Schiene berechnet",
        ),
    )
    require(
        "backend/app/distribution_layout.py",
        (
            "placing_overlay_rail",
            "placing_component_mounting_side",
            "Montageebene",
            "ElectricalCabinetComponentType.PHASE_RAIL",
            "Die Kamm-/Phasenschiene versorgt noch Schutzgeräte",
            "allow_junction_box",
            "In einer Verteilerdose können nur Klemmen",
            '"mounting_side"',
        ),
    )
    require(
        "frontend/src/pages/ElectricalDistributionLayoutPage.vue",
        (
            "junctionBoxLayout",
            "Komponenten der Verteilerdose",
            "ohne eigene TE-Belegung",
            "cabinetComponentForm.mounting_side",
            "excludeDeviceId !== null || excludeAssetId !== null",
        ),
    )
    require(
        "frontend/src/components/AssetDuplicateDialog.vue",
        (
            "node.layout_mode !== 'junction_box'",
            "layoutMode: node.layout_mode",
        ),
    )
    require(
        "backend/migrations/versions/0039_release_1_6_2_integrity.py",
        (
            'revision: str = "0039"',
            'down_revision: str | None = "0038"',
            "automation_key",
            "junction_box",
            "mounting_side",
        ),
    )
    require(
        "backend/app/core/project_info.py",
        (
            "https://github.com/Scotty042/docofhome",
            "https://github.com/Scotty042/docofhome/releases",
            "https://github.com/Scotty042/docofhome/issues",
        ),
    )

    source_info = json.loads(read("SOURCE_INFO.json"))
    if source_info["version"] != "1.6.2" or source_info["alembic_head"] != "0039":
        raise AssertionError("SOURCE_INFO.json enthält falsche Release-Metadaten")
    if not source_info["repository"].startswith("https://github.com/"):
        raise AssertionError("SOURCE_INFO.json enthält keinen GitHub-Bezug")

    lock = json.loads(read("frontend/package-lock.json"))
    if lock["version"] != "1.6.2" or lock["packages"][""]["version"] != "1.6.2":
        raise AssertionError("Eigene package-lock-Metadaten sind nicht 1.6.2")

    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    if not migrations[-1].name.startswith("0039_"):
        raise AssertionError("Alembic-Head muss für 1.6.2 bei 0039 liegen")

    print(
        "Release 1.6.2: Aufgaben-, Dashboard-, Phasen-, Verteiler- und "
        "Paketverträge vorhanden."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
