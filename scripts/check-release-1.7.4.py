"""Verify DocOfHome 1.7.4 cabinet presentation contracts."""
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


def forbid(relative: str, fragments: tuple[str, ...]) -> None:
    source = read(relative)
    present = [fragment for fragment in fragments if fragment in source]
    if present:
        raise AssertionError(f"{relative}: unerlaubt vorhanden: {', '.join(present)}")


def main() -> int:
    version = "1.7.4"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    source = json.loads(read("SOURCE_INFO.json"))
    assert source["version"] == version
    assert source["release_notes"] == "RELEASE_NOTES_1.7.4.md"
    assert source["alembic_head"] == "0049"

    require("frontend/src/pages/ElectricalDistributionLayoutPage.vue", (
        "const viewMode = ref<'overview' | 'wiring'>('overview')",
        '>Übersicht</v-btn>',
        '>Verkabelung</v-btn>',
        '<CabinetWiringOverlay',
        'Vorgelagerte Verbindungen',
        'Nachgelagerte Verbindungen',
        'simpleRowElementCount',
        'areaRowElementCount',
        'platzierte Elemente in dieser Reihe',
        'data-electrical-endpoint-key',
        'Automatische Kontakte einer Kamm-/Sammelschiene werden nicht einzeln gezeichnet.',
    ))
    forbid("frontend/src/pages/ElectricalDistributionLayoutPage.vue", (
        'value="expanded"',
        '<ElectricalWiringSummary',
        'import ElectricalWiringSummary',
        '<v-chip size="x-small">{{ group.devices.length }}</v-chip>',
    ))
    require("frontend/src/components/CabinetWiringOverlay.vue", (
        'function isAutomaticBusbarContact(',
        "connection.connection_type === 'busbar'",
        "endpoint.kind === 'grid_connection'",
        "if (endpoint.kind === 'distribution') return 'square'",
        "return source ? 'triangle' : 'circle'",
        'wire-l1',
        'wire-l2',
        'wire-l3',
        'wire-n',
        'wire-pe',
        'Hausanschluss',
    ))
    require("frontend/src/components/PhaseSupplyPathsCard.vue", (
        '.phase-supply-chip-l2 { background: #111 !important;',
        '.phase-supply-chip-l3 { background: #616161 !important;',
        'color: #fff !important;',
    ))
    require("frontend/src/pages/ElectricalTopologyPage.vue", (
        'function phaseChipClass(',
        '.topology-phase-l2 { background: #111 !important;',
        '.topology-phase-l3 { background: #616161 !important;',
    ))
    require("RELEASE_NOTES_1.7.4.md", (
        'Übersicht',
        'Verkabelung',
        'Hausanschluss erscheint als Dreieck',
        'Alembic-Head bleibt `0049`',
    ))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0049_")
    print("Releasevertrag 1.7.4 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
