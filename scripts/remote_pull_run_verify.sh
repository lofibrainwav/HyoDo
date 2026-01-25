#!/usr/bin/env bash
set -euo pipefail

: "${AFO_IMAGE_REF:?AFO_IMAGE_REF is required (e.g., ghcr.io/<owner>/afo-core-soul-engine:<tag>)}"
AFO_PORT="${AFO_PORT:-8010}"
AFO_NAME="${AFO_NAME:-afo-core-soul-engine}"

echo "--- docker info ---"
docker info >/dev/null

echo "--- pull image ---"
docker pull "${AFO_IMAGE_REF}"

echo "--- stop/remove old container (if exists) ---"
docker rm -f "${AFO_NAME}" >/dev/null 2>&1 || true

echo "--- run ---"
docker run -d \
  --name "${AFO_NAME}" \
  --restart unless-stopped \
  -p "${AFO_PORT}:8010" \
  "${AFO_IMAGE_REF}" >/dev/null

echo "--- wait health (api/health/comprehensive) ---"
# shellcheck disable=SC2034
for i in $(seq 1 60); do
  if curl -sf "http://127.0.0.1:${AFO_PORT}/api/health/comprehensive" >/dev/null; then
    break
  fi
  sleep 2
done

TMP_PAYLOAD=$(mktemp)

echo "--- verify health payload keys ---"
curl -sfL --retry 5 --retry-delay 2 --max-time 20 "http://127.0.0.1:${AFO_PORT}/api/health/comprehensive" > "$TMP_PAYLOAD"
python3 - "$TMP_PAYLOAD" <<'PY'
import json,sys
with open(sys.argv[1], 'r') as f:
    d=json.load(f)
keys=set(d.keys())
need_any=[{"organs_v2"},{"organs"},{"organs_v2","organs"}]
ok=any(n.issubset(keys) or any(k in keys for k in n) for n in need_any)
if not ok:
  raise SystemExit(f"missing expected organs keys; got={sorted(keys)[:30]}")
print("OK: health keys present")
PY

echo "--- verify openapi paths contain core endpoints (best-effort) ---"
curl -sf "http://127.0.0.1:${AFO_PORT}/openapi.json" > "$TMP_PAYLOAD"
python3 - "$TMP_PAYLOAD" <<'PY'
import json,sys
with open(sys.argv[1], 'r') as f:
    d=json.load(f)
paths=d.get("paths",{})
s=" ".join(paths.keys())
must=["/api/skills","/api/health"]
missing=[m for m in must if m not in s]
if missing:
  raise SystemExit(f"missing core paths: {missing}")
print(f"OK: openapi paths count={len(paths)}")
PY

echo "--- verify skills list count ---"
curl -sf "http://127.0.0.1:${AFO_PORT}/api/skills" > "$TMP_PAYLOAD"
python3 - "$TMP_PAYLOAD" <<'PY'
import json,sys
with open(sys.argv[1], 'r') as f:
    d=json.load(f)
skills=d.get("skills", d if isinstance(d,list) else None)
if isinstance(skills,list):
  n=len(skills)
  if n < 1:
    raise SystemExit("skills list empty")
  print(f"OK: skills count={n}")
else:
  raise SystemExit("unexpected skills payload shape")
PY

rm -f "$TMP_PAYLOAD"
echo "=== REMOTE MCP SWEEP: PASS ==="
