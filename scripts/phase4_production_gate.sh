#!/usr/bin/env bash
set -euo pipefail

BASE="${AFO_BASE_URL:-http://localhost:8010}"
BASE="${BASE%/}"

echo "== Gate: health =="
curl -fsS --max-time 5 "${BASE}/api/health/comprehensive" >/tmp/health.json

python3 - <<'PY'
import json
d=json.load(open("/tmp/health.json","r",encoding="utf-8"))
keys=set(d.keys()) if isinstance(d, dict) else set()
ok = any(k in keys for k in ("organs_v2","organsV2","organs","organs_v1"))
if not ok:
  raise SystemExit("❌ health ok but organs keys missing")
print("✅ health organs keys present")
PY

echo "== Gate: skills =="
curl -fsSL --max-time 5 "${BASE}/api/skills" >/tmp/skills.json

python3 - <<'PY'
import json
d=json.load(open("/tmp/skills.json","r",encoding="utf-8"))
skills = d.get("skills") if isinstance(d, dict) else None
if not skills:
  raise SystemExit("❌ skills missing")
print("✅ skills count:", len(skills))
PY

echo "✅ PH4 Production Gate PASS"
