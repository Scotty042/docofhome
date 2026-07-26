#!/bin/sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker wurde nicht gefunden." >&2
  exit 1
fi

echo "Erzeuge frontend/package-lock.json mit Node 22.16 und npm 10 ..."
docker run --rm \
  -v "$PROJECT_ROOT/frontend:/frontend" \
  -w /frontend \
  node:22.16-alpine \
  npm install --package-lock-only --ignore-scripts --no-audit --no-fund

echo "Fertig: $PROJECT_ROOT/frontend/package-lock.json"
