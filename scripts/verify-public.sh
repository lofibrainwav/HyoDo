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

echo "-- ruff --"
$PYTHON -m ruff check hyodo/ tests/ --output-format=concise
$PYTHON -m ruff format --check hyodo/ tests/

echo "-- pyright --"
$PYTHON -m pyright hyodo

echo "-- pytest --"
$PYTHON -m pytest tests -q --tb=short

echo "-- CLI smoke --"
$HYODO --version
$HYODO score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --loyalty 0.9 >/tmp/hyodo-score.out
grep -q "REVIEW_SIGNAL" /tmp/hyodo-score.out
# safe should not auto-pass secrets fixture
printf 'token = ghp_abcdefghijklmnopqrstuvwxyz012345\n' >/tmp/hyodo-safe-fixture.txt
set +e
$HYODO safe /tmp/hyodo-safe-fixture.txt >/tmp/hyodo-safe.out 2>&1
set -e
grep -Eq "secret|Risk|high|caution" /tmp/hyodo-safe.out

echo "-- claim regression (public surfaces) --"
if grep -rEn "Auto-approve|AUTO_RUN" README.md QUICK_START_SIMPLE.md SECURITY.md hyodo/cli/main.py commands/score.md commands/check.md 2>/dev/null; then
  echo "ERROR: banned auto-approve phrasing found"
  exit 1
fi

echo "== PASS: public package verify =="
