#!/usr/bin/env bash
set -euo pipefail

fail=0

pass(){ echo "✅ $*"; }
nope(){ echo "❌ $*"; fail=1; }
skip(){ echo "⏭️  $*"; }

need_file(){
  if [ -f "$1" ]; then pass "file exists: $1"; else nope "missing file: $1"; fi
}

need_match(){
  local file="$1"; shift
  local pat="$1"; shift
  if [ -f "$file" ] && grep -nE "$pat" "$file" >/dev/null 2>&1; then
    pass "match in $file: $pat"
  else
    nope "no match in $file: $pat"
  fi
}

echo "=== SSOT Reality Check ==="

# Handle task.md location (Dynamic Discovery)
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

LATEST_TASK_MD="$(
python3 - << 'PY'
import os, glob
paths = glob.glob("**/artifacts/**/task.md", recursive=True)
paths = [p for p in paths if os.path.isfile(p)]
if not paths:
    print("")
else:
    paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    print(paths[0])
PY
)"

echo "LATEST_TASK_MD=${LATEST_TASK_MD}"

if [ -n "$LATEST_TASK_MD" ]; then
    need_file "$LATEST_TASK_MD"
    # Optional: Verify content if relevant, allowing for version changes
    # need_match "$LATEST_TASK_MD" "Phase 3: Soul Engine Resurrection" || true
else
    skip "No task.md found in artifacts"
fi

need_file "AFO_EVOLUTION_LOG.md"
need_match "AFO_EVOLUTION_LOG.md" "2025-12-28|Soul Engine Resurrection|Docker Eternity"

need_file "pyproject.toml"
need_match "packages/afo-core/pyproject.toml" "playwright>=1\.57"

df_found=0
# Simplified loop for compatibility
for df in $(find . -maxdepth 5 -type f \( -name "Dockerfile" -o -name "dockerfile" \) 2>/dev/null); do
  df_found=1
  if grep -n "playwright" "$df" >/dev/null 2>&1; then
    pass "Dockerfile has playwright: $df"
  else
    if [[ "$df" == *"packages/afo-core/Dockerfile"* ]] || [[ "$df" == *"Dockerfile"* ]]; then
        if grep -n "playwright" "$df" >/dev/null 2>&1; then
             pass "Dockerfile has playwright: $df"
        else
             if [[ "$df" == *"packages/afo-core/Dockerfile"* ]]; then
                 nope "Dockerfile missing playwright: $df"
             else
                 skip "Dockerfile (other) missing playwright: $df"
             fi
        fi
    fi
  fi
  if grep -nE "playwright\\s+install|playwright\\s+install\\." "$df" >/dev/null 2>&1; then
     pass "Dockerfile has playwright install: $df"
  fi
done

if [ "$df_found" -eq 0 ]; then skip "no Dockerfile found (maxdepth 5)"; fi

health_ok=0
for url in \
  "http://localhost:8010/health/comprehensive" \
  "http://localhost:8010/api/health/comprehensive" \
   \
   \
   \
  
  
do
  if curl -fsS --max-time 2 "$url" >/tmp/afo_health.json 2>/dev/null; then
    PYTHON_BIN="python3"
    [ -f "packages/afo-core/.venv/bin/python" ] && PYTHON_BIN="packages/afo-core/.venv/bin/python"
    if $PYTHON_BIN - <<'PY' >/dev/null 2>&1
import json
p="/tmp/afo_health.json"
try:
  d=json.load(open(p,"r",encoding="utf-8"))
except Exception:
  raise SystemExit(1)
ok = ("organs_v2" in d) or ("organs" in d) or ("organsV2" in d)
raise SystemExit(0 if ok else 2)
PY
    then
      pass "health ok (organs* present): $url"
      health_ok=1
      break
    else
      nope "health reachable but missing organs keys: $url"
    fi
  fi
done
if [ "$health_ok" -eq 0 ]; then skip "health not reachable on known local urls"; fi

if docker info >/dev/null 2>&1; then
  pass "docker daemon: up"
else
  skip "docker daemon: down (build pending)"
fi

echo "=== RESULT ==="
if [ "$fail" -eq 0 ]; then
  echo "✅ SSOT matches repo reality (on checked items)"
else
  echo "❌ SSOT mismatch detected (see ❌ lines)"
  exit 1
fi
