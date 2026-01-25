#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

fail() { echo "FILIAL_HARD_LOCK_FAIL: $1" >&2; exit 1; }

# Env flags (common .env targets)
ENV_FILES=()
[ -f "packages/afo-core/.env" ] && ENV_FILES+=("packages/afo-core/.env")
[ -f ".env" ] && ENV_FILES+=(".env")
[ -f ".env.local" ] && ENV_FILES+=(".env.local")
[ -f ".env.production" ] && ENV_FILES+=(".env.production")

for f in "${ENV_FILES[@]}"; do
  if grep -Eiq '^\s*EXTERNAL_EXPOSURE_ENABLED\s*=\s*true\s*$' "$f"; then fail "$f sets EXTERNAL_EXPOSURE_ENABLED=true"; fi
  if grep -Eiq '^\s*EXTERNAL_API_ENABLED\s*=\s*true\s*$' "$f"; then fail "$f sets EXTERNAL_API_ENABLED=true"; fi
  if grep -Eiq '^\s*PUBLIC_ENDPOINTS_ENABLED\s*=\s*true\s*$' "$f"; then fail "$f sets PUBLIC_ENDPOINTS_ENABLED=true"; fi
  if grep -Eiq '^\s*AFO_DRY_RUN_DEFAULT\s*=\s*false\s*$' "$f"; then fail "$f sets AFO_DRY_RUN_DEFAULT=false"; fi
done

# Code/config scans (exclude docs/evidence to avoid false positives)
PATTERN='CORS\s*\*|Access-Control-Allow-Origin:\s*\*|allow_origins=\["\*"\]|ALLOW_ALL_ORIGINS'

HITS="$(git grep -nE "$PATTERN" -- \
  . \
  ':(exclude)docs/**' \
  ':(exclude)docs/ssot/**' \
  ':(exclude)docs/phase_14_b_preparation/**' \
  ':(exclude)artifacts/**' \
  ':(exclude)**/*.md' \
  ':(exclude)**/*.txt' \
  ':(exclude)**/*.bak*' \
  ':(exclude)scripts/**' \
  ':(exclude)**/*.log' \
  ':(exclude)**/*.json' || true)"

if [ -n "$HITS" ]; then
  echo "$HITS" >&2
  fail "forbidden external-exposure trigger found"
fi

echo "FILIAL_HARD_LOCK_OK"
