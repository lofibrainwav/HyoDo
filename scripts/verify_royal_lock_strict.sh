#!/bin/bash
set -euo pipefail

echo "🏰 Starting Strict Royal Lock Verification..."

# 1. UV Sync
echo "📦 Verifying dependencies (uv sync --frozen)..."
uv sync --frozen

# 2. Import Check
echo "🐍 Verifying AFO import naming..."
env -u PYTHONPATH uv run python - <<'PY'
import importlib.util as u
import sys
try:
    A = u.find_spec("AFO")
    a = u.find_spec("afo")
    print(f"AFO spec: {A}")
    print(f"afo spec: {a}")
    assert A is not None, "AFO package not found"
    assert a is None, "Lowercase 'afo' package found (Should be 'AFO')"
    print("✅ Import Check Passed")
except Exception as e:
    print(f"❌ Import Check Failed: {e}")
    sys.exit(1)
PY

# 3. Ruff Check
echo "⚡ Running Ruff (Check)..."
ruff check packages scripts --ignore E402,B007,F841,B904,C901,A001,N806,I001 || { echo "❌ Ruff Check Failed"; exit 1; }

# 4. Ruff Format
echo "🎨 Running Ruff (Format Check)..."
ruff format --check packages scripts || { echo "❌ Ruff Format Failed"; exit 1; }

# 5. Pyright
echo "📘 Running Pyright..."
uv run pyright || { echo "❌ Pyright Failed"; exit 1; }

# 6. Pytest
echo "🧪 Running Pytest..."
uv run pytest -q || { echo "❌ Pytest Failed"; exit 1; }

# 7. CI Hardening Gate
if [ -f "./scripts/ci_hardening_gate.sh" ]; then
    echo "🛡️ Running CI Hardening Gate..."
    bash -x ./scripts/ci_hardening_gate.sh || { echo "❌ CI Gate Failed"; exit 1; }
fi

echo "🏆 ROYAL LOCK VERIFICATION PASSED (All 0 exit)"
