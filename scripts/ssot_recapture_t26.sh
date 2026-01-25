#!/usr/bin/env bash
set -euo pipefail

TS="$(date +%Y%m%d-%H%M)"
OUT="artifacts/t26/$TS"
rm -rf "$OUT"
mkdir -p "$OUT"

git diff --name-only > "$OUT/git_files_changed.txt" || true
git status --porcelain > "$OUT/git_status.txt" || true

curl -sS -D "$OUT/dashboard_headers.txt" -o /dev/null http://127.0.0.1:3000 || true

# API server calls (use 8010 as primary)
curl -sS -D "$OUT/julie_dashboard_headers.txt" -o "$OUT/julie_dashboard_body.json" \
  http://127.0.0.1:8010/api/julie/dashboard || true

# approve: side-effect 금지 → OPTIONS만
curl -sS -X OPTIONS -D "$OUT/approve_options_headers.txt" -o "$OUT/approve_options_body.txt" \
  http://127.0.0.1:8010/api/julie/transaction/approve || true

docker compose -f packages/afo-core/docker-compose.yml ps > "$OUT/docker_ps.txt" || true

python - <<PY > "$OUT/json_parse.txt" 2>&1 || true
import json, pathlib

p = pathlib.Path("artifacts/t26") / "$TS" / "julie_dashboard_body.json"
try:
    json.loads(p.read_text())
    print("JSON_PARSE_OK: julie_dashboard_body.json")
except Exception as e:
    print("JSON_PARSE_FAIL:", e)
PY

ls -la "$OUT" > "$OUT/ls_la.txt" || true
wc -c "$OUT"/* > "$OUT/bytes.txt" 2>/dev/null || true

echo "EVIDENCE_DIR=$OUT"