"""Verify source contracts added for DocOfHome 1.3.2."""

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
    require("RELEASE_NOTES_1.3.2.md", ("DocOfHome 1.3.2",))
    require(
        "backend/migrations/versions/0033_remove_legacy_single_target_topology_index.py",
        (
            'revision: str = "0033"',
            'down_revision: str | None = "0032"',
            'LEGACY_INDEX = "uq_electrical_connections_active_target"',
            "op.drop_index(LEGACY_INDEX",
        ),
    )
    require(
        "backend/app/services/electrical_topology.py",
        (
            "Diese Versorgungsverbindung ist bereits vorhanden",
            "Bitte Migration 0033 ausführen",
            "Versorgungsverbindung kollidiert mit vorhandenen Daten",
        ),
    )
    require(
        "backend/tests/test_topology_multi_source_repair_migration.py",
        (
            "test_migration_0033_repairs_already_migrated_database",
            "assert LEGACY_INDEX not in indexes",
            "assert connection.execute(",
        ),
    )
    print("Release 1.3.2: Reparatur für Mehrfacheinspeisungen vorhanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
