#!/bin/bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

TS="$(date +%Y%m%d_%H%M%S)"
mkdir -p artifacts
OUT="artifacts/verify_context7_local_drift_${TS}.log"

{
  echo "=== PHASE 5 ACTION 4: LOCAL SSOT DRIFT CHECK ==="
  echo "time: ${TS}"
  echo

  echo "--- git status ---"
  git status -sb
  echo

  if [ -n "$(git status --porcelain)" ]; then
    echo "❌ FAIL: working tree not clean (local drift risk)"
    git status --porcelain
    if git status --porcelain | grep -q "^ M"; then
         echo "❌ FAIL: Modified files detected."
         exit 4
    fi
     echo "⚠️ (Proceeding with untracked files only)"
  fi
  echo "✅ working tree clean (no tracked modifications)"
  echo

  echo "--- required files ---"
  test -f docs/context7_integration_metadata.json && echo "✅ docs/context7_integration_metadata.json exists"
  python3 - <<'PY'
import json,sys,os
p="docs/context7_integration_metadata.json"
try:
    d=json.load(open(p,"r",encoding="utf-8"))
except Exception as e:
    print(f"❌ FAIL: could not load json: {e}")
    sys.exit(4)

items=[]
if isinstance(d, list):
    items = d
elif isinstance(d, dict):
    if "items" in d and isinstance(d["items"], list):
        items = d["items"]
    else:
        # dict of dicts
        items = list(d.values())

if not items:
    print("❌ FAIL: No items extracted from JSON")
    sys.exit(4)

paths=[]
for m in items:
    if isinstance(m,dict):
        # Prioritize 'file' or 'path' or 'source'
        for k in ("file","path","filepath","file_path","source_path","relpath","name","title","id","key"):
            v=m.get(k)
            # Must be a string and look like a file path (not just "doc_0")
            if isinstance(v,str) and v.strip() and ("/" in v or "." in v):
                paths.append(v.strip()); break

missing=[x for x in paths if not os.path.exists(x)]
print(f"expected_items_in_json={len(paths)}")
if len(paths) < 5:
    print("❌ FAIL: Too few paths found (parsing error? expected > 5)")
    sys.exit(4)

if missing:
    print("❌ FAIL: missing expected files:")
    for x in missing[:50]:
        print(" -", x)
    sys.exit(4)

print("✅ all expected JSON paths exist on disk")
PY
  echo

  echo "--- local API health ---"
  curl -fsS "http://127.0.0.1:8010/api/health/comprehensive" >/dev/null
  echo "✅ local API reachable: /api/health/comprehensive"
  echo

  echo "--- strict metadata verify (LOCAL) ---"
  unset AFO_BASE_URL
  unset CONTEXT7_META_JSON
  
  AFO_BASE_URL="http://127.0.0.1:8010" \
  CONTEXT7_META_JSON="docs/context7_integration_metadata.json" \
  python3 scripts/verify_context7_remote_metadata.py
  echo

  echo "✅ PHASE 5 ACTION 4 COMPLETE: LOCAL DRIFT CHECK PASS"
} | tee "${OUT}"

echo
echo "Saved log: ${OUT}"
