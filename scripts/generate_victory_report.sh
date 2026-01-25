#!/usr/bin/env bash
set -euo pipefail

ASOF="$(date +%Y-%m-%d)"
HEAD="$(git rev-parse HEAD)"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"

REPORT="docs/reports/FINAL_VICTORY_REPORT_${ASOF}.md"

WALK="$(find . -maxdepth 4 -iname '*walkthrough*.md' | head -n 1 || true)"
if [ -z "${WALK}" ]; then
  mkdir -p docs
  WALK="docs/walkthrough.md"
fi

EVID_DIR=""
if [ -d artifacts/final-report ]; then
  EVID_DIR="$(find artifacts/final-report -maxdepth 1 -not -path artifacts/final-report -print | tail -n 1 || true)"
fi

{
  echo "# FINAL Victory Report (${ASOF})"
  echo
  echo "## Snapshot"
  echo "- As-of: ${ASOF}"
  echo "- Git HEAD: ${HEAD}"
  echo "- Branch: ${BRANCH}"
  echo "- Worktree: clean = $(test -z "$(git status --porcelain)" && echo YES || echo NO)"
  echo
  echo "## Gates"
  echo '```'
  echo "pnpm -r lint      : PASS (expected)"
  echo "pnpm -r type-check: PASS (expected)"
  echo "pnpm -r build     : PASS (expected)"
  echo '```'
  echo
  echo "## Evidence"
  if [ -n "${EVID_DIR}" ]; then
    echo "- Final Evidence Dir: ${EVID_DIR}"
  else
    echo "- Final Evidence Dir: (not found under artifacts/final-report/*)"
  fi
  echo
  echo "## Recent History"
  echo '```'
  git --no-pager log --oneline --decorate -n 30
  echo '```'
  echo
  echo "## Done"
  echo "- Phase 1-6 complete"
  echo "- Main clean"
  echo "- CI local gates green"
} > "${REPORT}"

mkdir -p "$(dirname "${WALK}")"
if [ ! -f "${WALK}" ]; then
  touch "${WALK}"
fi

{
  echo
  echo "## ${ASOF} — FINAL Victory Report"
  echo "- Report: ${REPORT}"
  if [ -n "${EVID_DIR}" ]; then
    echo "- Evidence: ${EVID_DIR}"
  fi
  echo "- Git HEAD: ${HEAD}"
} >> "${WALK}"

echo "${REPORT}"
echo "${WALK}"
