#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AFO_BASE_URL:-http://localhost:8010}"
SENSITIVE_PATH="${AFO_TEST_SENSITIVE_PATH:-/api/wallet/keys}"
GENERAL_PATH="${AFO_TEST_GENERAL_PATH:-/health}"

echo "🧪 Starting Phase 2.6 Policy Verification (Circuit Breaker Edition)..."
echo "[1/6] Base URL: ${BASE_URL}"
echo "[2/6] Stopping redis..."
# Use direct container name to ensure kill
docker stop afo-redis >/dev/null 2>&1 || true
count=0
while docker ps | grep -q "afo-redis"; do
  echo "Waiting for Redis to stop..."
  sleep 1
  count=$((count+1))
  if [ $count -ge 10 ]; then
    echo "❌ Failed to stop Redis!"
    exit 1
  fi
done
echo "Redis stopped confirmed."

echo
echo "[3/6] Sensitive request (expect 503/429 + X-AFO-Redis-Down + X-AFO-Redis-CB-State): ${SENSITIVE_PATH}"
curl -isS "${BASE_URL}${SENSITIVE_PATH}" | head -n 25

echo
echo "[4/6] General request (expect NOT fail-closed; should include X-AFO-Redis-Down: 1): ${GENERAL_PATH}"
curl -isS "${BASE_URL}${GENERAL_PATH}" | head -n 30

echo
echo "[5/6] Starting redis..."
docker compose start afo-redis >/dev/null 2>&1 || true
sleep 2

echo
echo "[6/6] General request again (expect Redis-Down header absent): ${GENERAL_PATH}"
curl -isS "${BASE_URL}${GENERAL_PATH}" | head -n 30

echo "OK"
