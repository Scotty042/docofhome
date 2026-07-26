"""Verify source contracts added for DocOfHome 1.4.0."""

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
    require("RELEASE_NOTES_1.4.0.md", ("DocOfHome 1.4.0",))
    require(
        "backend/app/models/electrical.py",
        (
            "linked_rcd_device_id",
            "start_phase",
            "assigned_rcd_id",
            "neutral_rail_id",
        ),
    )
    require(
        "backend/app/services/electrical.py",
        (
            "def _busbar_phase_pattern",
            "effective_rcd_id",
            "effective_neutral_rail_id",
            "Mehrere Sammelschienen überdecken",
            "Das Gerät ragt über das Ende der Sammelschiene hinaus",
        ),
    )
    require(
        "frontend/src/pages/ElectricalDistributionLayoutPage.vue",
        (
            "Kompakt",
            "Erweitert",
            "busbar-card",
            "Zugehöriger FI/RCD",
            "Startphase",
            "Noch nicht platzierte DIN-Assets",
            "detailDrawer",
        ),
    )
    require(
        "frontend/src/services/electricalPresentation.ts",
        ("export function busbarPhasePattern", "component.start_phase"),
    )
    require(
        "docs/VALIDATION_REPORT_1.4.0.md",
        ("Alembic-Head: `0034`", "Nicht vollständig ausführbare Prüfungen"),
    )
    require(
        "backend/migrations/versions/0034_home_electrical_groups.py",
        (
            'revision: str = "0034"',
            'down_revision: str | None = "0033"',
            'batch.add_column(sa.Column("assigned_rcd_id"',
            'batch.add_column(sa.Column("neutral_rail_id"',
        ),
    )
    print("Release 1.4.0: Sammelschienen-, FI-, N-Schienen- und UI-Verträge vorhanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
