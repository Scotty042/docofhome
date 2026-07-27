"""Verify source contracts added for DocOfHome 1.5.0."""

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
    version = read("VERSION").strip()
    version_parts = tuple(int(part) for part in version.split(".")[:3])
    if version_parts < (1, 5, 0):
        raise AssertionError("Handbuch-Vertrag benötigt mindestens Version 1.5.0")
    require(
        "frontend/src/router/handbookRoutes.ts",
        ("/wiki/handbuch", "wiki-handbook", "HandbookGlossaryPage"),
    )
    require(
        "frontend/src/App.vue",
        ("Wiki-Seiten", "Handbuch & Glossar", "to=\"/wiki/handbuch\""),
    )
    require(
        "frontend/src/pages/HandbookGlossaryPage.vue",
        (
            "Handbuch und Glossar durchsuchen",
            "Glossar A–Z",
            "Sprungmarken",
            "Änderungen an elektrischen Anlagen gehören in die Hände einer Elektrofachkraft",
            "d-md-none",
            "d-none d-md-block",
        ),
    )
    require(
        "frontend/src/content/handbook.ts",
        (
            "term: 'Asset'",
            "term: 'Sammelschiene'",
            "term: 'Phasenschiene / Kammschiene'",
            "term: 'FI / RCD'",
            "term: 'N-Schiene'",
            "term: 'VLAN'",
            "term: 'DHCP'",
            "term: 'Switch-Port'",
            "term: 'Zählerstand'",
            "filterHandbookEntries",
            "glossaryLetters",
        ),
    )
    layout = read("frontend/src/pages/ElectricalDistributionLayoutPage.vue")
    if layout.count("Asset bearbeiten") != 2:
        raise AssertionError("DIN-Detailansicht muss genau zwei Asset-Bearbeitungswege enthalten")
    passive = layout.split('<template v-else-if="detailComponent">', 1)[1].split(
        '<template v-else-if="detailAsset">', 1
    )[0]
    if "Asset bearbeiten" in passive:
        raise AssertionError("Passive Schrankkomponente zeigt einen Asset-Button")
    migrations = {item.name for item in (ROOT / "backend/migrations/versions").glob("*.py")}
    if not any(name.startswith("0036_") for name in migrations):
        raise AssertionError("Migration 0036 fehlt")
    lock = json.loads(read("frontend/package-lock.json"))
    if lock["version"] != version or lock["packages"][""]["version"] != version:
        raise AssertionError("Eigene package-lock-Metadaten stimmen nicht mit VERSION überein")
    rfdc = lock["packages"]["node_modules/rfdc"]
    if rfdc["version"] != "1.4.1":
        raise AssertionError("Transitive rfdc-Abhängigkeit wurde verändert")
    print("Release 1.5.0: statisches Handbuch, Glossar und DIN-Asset-Button vorhanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
