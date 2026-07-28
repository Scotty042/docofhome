"""Dependency-free release contract check for the 1.1.2 collected fixes."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(relative: str, *needles: str) -> None:
    content = text(relative)
    missing = [needle for needle in needles if needle not in content]
    if missing:
        joined = ", ".join(repr(item) for item in missing)
        raise AssertionError(f"{relative}: missing {joined}")


def main() -> int:
    checks = [
        (
            "Zähler-Ort/Asset",
            lambda: require(
                "frontend/src/pages/ConsumptionPage.vue",
                'v-model="meterForm.asset_id"',
                'v-model="meterForm.location_id"',
            ),
        ),
        (
            "Immich-Großansicht",
            lambda: require(
                "frontend/src/components/ImmichImageLinksCard.vue",
                "openPreview(link)",
                'v-model="previewDialog"',
                "Bild vergrößern",
            ),
        ),
        (
            "N/PE und halbe Bereiche",
            lambda: require(
                "frontend/src/pages/ElectricalDistributionLayoutPage.vue",
                "neutral_rail",
                "protective_earth_rail",
                "area-half",
                "Halbe Spaltenbreite",
            ),
        ),
        (
            "Home-Assistant-Livewerte",
            lambda: require(
                "backend/app/services/consumption.py",
                "home_assistant_power_entity_id",
                "home_assistant_voltage_entity_id",
                "def meter_live_values",
                "power_w=power",
                "voltage_v=voltage",
            ),
        ),
        (
            "Zählerplatzierung",
            lambda: require(
                "backend/app/distribution_layout.py",
                "def place_meter",
                "def place_asset_meter",
                "asset_type.is_meter",
            ),
        ),
        (
            "Verteilungs-Asset-Typ",
            lambda: require(
                "backend/app/services/electrical.py",
                'required_asset_type="Elektrische Verteilung"',
            ),
        ),
        (
            "Hierarchische Ortssortierung",
            lambda: require(
                "frontend/src/services/locationOptions.ts",
                "sort_order",
                "sortLocationTree",
                "locationSelectItems",
            ),
        ),
        (
            "Netzanschluss als Quelle",
            lambda: require(
                "backend/app/repositories/electrical_topology.py",
                "GRID_CONNECTION_ENDPOINT_ID",
                "ElectricalEndpointKind.GRID_CONNECTION",
                'else "Netzanschluss"',
            ),
        ),
        (
            "Logische Netzwerkschnittstellen",
            lambda: require(
                "backend/app/services/network.py",
                "logical_interface_id",
                "primary_address=primary.address",
                "def _validate_logical_interface",
            ),
        ),
        (
            "Gerätebezogene Netzwerkprüfung",
            lambda: require(
                "backend/app/services/network.py",
                "device_without_connection_count",
                "free_interface_count",
                "has_wireless_uplink",
            ),
        ),
    ]

    failures: list[str] = []
    for name, check in checks:
        try:
            check()
        except (AssertionError, OSError) as exc:
            failures.append(f"{name}: {exc}")

    if failures:
        print("Abnahmecheck fehlgeschlagen:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Gesammelte Fixes geprüft: {len(checks)}/10 Verträge vorhanden")
    return 0


if __name__ == "__main__":
    sys.exit(main())
