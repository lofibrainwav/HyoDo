#!/usr/bin/env bash
# HyoDo public package verification (English)
# Does NOT install afo_core extended stack.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== HyoDo public verify =="
echo "root: $ROOT"

if [[ ! -f pyproject.toml ]] || [[ ! -d hyodo ]]; then
  echo "ERROR: run from HyoDo repo root"
  exit 1
fi

PYTHON="${PYTHON:-python3}"
BINDIR=""
if [[ -x .venv/bin/python ]]; then
  PYTHON=".venv/bin/python"
  BINDIR=".venv/bin"
elif [[ -x venv/bin/python ]]; then
  PYTHON="venv/bin/python"
  BINDIR="venv/bin"
fi

echo "python: $PYTHON ($($PYTHON --version 2>&1))"

# ensure editable install for CLI
$PYTHON -m pip install -e ".[dev]" -q

HYODO="${BINDIR:+$BINDIR/}hyodo"
if [[ ! -x "$HYODO" ]]; then
  HYODO="$PYTHON -m hyodo.cli.main"
fi
echo "hyodo: $HYODO"

echo "-- version sync --"
$PYTHON scripts/release/check_version_sync.py
EXPECTED_VERSION="$(tr -d '[:space:]' < VERSION)"

echo "-- ruff --"
$PYTHON -m ruff check hyodo/ tests/ --output-format=concise
$PYTHON -m ruff format --check hyodo/ tests/

echo "-- pyright --"
$PYTHON -m pyright --pythonpath "$PYTHON" hyodo

echo "-- pytest --"
$PYTHON -m pytest tests -q --tb=short

echo "-- shell syntax --"
bash -n install.sh
bash -n install_interactive.sh

echo "-- package build --"
rm -rf dist build
$PYTHON -m pip install -q build twine
$PYTHON -m build
$PYTHON -m twine check dist/*

echo "-- sdist must not ship afo_core --"
$PYTHON - <<'PY'
import tarfile
from pathlib import Path

sdists = list(Path("dist").glob("*.tar.gz"))
assert sdists, "no sdist found"
with tarfile.open(sdists[0]) as t:
    names = t.getnames()
bad = [n for n in names if "/afo_core/" in n or n.endswith("/afo_core")]
if bad:
    raise SystemExit(f"ERROR: sdist contains afo_core paths ({len(bad)}), e.g. {bad[:3]}")
size = sdists[0].stat().st_size
# public sdist should stay small (no advisory tree)
if size > 500_000:
    raise SystemExit(f"ERROR: sdist too large ({size} bytes); expected < 500KB without afo_core")
print(f"sdist ok: {sdists[0].name} ({size} bytes), {len(names)} entries")
PY

echo "-- wheel install smoke --"
$PYTHON -m pip install -q --force-reinstall "dist/hyodo-${EXPECTED_VERSION}-py3-none-any.whl"
$HYODO --version | grep -F "$EXPECTED_VERSION"
$PYTHON - <<PY
import hyodo
assert hyodo.__version__ == "${EXPECTED_VERSION}", hyodo.__version__
from hyodo import is_strong_review_signal, calculate_hygook_v5_score
assert is_strong_review_signal(95, 5) is True
assert is_strong_review_signal(50, 5) is False
f, s = calculate_hygook_v5_score(1, 1, 1, 1, 1)
assert round(f, 2) == 60.00 and round(s, 2) == 10.00
print("wheel import API ok")
PY

echo "-- CLI smoke --"
# reinstall editable so `hyodo check` uses the working tree sources
$PYTHON -m pip install -e ".[dev]" -q
# HyoDo checkout: expect executed gates to pass (never the false-green "All gates passed" alone)
set +e
$HYODO check >/tmp/hyodo-check.out 2>&1
CHECK_EC=$?
set -e
grep -q "All executed gates passed" /tmp/hyodo-check.out
test "$CHECK_EC" -eq 0
# Empty/non-HyoDo tree must not false-green
EMPTY_DIR="$(mktemp -d)"
set +e
$HYODO check "$EMPTY_DIR" >/tmp/hyodo-check-empty.out 2>&1
EMPTY_EC=$?
set -e
test "$EMPTY_EC" -eq 2
grep -q "No project gates were executed" /tmp/hyodo-check-empty.out
grep -q "This is not a validation pass" /tmp/hyodo-check-empty.out
if grep -q "All gates passed" /tmp/hyodo-check-empty.out; then
  echo "ERROR: false-green 'All gates passed' on empty tree"
  exit 1
fi
$HYODO score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --loyalty 0.9 >/tmp/hyodo-score.out
grep -q "REVIEW_SIGNAL" /tmp/hyodo-score.out
printf 'token = ghp_abcdefghijklmnopqrstuvwxyz012345\n' >/tmp/hyodo-safe-fixture.txt
set +e
$HYODO safe /tmp/hyodo-safe-fixture.txt >/tmp/hyodo-safe.out 2>&1
SAFE_EC=$?
$HYODO safe --strict /tmp/hyodo-safe-fixture.txt >/tmp/hyodo-safe-strict.out 2>&1
SAFE_STRICT_EC=$?
set -e
test "$SAFE_EC" -eq 0
test "$SAFE_STRICT_EC" -eq 1
grep -Eq "secret|Risk|high|caution" /tmp/hyodo-safe.out

echo "-- claim regression (public surfaces) --"
if grep -rEn "Auto-approve|AUTO_RUN|Proceed immediately|Candidate for approval" \
  README.md QUICK_START.md SECURITY.md CONTRIBUTING.md \
  RELEASE_CHECKLIST.md hyodo/cli/main.py commands/score.md commands/check.md 2>/dev/null; then
  echo "ERROR: banned auto-approve / proceed-immediately phrasing found"
  exit 1
fi

echo "== PASS: public package verify =="
