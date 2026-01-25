#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
mkdir -p artifacts

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! "$PYTHON_BIN" -c "import vulture" >/dev/null 2>&1; then
  if command -v uv >/dev/null 2>&1; then
    uv pip install vulture
  else
    "$PYTHON_BIN" -m pip install vulture
  fi
fi

{
  echo "ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  "$PYTHON_BIN" -m vulture --version || true
  echo "---"
  "$PYTHON_BIN" -m vulture packages/afo-core/AFO --min-confidence 80 || true
} > artifacts/vulture.txt

test -s artifacts/vulture.txt
echo "OK: artifacts/vulture.txt"
