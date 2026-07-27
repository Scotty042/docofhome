"""Fail when visible DocOfHome surfaces contain legacy product branding."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
LEGACY = re.compile(r"\bTectoryn\b|(?<![A-Za-z0-9_])JARVIS(?![A-Za-z0-9_])")
LOWERCASE_BRAND = re.compile(r"\bdocofhome\b")
CENTRAL_DOCS = [
    ROOT / "README.md",
    ROOT / "PROJECT_STATUS.md",
    ROOT / "ROADMAP.md",
    ROOT / "CHANGELOG.md",
    ROOT / "RELEASE_NOTES_1.0.0.md",
    ROOT / "docs" / "MIGRATION_GUIDE_1.0.0.md",
    ROOT / "docs" / "KNOWN_LIMITATIONS_1.0.0.md",
]


def line_hits(path: Path, content: str, pattern: re.Pattern[str]) -> list[str]:
    return [
        f"{path.relative_to(ROOT)}:{number}: {line.strip()}"
        for number, line in enumerate(content.splitlines(), 1)
        if pattern.search(line)
    ]


def main() -> int:
    failures: list[str] = []
    for path in (ROOT / "frontend" / "src").rglob("*.vue"):
        content = path.read_text(encoding="utf-8")
        template = content.split("<template>", 1)[-1] if "<template>" in content else content
        failures.extend(line_hits(path, template, LEGACY))
        failures.extend(line_hits(path, template, LOWERCASE_BRAND))
    for path in CENTRAL_DOCS:
        content = path.read_text(encoding="utf-8")
        failures.extend(line_hits(path, content, LEGACY))
        failures.extend(line_hits(path, content, LOWERCASE_BRAND))
    branding = (ROOT / "frontend" / "src" / "config" / "branding.ts").read_text(
        encoding="utf-8"
    )
    index = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    main_app = (ROOT / "backend" / "app" / "main.py").read_text(encoding="utf-8")
    if "APP_NAME = 'DocOfHome'" not in branding:
        failures.append("frontend/src/config/branding.ts: APP_NAME ist nicht DocOfHome")
    if "<title>DocOfHome</title>" not in index:
        failures.append("frontend/index.html: Seitentitel ist nicht DocOfHome")
    if 'title="DocOfHome API"' not in main_app:
        failures.append("backend/app/main.py: FastAPI-Titel ist nicht DocOfHome API")
    if failures:
        print("Sichtbare Branding-Verstöße:")
        print("\n".join(failures))
        return 1
    print("Branding geprüft: sichtbarer Produktname ist DocOfHome.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
