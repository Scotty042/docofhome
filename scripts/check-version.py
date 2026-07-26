"""Verify all release-facing version sources against VERSION."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    package = (ROOT / "frontend" / "package.json").read_text(encoding="utf-8")
    lock = (ROOT / "frontend" / "package-lock.json").read_text(encoding="utf-8")
    pyproject = (ROOT / "backend" / "pyproject.toml").read_text(encoding="utf-8")
    checks = {
        "frontend/package.json": f'"version": "{version}"' in package,
        "frontend/package-lock.json": f'"version": "{version}"' in lock,
        "backend/pyproject.toml": bool(
            re.search(rf'^version\s*=\s*"{re.escape(version)}"$', pyproject, re.MULTILINE)
        ),
    }
    failures = [name for name, valid in checks.items() if not valid]
    if failures:
        print(f"Versionsabweichung zu VERSION={version}: {', '.join(failures)}")
        return 1
    print(f"Versionen konsistent: {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
