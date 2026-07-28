"""Verify the DocOfHome 1.7.1 merged release contracts without runtime dependencies."""
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
    version = "1.7.1"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    source = json.loads(read("SOURCE_INFO.json"))
    assert source["version"] == version
    assert source["release_notes"] == "RELEASE_NOTES_1.7.1.md"
    assert source["alembic_head"] == "0048"

    require("backend/app/repositories/asset_engine.py", (
        "Older seeded asset types could exist without a matching counter row",
        "AssetCodeCounter(prefix=prefix, next_value=number + 1)",
    ))
    require("backend/app/electrical_device_classification.py", (
        "def is_rcd_asset_type_name",
        "def protective_asset_device_type",
        "def is_end_protective_asset_type_name",
    ))
    require("backend/app/services/electrical_circuit.py", (
        'reference_type="asset"',
        "_validate_asset_protective_device",
        "protective_device_asset_id",
        "Das Schutzgerät ist bereits dem Stromkreis",
    ))
    require("backend/app/distribution_layout.py", (
        "_validate_rcd_asset",
        "linked_rcd_asset_id=record.linked_rcd_asset_id",
        "protective_device_asset_id == asset_id",
    ))
    require("backend/app/services/electrical_topology.py", (
        "def _active_physical_phase_source(",
        "ElectricalPhaseSource.BUSBAR",
        "ElectricalPhaseSource.WIRE",
    ))
    require("backend/app/services/work.py", ("reminder_days_json", "monthrange", "meter-reading:"))
    require("backend/app/services/network.py", (
        "sync_observed_addresses",
        "list_ip_overview",
        "accept_observed_address",
        "ignore_observed_address",
        "NetworkIpStatus.MISMATCH",
    ))
    require("backend/app/connectors/fritzbox.py", ("int(address)", "return sorted(result, key=sort_key)"))
    require("backend/app/schemas/network.py", (
        "Unterstriche sind in Hostnamen nicht erlaubt",
        "Geschwindigkeit muss 100, 1000 oder 2500 Mbit/s sein",
    ))
    require("backend/app/services/product_images.py", (
        "class AssetImageService",
        'image.thumbnail((1600, 1600)',
        'format="WEBP"',
    ))
    require("frontend/src/components/GlobalNotifications.vue", ("<Teleport to=\"body\">", "z-index: 32000"))
    require("frontend/src/pages/NetworkDeviceDetailPage.vue", (
        "switch-port-row", "overflow-x: auto", "sequential_halves"
    ))
    require("frontend/src/pages/NetworkPage.vue", (
        "IP-Adressen",
        "ipAssignmentFilter",
        "compact-device-card",
        'icon="mdi-ip-outline" title="Keine IP-Adressen"',
    ))
    assert "mdi-ip-off-outline" not in read("frontend/src/pages/NetworkPage.vue")
    require("frontend/src/pages/SmartHomePage.vue", (
        "createEmptyAsset, type Asset, type AssetType, type AssetWrite",
        "ref<AssetWrite>(createEmptyAsset())",
    ))
    require("frontend/src/services/homeAssistantAssetDraft.ts", (
        "image_url: null",
        "image_source: 'url'",
        "image_reference: null",
    ))
    require("frontend/src/pages/locationRouteLifecycle.test.ts", (
        "asset_type_image_url: null",
        "effective_image_url: null",
        "asset_type_is_meter: false",
    ))
    require("frontend/src/services/locationAssets.test.ts", (
        "asset_type_image_url: null",
        "effective_image_url: null",
        "asset_type_is_meter: false",
    ))
    require("frontend/src/services/electricalCircuitApi.test.ts", (
        "protective_device_type: 'mcb'",
        "protective_device_assignment_missing: false",
    ))
    require("frontend/src/services/electricalTopology.test.ts", (
        "phase_source: 'wire'",
        "source_connection_id: null",
    ))
    require("frontend/src/services/homeAssistantAssetDraft.test.ts", (
        "image_source: 'url'",
        "is_meter: false",
        "switch_port_layout: 'odd_even'",
    ))
    require("frontend/src/pages/AssetEditorPage.vue", ("Individuelles Asset-Bild", 'upload-kind="asset"'))
    require("frontend/src/pages/ElectricalDistributionLayoutPage.vue", (
        "linkedRcdSelection",
        "linked_rcd_asset_id",
        ">DIN-Gerät platzieren</v-btn>",
    ))
    require("frontend/src/pages/ElectricalCircuitEditorPage.vue", (
        "protectiveDeviceSelection",
        "protective_device_asset_id",
        "Sicherung / Schutzgerät",
    ))
    require("backend/migrations/versions/0046_repair_asset_code_counters.py", (
        'revision: str = "0046"',
        'down_revision: str | None = "0045"',
    ))
    require("backend/migrations/versions/0047_link_cabinet_rails_to_din_rcd_assets.py", (
        'revision: str = "0047"',
        'down_revision: str | None = "0046"',
        "linked_rcd_asset_id",
    ))
    require("backend/migrations/versions/0048_release_1_7_1.py", (
        'revision: str = "0048"',
        'down_revision: str | None = "0047"',
        "network_observed_addresses",
        "phase_source",
        "is_meter",
        "switch_port_layout",
        "protective_device_asset_id",
    ))
    require("DocOfHome_Runbook_Version_1.7.md", ("DOH-1701", "DOH-1712", "Definition of Done"))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0048_")
    print("Releasevertrag 1.7.1 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
