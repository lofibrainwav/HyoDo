#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PARENT_DIR="$(dirname "$ROOT_DIR")"
cd "$ROOT_DIR"

echo "Running ruff..."
python -m ruff check .

echo "Running pytest..."
python -m pytest

echo "Running mypy (AFO package, ignoring missing imports/excluded duplicates)..."
(cd "$PARENT_DIR" && python -m mypy --ignore-missing-imports --exclude 'api_wallet\\.py' -p AFO)
