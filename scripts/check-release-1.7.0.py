"""Verify the DocOfHome 1.7.0 release contracts without runtime dependencies."""
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
    version = "1.7.0"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    source = json.loads(read("SOURCE_INFO.json"))
    assert source["version"] == version
    assert source["release_notes"] == "RELEASE_NOTES_1.7.0.md"
    assert source["alembic_head"] == "0046"

    require("backend/app/services/electrical_circuit.py", (
        "protective_device_options",
        'device.record.device_type not in {"fuse", "mcb", "rcbo"}',
        "Das ausgewählte Schutzgerät muss aktiv und in der Verteilung platziert sein.",
        "Das Schutzgerät ist bereits dem Stromkreis",
    ))
    require("backend/app/services/electrical_topology.py", (
        "def _active_physical_phase_source(",
        "ElectricalPhaseSource.BUSBAR",
        "ElectricalPhaseSource.WIRE",
        "target_physical = self._active_physical_phase_source(target)",
    ))
    require("backend/app/distribution_layout.py", ("asset_type.is_meter",))
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
    require("frontend/src/pages/NetworkPage.vue", ("IP-Adressen", "ipAssignmentFilter", "compact-device-card"))
    require("frontend/src/pages/AssetEditorPage.vue", ("Individuelles Asset-Bild", 'upload-kind="asset"'))
    require("backend/migrations/versions/0046_release_1_7_0.py", (
        'revision: str = "0046"',
        'down_revision: str | None = "0045"',
        "network_observed_addresses",
        "phase_source",
        "is_meter",
        "switch_port_layout",
    ))
    require("DocOfHome_Runbook_Version_1.7.md", ("DOH-1701", "DOH-1712", "Definition of Done"))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0046_")
    print("Releasevertrag 1.7.0 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
