"""Verify source contracts added for DocOfHome 1.3.1."""

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
        "backend/app/models/asset_engine.py",
        (
            "ck_asset_types_module_width",
            "ck_assets_module_width",
            "module_width: int | None",
        ),
    )
    require(
        "backend/app/services/asset_engine.py",
        (
            '"effective_module_width"',
            "product.module_width is not None",
            "bevor Status, Produkt, Asset-Typ oder DIN-Breite geändert werden",
        ),
    )
    require(
        "backend/app/distribution_layout.py",
        (
            "Die Platzierungsbreite muss der am Asset, Asset-Typ oder Produkt",
            "exclude_asset_placement_id",
            "effective_asset_module_width",
            "Schutzgeräte-Asset benötigt eine DIN-Breite",
        ),
    )
    require(
        "backend/app/services/electrical.py",
        (
            "def _resolved_module_width",
            "effective_module_width=effective_asset_module_width",
            "requested_width != inherited_width",
        ),
    )
    require(
        "backend/app/services/din_width.py",
        (
            "def effective_asset_module_width",
            "asset.module_width",
            "product.din_rail_mount",
            "asset_type.module_width",
        ),
    )
    require(
        "frontend/src/pages/SmartHomePage.vue",
        (
            "const createAssetForm = ref<AssetWrite>",
            "inventory_number: null, module_width: null, status: 'active'",
        ),
    )
    require(
        "frontend/src/pages/ElectricalDistributionLayoutPage.vue",
        (
            "simpleAssetPlacementsForRow",
            "beginAssetDrag",
            "placeDraggedItem",
            "module-drop-cell",
            "Noch nicht platzierte DIN-Assets",
            "protectiveDeviceWidth",
            "readonly",
        ),
    )
    require(
        "backend/app/services/electrical_topology.py",
        (
            "def _validate_cabinet_phase_flow",
            "incoming.update(phases)",
            "outgoing - incoming",
            "weil diese Leiter nicht eingespeist werden",
        ),
    )
    require(
        "frontend/src/services/electricalTopology.ts",
        (
            "incomingTopologyConnections",
            "incomingConnections: ElectricalConnection[]",
        ),
    )
    require(
        "frontend/src/components/ElectricalWiringSummary.vue",
        (
            "dokumentierte Einspeisungen",
            "incomingConnections.value.flatMap",
        ),
    )
    require(
        "backend/app/services/consumption.py",
        (
            "return start_local.astimezone(UTC), local_now.astimezone(UTC)",
            "end_is_covered",
            "datetime.now(zone).date()",
        ),
    )
    require(
        "backend/migrations/versions/0032_asset_and_type_din_width.py",
        (
            'revision: str = "0032"',
            'down_revision: str | None = "0031"',
            'op.batch_alter_table("asset_types")',
            'op.batch_alter_table("assets")',
        ),
    )
    print("Release 1.3.1: alle statischen DIN-, Phasen- und Verbrauchsverträge vorhanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
