#!/usr/bin/env bash
set -euo pipefail

TS="${TS:-$(date +%Y%m%d_%H%M%S)}"
SEAL_DIR="${SEAL_DIR:-artifacts/trinity_seals}"
AFO_BASE_URL="${AFO_BASE_URL:-http://localhost:8010}"  # 포트 수정

mkdir -p "$SEAL_DIR"

fetch_json () {
  local url="$1"
  local out="$2"
  local tmp
  tmp="$(mktemp)"
  curl -sf "$url" -o "$tmp"
  test -s "$tmp"                    # 0 bytes 감지
  python -m json.tool < "$tmp" >/dev/null  # JSON 유효성 검증
  mv "$tmp" "$out"
}

fetch_json "$AFO_BASE_URL/chancellor/rag/shadow/health" "$SEAL_DIR/rag_health_${TS}.json"
fetch_json "$AFO_BASE_URL/api/health" "$SEAL_DIR/health_${TS}.json"
fetch_json "$AFO_BASE_URL/api/5pillars/current" "$SEAL_DIR/5pillars_${TS}.json"

echo "OK: $SEAL_DIR/{rag_health,health,5pillars}_${TS}.json"
