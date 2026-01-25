#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
mkdir -p artifacts

# Detect Python
PYTHON_BIN="python3"
if [ -f "packages/afo-core/.venv/bin/python" ]; then
    PYTHON_BIN="packages/afo-core/.venv/bin/python"
fi

echo "Using Python: $PYTHON_BIN"

# Install Vulture if missing
if ! "$PYTHON_BIN" -c "import vulture" >/dev/null 2>&1; then
    echo "Installing vulture..."
    "$PYTHON_BIN" -m pip install vulture
fi

# Run Vulture
{
  echo "ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  "$PYTHON_BIN" -m vulture --version || true
  echo "---"
  "$PYTHON_BIN" -m vulture packages/afo-core/AFO --min-confidence 80 || true
} > artifacts/vulture.txt

test -s artifacts/vulture.txt
echo "OK: artifacts/vulture.txt (Size: $(stat -f%z artifacts/vulture.txt) bytes)"
