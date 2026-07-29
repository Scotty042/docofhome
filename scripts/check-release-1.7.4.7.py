"""Verify DocOfHome 1.7.4.7 interactive wiring focus contracts."""
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


def reject(relative: str, fragments: tuple[str, ...]) -> None:
    source = read(relative)
    present = [fragment for fragment in fragments if fragment in source]
    if present:
        raise AssertionError(f"{relative}: unerwünscht: {', '.join(present)}")


def main() -> int:
    version = "1.7.4.7"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    source = json.loads(read("SOURCE_INFO.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    assert source["version"] == version
    assert source["base_version"] == "1.7.4.6"
    assert source["release_notes"] == "RELEASE_NOTES_1.7.4.7.md"
    assert source["alembic_head"] == "0049"

    require("frontend/src/components/CabinetWiringOverlay.vue", (
        "interactive?: boolean",
        "focusedEndpointKey",
        "function handlePointerOver(",
        "function handlePointerOut(",
        "function handleClick(",
        "event.key !== 'Escape'",
        "focusKey && connection.source.key !== focusKey && connection.target.key !== focusKey",
        "focusKey !== connection.target.key",
        "cabinet-wiring-focus-selected",
        "cabinet-wiring-focus-related",
        "cabinet-wiring-focus-muted",
        "function isIndividualCircuitBranch(",
        "label: 'IN'",
        "label: 'OUT'",
    ))
    require("frontend/src/pages/ElectricalDistributionLayoutPage.vue", (
        ":interactive=\"viewMode === 'overview'\"",
        "Mouse-over zeigt die direkt angeschlossene Verkabelung",
        "Klick oder Antippen fixiert sie",
        "Escape hebt die Fixierung auf",
    ))
    require("frontend/src/components/CabinetWiringOverlay.test.ts", (
        "shows direct wiring on hover and allows pinning in overview mode",
        "expect(overlay).toContain('handlePointerOver')",
        "expect(layout).toContain('Mouse-over zeigt die direkt angeschlossene Verkabelung')",
    ))
    require("RELEASE_NOTES_1.7.4.7.md", (
        "Mouse-over",
        "Klick oder Antippen",
        "automatischer Kammschienenkontakt",
        "Alembic-Head bleibt `0049`",
    ))
    reject("frontend/src/components/CabinetWiringOverlay.vue", (
        "function individualCircuitEndpointKeys(",
        "new Set(['mcb', 'rcbo'])",
    ))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0049_")
    print("Releasevertrag 1.7.4.7 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
