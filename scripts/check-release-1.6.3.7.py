"""Verify DocOfHome 1.6.3.7 release contracts."""
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
    version = "1.6.3.7"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    source = json.loads(read("SOURCE_INFO.json"))
    assert source["version"] == version
    assert source["release_notes"] == "RELEASE_NOTES_1.6.3.7.md"
    assert source["alembic_head"] == "0046"

    require("backend/app/repositories/asset_engine.py", (
        "scalar_one_or_none()",
        "Older seeded asset types could exist without a matching counter row",
        "AssetCodeCounter(prefix=prefix, next_value=number + 1)",
    ))
    require("backend/tests/test_asset_engine.py", (
        "def test_asset_creation_repairs_missing_code_counter",
        'jarvis_code="SRA-007"',
        'assert first.jarvis_code == "SRA-008"',
    ))
    require("backend/migrations/versions/0046_repair_asset_code_counters.py", (
        'revision: str = "0046"',
        'down_revision: str | None = "0045"',
        "asset_code_counters",
        "required_next = highest + 1",
    ))
    require("backend/migrations/versions/0038_release_1_6_1_corrections.py", (
        '"prefix": "SRA"',
        '"name": "Smartes Relais / DIN-Schaltaktor"',
        "'Shelly Pro 1'",
    ))
    require("README.md", ("DocOfHome 1.6.3.7", "Migration `0046`"))
    require("RELEASE_NOTES_1.6.3.7.md", (
        "DIN-Gerät platzieren",
        "electrical_asset_placements",
        "Rückwärtskompatibilität",
    ))
    require("frontend/src/pages/ElectricalDistributionLayoutPage.vue", (
        ">DIN-Gerät platzieren</v-btn>",
        "Ziehe ein DIN-Gerät auf die gewünschte Teilungseinheit",
        "Sicherung, FI/RCD, Relais oder anderes DIN-Gerät platzieren",
    ))
    page = read("frontend/src/pages/ElectricalDistributionLayoutPage.vue")
    assert "Sicherungs-/Schutzgerät platzieren" not in page
    assert "Schutzgerät hinzufügen" not in page
    require("backend/app/services/phase_rail_connections.py", (
        "current DIN placements use the underlying ``asset`` endpoint",
        "ElectricalAssetPlacement",
        'target_kind="asset"',
    ))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0046_")
    print("Releasevertrag 1.6.3.7 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
