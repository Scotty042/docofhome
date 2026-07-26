"""Verify source contracts added for DocOfHome 1.4.2."""

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
    require("RELEASE_NOTES_1.4.2.md", ("DocOfHome 1.4.2",))
    require(
        "backend/app/core/project_info.py",
        ("PROJECT_LINKS", "FEEDBACK_PUBLIC_SHARE_URL", "dwAsWdcZdbd8fZG"),
    )
    require(
        "backend/app/services/about.py",
        ("NextcloudPublicShareUploader", "application/zip", "_feedback_zip"),
    )
    require(
        "frontend/src/pages/AboutPage.vue",
        ("Versionen & Changelog", "öffentlichen DocOfHome-File-Drop"),
    )
    if "Impressum" in read("frontend/src/pages/AboutPage.vue"):
        raise AssertionError("Info-Seite enthält weiterhin ein Impressum")
    settings_page = read("frontend/src/pages/SettingsPage.vue")
    if "form.about" in settings_page:
        raise AssertionError("Einstellungen enthalten weiterhin pflegbare About-Felder")
    for fragment in ("const integrationMeta:", "const requiredRule ="):
        if fragment not in settings_page:
            raise AssertionError(f"SettingsPage: benötigte Integrationshilfe fehlt: {fragment}")
    require(
        "backend/migrations/versions/0036_remove_configurable_about_fields.py",
        ('revision: str = "0036"', 'down_revision: str | None = "0035"'),
    )
    require("RELEASE_NOTES_1.4.2.md", ("File Drop", "ZIP", "Impressum"))
    require(
        "docs/VALIDATION_REPORT_1.4.2.md",
        ("Alembic-Head: `0036`", "Nicht vollständig ausführbare Prüfungen"),
    )
    lock = json.loads(read("frontend/package-lock.json"))
    shared = lock["packages"]["node_modules/@vue/devtools-shared"]
    rfdc = lock["packages"]["node_modules/rfdc"]
    if shared["dependencies"]["rfdc"] != "^1.4.1":
        raise AssertionError("package-lock: falsche rfdc-Anforderung")
    if rfdc["version"] != "1.4.1":
        raise AssertionError("package-lock: nicht vorhandene rfdc-Version")
    if not rfdc["resolved"].endswith("/rfdc-1.4.1.tgz"):
        raise AssertionError("package-lock: falsche rfdc-Download-URL")
    print("Release 1.4.2: feste Projektinfos und ZIP-Feedback vorhanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
