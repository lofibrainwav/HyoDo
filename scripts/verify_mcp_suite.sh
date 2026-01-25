#!/usr/bin/env bash
set -euo pipefail

BASE="${AFO_BASE_URL:-http://localhost:8010}"
BASE="${BASE%/}"

echo "== MCP SUITE: BASE=$BASE =="

echo "== 1) Health gate =="
# Follow redirects with -L
curl -fsSL --max-time 20 "$BASE/api/health/comprehensive" >/tmp/health.json
python3 - <<'PY'
import json
try:
    d=json.load(open("/tmp/health.json","r",encoding="utf-8"))
    keys=set(d.keys()) if isinstance(d, dict) else set()
    ok = any(k in keys for k in ("organs_v2","organsV2","organs","organs_v1"))
    if not ok:
        print(f"❌ health keys: {keys}")
        raise SystemExit("❌ health OK but organs keys missing")
    print("✅ health organs keys present")
except Exception as e:
    print(f"❌ Health Check Failed: {e}")
    raise SystemExit(1)
PY

echo "== 2) OpenAPI discovery (what exists) =="
curl -fsSL --max-time 5 "$BASE/openapi.json" >/tmp/openapi.json
python3 - <<'PY'
import json
try:
    o=json.load(open("/tmp/openapi.json","r",encoding="utf-8"))
    paths=o.get("paths",{}) if isinstance(o, dict) else {}
    keys=sorted(paths.keys())
    def count_kw(kw):
        return sum(1 for p in keys if kw in p)
    print("paths:", len(keys))
    for kw in ["/api/skills","context7","council","gen-ui","mcp","logs","health"]:
        print(f"contains '{kw}':", count_kw(kw))
except Exception as e:
    print(f"❌ OpenAPI parsing failed: {e}")
PY

echo "== 3) Skills list gate =="
curl -fsSL --max-time 5 "$BASE/api/skills" >/tmp/skills.json
python3 - <<'PY'
import json
try:
    d=json.load(open("/tmp/skills.json","r",encoding="utf-8"))
    skills=d.get("skills") if isinstance(d, dict) else None
    if not skills:
        raise SystemExit("❌ skills missing")
    print("✅ skills count:", len(skills))
except Exception as e:
    print(f"❌ Skills Check Failed: {e}")
    raise SystemExit(1)
PY

echo "== 4) Known verification scripts (if present) =="
run_py () {
  local f="$1"
  if [ -f "$f" ]; then
    echo "-> python $f"
    python3 "$f"
  elif [ -f "scripts/$f" ]; then
    echo "-> python scripts/$f"
    python3 "scripts/$f"
  else
    echo "-> skip (missing): $f"
  fi
}

run_py "mcp_smoke_test_afo_skills.py"
run_py "verify_all_skills_trinity_score.py"
run_py "scripts/verify_context7_refine.py"

if [ -f "scripts/demo_mcp_execute.py" ]; then
  echo "-> python scripts/demo_mcp_execute.py"
  python3 scripts/demo_mcp_execute.py
else
  echo "-> skip (missing): scripts/demo_mcp_execute.py"
fi

echo "✅ MCP SUITE PASS"
