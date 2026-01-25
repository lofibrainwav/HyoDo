#!/bin/bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

TS="$(date +%Y%m%d_%H%M%S)"
mkdir -p artifacts

BASE="http://127.0.0.1:8010"

echo "=== PHASE 6 ACTION 1: API CONTRACT SNAPSHOT ==="
echo "Capturing snapshots from ${BASE}..."

curl -fsSL "${BASE}/openapi.json" > "artifacts/phase6_openapi_${TS}.json" && echo "✅ Captured: openapi.json"
curl -fsSL "${BASE}/api/health/comprehensive" > "artifacts/phase6_health_${TS}.json" && echo "✅ Captured: health/comprehensive"
curl -fsSL "${BASE}/api/skills" > "artifacts/phase6_skills_${TS}.json" && echo "✅ Captured: skills"
curl -fsSL "${BASE}/api/context7/list" > "artifacts/phase6_context7_list_${TS}.json" && echo "✅ Captured: context7/list"

python3 - <<PY
import json
from pathlib import Path
ts="${TS}"
def j(p): return json.loads(Path(p).read_text())
try:
    openapi=j(f"artifacts/phase6_openapi_{ts}.json")
    health=j(f"artifacts/phase6_health_{ts}.json")
    skills=j(f"artifacts/phase6_skills_{ts}.json")
    c7=j(f"artifacts/phase6_context7_list_{ts}.json")

    paths=len(openapi.get("paths",{}))
    organs=len((health.get("organs_v2") or health.get("organs") or {}))
    total_skills=len(skills.get("skills", skills if isinstance(skills,list) else []))
    items=len(c7.get("items", c7 if isinstance(c7,list) else []))

    out=Path(f"artifacts/phase6_contract_summary_{ts}.md")
    out.write_text(
f"""# Phase 6 Contract Snapshot
- openapi_paths: {paths}
- organs_count: {organs}
- total_skills: {total_skills}
- context7_items: {items}
""",
    encoding="utf-8"
    )
    print(f"✅ Summary generated: {out}")
except Exception as e:
    print(f"❌ Verification failed: {e}")
    exit(1)
PY
