#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

cd "$ROOT_DIR"
python scripts/check-version.py
python scripts/check-branding.py
python scripts/check-collected-fixes.py
python scripts/check-reading-reminders.py
python scripts/check-release-1.7.8.py
python scripts/check-electrical-integrity-1.6.3.py
python scripts/check-phase-rail-runtime-sync.py
python scripts/check-phase-rail-explicit-sync.py
node scripts/check-typescript-syntax.mjs
python scripts/check-migration-0030.py
python scripts/check-migration-0031.py
python scripts/check-migration-0032.py
python scripts/check-migration-0033.py
python scripts/check-migration-0034.py
python scripts/check-migration-0035.py
python scripts/check-migration-0036.py
python scripts/check-migration-0037.py
python scripts/check-migration-0039.py
python scripts/check-migration-0040.py
python scripts/check-migration-0041.py
python scripts/check-migration-0042.py
python scripts/check-migration-0043.py
python scripts/check-migration-0044.py
python scripts/check-migration-0045.py
python scripts/check-migration-0046.py
python scripts/check-migration-0047.py
python scripts/check-migration-0048.py
python scripts/check-migration-0049.py
python scripts/check-migration-0050.py
python scripts/check-migration-0051.py
python scripts/check-migration-0052.py

cd "$ROOT_DIR/backend"
ruff check app tests
mypy app
python -m pytest -q

CHECK_DATA_DIR=$(mktemp -d)
trap 'rm -rf "$CHECK_DATA_DIR"' EXIT
JARVIS_DATA_DIR="$CHECK_DATA_DIR" alembic upgrade head
JARVIS_DATA_DIR="$CHECK_DATA_DIR" alembic check

cd "$ROOT_DIR/frontend"
npm test
npm run build
