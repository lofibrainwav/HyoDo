#!/usr/bin/env bash
set -euo pipefail

TS="${TS:-$(date +%Y%m%d_%H%M%S)}"
SEAL_DIR="${SEAL_DIR:-artifacts/trinity_seals}"
AFO_BASE_URL="${AFO_BASE_URL:-http://localhost:8011}"

mkdir -p "$SEAL_DIR"

curl -sf "$AFO_BASE_URL/chancellor/learning/health" \
  | tee "$SEAL_DIR/learning_health_${TS}.json" \
  | python -m json.tool >/dev/null

curl -sf "$AFO_BASE_URL/api/5pillars/current" \
  | tee "$SEAL_DIR/5pillars_${TS}.json" \
  | python -m json.tool >/dev/null

curl -sf "$AFO_BASE_URL/api/health" \
  | tee "$SEAL_DIR/health_${TS}.json" \
  | python -m json.tool >/dev/null

echo "OK: $SEAL_DIR/{learning_health,5pillars,health}_${TS}.json"
