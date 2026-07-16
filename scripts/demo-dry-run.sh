#!/usr/bin/env bash
# Capture a demo dry-run transcript for HyoDo public CLI (English).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OUT="${OUT:-$ROOT/docs/DEMO_DRY_RUN_LATEST.md}"
PYTHON="${PYTHON:-python3}"
if [[ -x .venv/bin/python ]]; then
  PYTHON=".venv/bin/python"
  HYODO=".venv/bin/hyodo"
elif [[ -x venv/bin/python ]]; then
  PYTHON="venv/bin/python"
  HYODO="venv/bin/hyodo"
else
  HYODO="hyodo"
fi

$PYTHON -m pip install -e ".[dev]" -q

{
  echo "# HyoDo demo dry-run"
  echo
  echo "Generated: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  echo "Branch: $(git rev-parse --abbrev-ref HEAD)"
  echo "Commit: $(git rev-parse --short HEAD)"
  echo "Version: $(tr -d '[:space:]' < VERSION)"
  echo
  echo '## hyodo --version'
  echo '```'
  $HYODO --version
  echo '```'
  echo
  echo '## hyodo check'
  echo '```'
  set +e
  $HYODO check
  CHECK_EC=$?
  set -e
  echo '```'
  echo "exit: $CHECK_EC"
  if [[ "$CHECK_EC" -ne 0 ]]; then
    echo "ERROR: hyodo check failed" >&2
    exit 1
  fi
  echo
  echo '## hyodo score'
  echo '```'
  $HYODO score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --loyalty 0.9
  echo '```'
  echo
  echo '## hyodo safe (clean tree)'
  echo '```'
  $HYODO safe || true
  echo '```'
  echo
  printf 'token = ghp_abcdefghijklmnopqrstuvwxyz012345\n' >/tmp/hyodo-demo-safe.txt
  echo '## hyodo safe (secret fixture)'
  echo '```'
  set +e
  $HYODO safe /tmp/hyodo-demo-safe.txt
  SAFE_EC=$?
  set -e
  echo '```'
  echo "exit: $SAFE_EC (non-zero expected under --strict; default may still print high risk)"
  echo
  echo '## verify-public'
  echo '```'
  bash scripts/verify-public.sh
  echo '```'
} | tee "$OUT"

echo "Wrote $OUT"
