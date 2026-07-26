"""Verify source contracts added for DocOfHome 1.3.0."""

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
    require(
        "backend/app/models/electrical.py",
        (
            "class ElectricalCabinetComponent",
            'phase_distribution_block',
            "area_id: UUID | None",
            "outgoing_connections",
        ),
    )
    require(
        "backend/app/schemas/electrical_topology.py",
        ('CABINET_COMPONENT = "cabinet_component"',),
    )
    require(
        "backend/app/distribution_layout.py",
        (
            "def create_cabinet_component",
            "def update_cabinet_component",
            "def archive_cabinet_component",
            "def _validate_module_placement",
            "Die einfache Reihenaufteilung verwendet keinen DIN-Bereich.",
        ),
    )
    require(
        "backend/app/repositories/electrical_topology.py",
        (
            "ElectricalCabinetComponent",
            "Phasenverteilerblock",
            "ElectricalEndpointKind.CABINET_COMPONENT",
        ),
    )
    require(
        "backend/app/services/asset_engine.py",
        (
            "def _series_slots",
            "ElectricalCabinetComponent",
            "Die einfache Reihenaufteilung verwendet keinen DIN-Bereich.",
        ),
    )
    require(
        "frontend/src/pages/ElectricalDistributionLayoutPage.vue",
        (
            "dropDeviceSimple",
            "cabinet_component",
            "Schrankkomponente",
            "simpleDropCellClasses",
        ),
    )
    require(
        "frontend/src/components/AssetDuplicateDialog.vue",
        (
            "selectedUsesSections",
            "Diese Verteilung verwendet die einfache Reihenaufteilung",
            "placeSequentially.value && selectedUsesSections.value",
        ),
    )
    require(
        "backend/migrations/versions/0031_cabinet_components_and_rows_placements.py",
        (
            'revision: str = "0031"',
            'down_revision: str | None = "0030"',
            "electrical_cabinet_components",
            "cabinet_component",
        ),
    )
    print("Release 1.3.0: alle statischen Schrank- und Reihenlayout-Verträge vorhanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
