"""Verify source contracts added for DocOfHome 1.4.1."""

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
    require(
        "frontend/src/pages/AboutPage.vue",
        (
            "Über DocOfHome",
            "Versionen & Changelog",
            "feedback.include_technical_info",
        ),
    )
    require(
        "frontend/src/pages/DashboardPage.vue",
        ("Zählerstände erfassen", "/consumption?capture=1"),
    )
    if "Installierte Version" in read("frontend/src/pages/DashboardPage.vue"):
        raise AssertionError("Dashboard enthält weiterhin die alte Versionskachel")
    require(
        "backend/app/services/about.py",
        (
            "RELEASE_NOTES_",
            "_check_rate_limit",
        ),
    )
    require(
        "backend/migrations/versions/0035_about_page_and_feedback.py",
        ('revision: str = "0035"', 'down_revision: str | None = "0034"'),
    )
    require("RELEASE_NOTES_1.4.1.md", ("Info-Seite", "Zählerstände erfassen"))
    require(
        "docs/VALIDATION_REPORT_1.4.1.md",
        ("Alembic-Head: `0035`", "Nicht vollständig ausführbare Prüfungen"),
    )
    require("docs/KNOWN_LIMITATIONS_1.4.1.md", ("Feedback", "Dashboard"))
    print("Release 1.4.1: Info-, Feedback- und Dashboard-Verträge vorhanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
