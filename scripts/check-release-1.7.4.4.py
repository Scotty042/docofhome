"""Verify DocOfHome 1.7.4.4 dynamic cabinet wiring contracts."""
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
    version = "1.7.4.4"
    assert read("VERSION").strip() == version
    assert f'version = "{version}"' in read("backend/pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    lock = json.loads(read("frontend/package-lock.json"))
    assert package["version"] == version
    assert lock["version"] == version and lock["packages"][""]["version"] == version
    source = json.loads(read("SOURCE_INFO.json"))
    assert source["version"] == version
    assert source["base_version"] == "1.7.4.3"
    assert source["release_notes"] == "RELEASE_NOTES_1.7.4.4.md"
    assert source["alembic_head"] == "0049"

    require("frontend/src/components/CabinetWiringOverlay.vue", (
        "function choosePort(",
        "side: 'top' | 'bottom'",
        "Verbindungen zu einer oberhalb liegenden Sammelschiene unmittelbar nach oben",
        "von unten kommende Leitungen sauber an der Unterseite",
        "const baseMidY = sy + (ty - sy) / 2",
        "const conductorOffset = (phaseIndex - center) * 8",
    ))
    reject("frontend/src/components/CabinetWiringOverlay.vue", (
        "crossSectionOrthogonalPath",
        "upper card borders as a shared trunk",
    ))
    require("frontend/src/components/CabinetWiringOverlay.test.ts", (
        "expect(overlay).toContain('function choosePort(')",
        "expect(overlay).toContain('Die Wege dürfen innerhalb des Schrankbilds verlaufen')",
    ))
    require("RELEASE_NOTES_1.7.4.4.md", (
        "direkte Aufwärtsführung",
        "Unterseiten-Anbindung",
        "Alembic-Head bleibt `0049`",
    ))
    migrations = sorted((ROOT / "backend/migrations/versions").glob("*.py"))
    assert migrations[-1].name.startswith("0049_")
    print("Releasevertrag 1.7.4.4 erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
