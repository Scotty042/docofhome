#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

cd "$ROOT_DIR"
python scripts/check-release-1.2.4.py
python scripts/check-release-1.3.0.py
python scripts/check-release-1.3.1.py
python scripts/check-release-1.3.2.py
python scripts/check-release-1.4.0.py
python scripts/check-release-1.4.1.py
python scripts/check-release-1.4.2.py
python scripts/check-release-1.5.0.py
python scripts/check-migration-0030.py
python scripts/check-migration-0031.py
python scripts/check-migration-0032.py
python scripts/check-migration-0033.py
python scripts/check-migration-0034.py
python scripts/check-migration-0035.py
python scripts/check-migration-0036.py

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
