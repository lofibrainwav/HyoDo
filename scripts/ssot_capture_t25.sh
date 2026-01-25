#!/usr/bin/env bash
set -euo pipefail

echo "=== T25 SSOT Capture Script ==="
echo "Goal: Close security gate (bandit clean) + update evidence"

# 1) Create single timestamp folder
TS="$(date +%Y%m%d-%H%M)"
OUT="artifacts/t25/$TS"

echo "Creating evidence folder: $OUT"
rm -rf "$OUT"
mkdir -p "$OUT"
echo "$TS" > "$OUT/timestamp.txt"

# 2) Bandit scan (our code only)
echo "Running bandit scan..."
python -m bandit -r packages/afo-core \
  -x ".venv,venv,node_modules,dist,build,.next,__pycache__,site-packages" \
  -f txt -n 999 -lll \
  > "$OUT/bandit.txt" 2>&1

echo $? > "$OUT/bandit_exitcode.txt"

# Generate summary for review
rg -n "Issue:|Severity:|Location:|B[0-9]{3}" "$OUT/bandit.txt" \
  > "$OUT/bandit_summary.txt" || true

# Gzip large bandit file if needed
python - <<'PY'
import os, gzip, shutil, pathlib
p = pathlib.Path("artifacts/t25/'$TS'/bandit.txt")
if p.exists():
    size = p.stat().st_size
    if size > 10_000_000:
        gz = p.with_suffix(".txt.gz")
        with open(p, "rb") as f_in, gzip.open(gz, "wb", compresslevel=6) as f_out:
            shutil.copyfileobj(f_in, f_out)
        print(f"GZ_CREATED {gz.as_posix()} SIZE {gz.stat().st_size} FROM {size}")
    else:
        print(f"BANDIT_SIZE_OK {size}")
PY

# 3) Functional evidence capture
echo "Capturing functional evidence..."

# Health
curl -sS -L http://127.0.0.1:8010/health > "$OUT/health_body.json" || true
curl -sS -D "$OUT/health_headers.txt" -o /dev/null http://127.0.0.1:8010/health || true

# Skills
curl -sS -L http://127.0.0.1:8010/api/skills > "$OUT/skills_body.json" || true
curl -sS -D "$OUT/skills_headers.txt" -o /dev/null http://127.0.0.1:8010/api/skills || true

# Docker
docker compose -f packages/afo-core/docker-compose.yml ps > "$OUT/docker_ps.txt" || true

# 4) Generate evidence listing
ls -la "$OUT" > "$OUT/ls_la.txt" || true
wc -c "$OUT"/* > "$OUT/bytes.txt" 2>/dev/null || true

# 5) Validation check
echo "Running validation check..."
python - <<'PY'
import json, pathlib, sys

out = pathlib.Path("artifacts/t25/'$TS'")
exitcode = int((out/"bandit_exitcode.txt").read_text().strip() or "999")

def json_ok(p):
    try:
        json.loads(p.read_text())
        return True
    except Exception:
        return False

ok = True

if exitcode != 0:
    print(f"FAIL: bandit_exitcode != 0 => {exitcode}")
    ok = False
else:
    print("OK: bandit exit 0")

hb = out/"health_body.json"
sb = out/"skills_body.json"
if not hb.exists() or not json_ok(hb):
    print("FAIL: health_body.json missing or not json")
    ok = False
else:
    data = json.loads(hb.read_text())
    print(f"OK: health json keys: {list(data)[:10]}")

if not sb.exists() or not json_ok(sb):
    print("FAIL: skills_body.json missing or not json")
    ok = False
else:
    data = json.loads(sb.read_text())
    if isinstance(data, dict) and ("skills" in data or "total" in data):
        print("OK: skills json looks dict-like")
    elif isinstance(data, list):
        print(f"OK: skills json list len: {len(data)}")
    else:
        print(f"WARN: skills json unknown shape: {type(data).__name__}")

sys.exit(0 if ok else 1)
PY

if [[ $? == 0 ]]; then
    echo "SUCCESS: T25 ready for DONE status"
    echo "Update docs/reports/T25_STABILIZATION_SSOT.md with:"
    echo "  - Status: DONE (Green 4-set)"
    echo "  - Evidence Directory: artifacts/t25/$TS/"
    echo "  - All Green Check: [x]"
else
    echo "FAILURE: T25 still BLOCKED - check bandit issues"
fi

echo "EVIDENCE_DIR=$OUT"
ls -la "$OUT"