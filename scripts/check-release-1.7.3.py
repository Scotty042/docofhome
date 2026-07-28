"""Verify DocOfHome 1.7.3 split-conductor supply contracts."""
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
    version = "1.7.3"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    source = json.loads(read("SOURCE_INFO.json"))
    assert source["version"] == version
    assert source["release_notes"] == "RELEASE_NOTES_1.7.3.md"
    assert source["alembic_head"] == "0049"

    require("backend/app/services/electrical_topology.py", (
        "def _is_auxiliary_conductor_only(",
        "target's aggregate supply, not to this N/PE-only path",
        "if self._is_auxiliary_conductor_only(payload.phases):",
        "line_phase_relevant = not self._is_auxiliary_conductor_only(stored_phases)",
        "return sorted(set(stored), key=order.__getitem__), []",
    ))
    require("frontend/src/pages/ElectricalTopologyPage.vue", (
        "auxiliaryConductorOnly",
        "linePhaseBindingRequested",
        "requestedLinePhases.length",
        "Außenleiter anderer Einspeisungen werden nicht auf diesen Leiterweg übertragen.",
        'restrictedConnectionConductors === null && phaseLockActive',
    ))
    require("backend/tests/test_electrical_topology.py", (
        "test_separate_neutral_feed_does_not_inherit_parallel_line_phases",
        'assert neutral["effective_phases"] == ["N"]',
        'assert neutral["phase_warnings"] == []',
        'assert rcd_node["incoming_phases"] == ["L1", "L2", "L3", "N"]',
    ))
    require("RELEASE_NOTES_1.7.3.md", (
        "Phasenverteilerblock → FI/RCD: L1, L2, L3",
        "Alembic-Head: `0049`",
        "Ein erneutes",
        "Speichern ist nicht erforderlich.",
    ))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0049_")
    print("Releasevertrag 1.7.3 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
