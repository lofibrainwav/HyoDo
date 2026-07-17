#!/usr/bin/env bash
# Reproducible AFO Core development environment (Python 3.12).
#
# Single source of truth for the AFO install contract: both local development
# (default mode, isolated .venv) and CI (--system mode) must go through this
# script so that a collection failure can always be attributed to code, not to
# an ad-hoc environment (missing extras, stray pytest plugins).
#
# Usage:
#   bash afo_core/scripts/dev_env.sh            # create/update afo_core/.venv
#   bash afo_core/scripts/dev_env.sh --system   # install into current python (CI)
#   AFO_PYTHON=/path/to/python3.12 bash afo_core/scripts/dev_env.sh
set -euo pipefail

# Extras required by the full API server import graph — same set CI installs.
AFO_EXTRAS="agents,browser"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VENV_DIR="${REPO_ROOT}/afo_core/.venv"

MODE="venv"
if [ "${1:-}" = "--system" ]; then
  MODE="system"
fi

fail() {
  echo "dev_env.sh: $*" >&2
  exit 1
}

# afo_core/pyproject.toml declares requires-python = ">=3.12,<3.14".
check_python() {
  "$1" -c 'import sys; raise SystemExit(0 if (3, 12) <= sys.version_info[:2] < (3, 14) else 1)' \
    || fail "$1 is $($1 --version 2>&1) — AFO Core requires Python >=3.12,<3.14"
}

if [ "$MODE" = "system" ]; then
  PY="${AFO_PYTHON:-python}"
  command -v "$PY" >/dev/null 2>&1 || fail "python not found on PATH"
  check_python "$PY"
else
  PY="${AFO_PYTHON:-python3.12}"
  command -v "$PY" >/dev/null 2>&1 \
    || fail "$PY not found — install Python 3.12 (e.g. 'uv python install 3.12' or pyenv) or set AFO_PYTHON"
  check_python "$PY"
  # Resolve symlinks (uv/pyenv shims): a venv created through a symlink dir
  # records that dir as `home` and then fails with "No module named 'encodings'".
  PY="$("$PY" -c 'import os, sys; print(os.path.realpath(sys.executable))')"
  # Recreate the venv if it is missing or its interpreter cannot start
  # (e.g. left over from a broken symlinked-home creation).
  if ! "${VENV_DIR}/bin/python" -c 'pass' >/dev/null 2>&1; then
    "$PY" -m venv --clear "${VENV_DIR}"
  fi
  PY="${VENV_DIR}/bin/python"
  check_python "$PY"
fi

"$PY" -m pip install --upgrade pip
"$PY" -m pip install -e "${REPO_ROOT}/afo_core[${AFO_EXTRAS}]"

# Readback: fail loudly if the audited gap dependencies did not land.
"$PY" - <<'EOF'
import importlib
import sys

for name in ("certifi", "dspy", "fastapi", "pytest", "pytest_asyncio"):
    importlib.import_module(name)
print(f"afo dev env ready: python {sys.version.split()[0]} at {sys.executable}")
EOF

if [ "$MODE" = "venv" ]; then
  cat <<EOF
Activate with: source afo_core/.venv/bin/activate
Run contract tests (same files as CI afo-core-contract):
  PYTHONPATH=afo_core afo_core/.venv/bin/python -m pytest -q \\
    afo_core/tests/test_librarian_agent.py \\
    afo_core/tests/test_chancellor_v3_routers.py \\
    afo_core/tests/test_v3_routing_verification.py \\
    afo_core/tests/api/chancellor_v2/test_orchestrator.py \\
    afo_core/tests/api/test_api_pillars.py
EOF
fi
