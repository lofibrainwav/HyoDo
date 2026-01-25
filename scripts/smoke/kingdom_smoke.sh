#!/usr/bin/env bash
set -euo pipefail

SOUL_URL="${SOUL_URL:-http://127.0.0.1:8010}"
DASH_URL="${DASH_URL:-http://127.0.0.1:3000}"

curl4() {
  curl -4 -sf --retry 20 --retry-connrefused --retry-delay 1 "$@"
}

echo "[1/4] soul /health"
curl4 "${SOUL_URL}/health" >/dev/null

echo "[2/4] soul /metrics (head)"
curl4 "${SOUL_URL}/metrics" | head -n 5 >/dev/null

echo "[3/4] dashboard"
curl4 -I "${DASH_URL}" | head -n 1 >/dev/null

echo "[4/4] sse guardrail (proxy working)"
# PH20-05: SSE guardrail - Next.js 프록시가 백엔드로 제대로 연결되는지 확인
# /api/health 엔드포인트를 통해 프록시 설정 검증
if ! curl -4 -f --max-time 5 "${DASH_URL}/api/health" >/dev/null 2>&1; then
  echo "[fail] dashboard proxy not working"
  exit 1
fi
echo "[ok] dashboard proxy working"

# --- PH20-05: SSE SSOT Guardrail ---
echo "[5/6] backend legacy redirect (need 308)"
# Check Legacy Path 1: /api/stream/logs
CODE=$(curl4 -o /dev/null -w "%{http_code}" "${SOUL_URL}/api/stream/logs")
if [ "$CODE" -ne 308 ]; then
  echo "[fail] backend /api/stream/logs code=${CODE} (expected 308)"
  exit 1
fi
# Check Legacy Path 2: /api/system/logs/stream
CODE=$(curl4 -o /dev/null -w "%{http_code}" "${SOUL_URL}/api/system/logs/stream")
if [ "$CODE" -ne 308 ]; then
  echo "[fail] backend /api/system/logs/stream code=${CODE} (expected 308)"
  exit 1
fi

echo "[6/6] frontend legacy forwarding (need 200)"
# Check Legacy Path 1: /api/stream/logs -> Should be 200 OK (Forwarding)
CODE=$(curl4 -o /dev/null -w "%{http_code}" "${DASH_URL}/api/stream/logs")
if [ "$CODE" -ne 200 ]; then
  echo "[fail] frontend /api/stream/logs code=${CODE} (expected 200)"
  exit 1
fi

echo "[ok] kingdom smoke passed"