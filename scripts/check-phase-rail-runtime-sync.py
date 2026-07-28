"""Dependency-free contracts for phase-rail contacts to all DIN devices."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def main() -> int:
    service = read("backend/app/services/phase_rail_connections.py")
    layout = read("backend/app/distribution_layout.py")
    topology = read("backend/app/services/electrical_topology.py")
    repository = read("backend/app/repositories/electrical_topology.py")
    api = read("backend/app/api/v1/electrical_layout.py")
    frontend = read("frontend/src/pages/ElectricalDistributionLayoutPage.vue")
    frontend_api = read("frontend/src/services/electricalApi.ts")

    required_service = (
        "class PhaseRailContact",
        "target_kind=\"asset\"",
        "target_kind=\"protective_device\"",
        "ElectricalAssetPlacement",
        "def _contacts_for_distribution(",
        "def _asset_contact(",
        "phase_rail_din_asset_phases",
        "def _sync_rail_contacts(",
        "explicit_assets=%d",
        "Automatische Phasenschienen-Verbindungen sind nach dem Abgleich",
    )
    for fragment in required_service:
        assert fragment in service, fragment

    assert "PhaseRailConnectionService(self.session).sync_distribution(distribution_id)" in layout
    assert "visible_asset_ids" in layout
    assert '"/{distribution_id}/cabinet-components/{component_id}/synchronize"' in api
    assert "payload.asset_ids" in api
    assert "visibleDinAssetIds()" in frontend
    assert "assetPlacements.value.map((placement) => placement.asset_id)" in frontend
    assert "DIN-Gerät(en) verbunden" in frontend
    assert "asset_ids: assetIds" in frontend_api
    assert "def din_asset_phases(" in repository
    assert "effective_phases=din_asset_phases(asset)" in repository
    assert "effective_asset_module_width(self.session, device_asset)" in repository
    assert "ElectricalEndpointKind.ASSET" in topology
    assert "_phase_rail_phases_for_asset" in topology
    assert "0045_phase_rail_all_din_contacts.py" in read("scripts/check-release-1.6.3.5.py")

    print("Laufzeitvertrag: Kammschiene erzeugt Kontakte zu allen DIN-Geräten.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
