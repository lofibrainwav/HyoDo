#!/usr/bin/env bash
set -euo pipefail

echo "=== T26 SSOT Capture Script ==="
echo "Goal: Complete evidence for Royal Finance Widget"

# 1) Create evidence folder
TS="$(date +%Y%m%d-%H%M)"
OUT="artifacts/t26/$TS"

echo "Creating evidence folder: $OUT"
rm -rf "$OUT"
mkdir -p "$OUT"
echo "$TS" > "$OUT/timestamp.txt"

# 2) Git evidence
echo "Capturing git evidence..."
git diff --name-only > "$OUT/git_files_changed.txt" || true
git status --porcelain > "$OUT/git_status.txt" || true

# 3) Dashboard evidence (safe)
echo "Capturing dashboard evidence..."
curl -sS -D "$OUT/dashboard_headers.txt" -o /dev/null http://127.0.0.1:3000 || true

# 4) Julie dashboard API evidence
echo "Capturing Julie dashboard API evidence..."
curl -sS -D "$OUT/julie_dashboard_headers.txt" -o "$OUT/julie_dashboard_body.json" \
  http://127.0.0.1:8010/api/julie/dashboard || true

# 5) Approve endpoint evidence (OPTIONS only - no side effects)
echo "Capturing approve endpoint evidence (OPTIONS only)..."
curl -sS -X OPTIONS -D "$OUT/approve_options_headers.txt" -o "$OUT/approve_options_body.txt" \
  http://127.0.0.1:8010/api/julie/transaction/approve || true

# 6) Docker evidence
echo "Capturing docker evidence..."
docker compose -f packages/afo-core/docker-compose.yml ps > "$OUT/docker_ps.txt" || true

# 7) Generate evidence listing
ls -la "$OUT" > "$OUT/ls_la.txt" || true
wc -c "$OUT"/* > "$OUT/bytes.txt" 2>/dev/null || true

# 8) Validation check
echo "Running validation check..."
python - <<'PY'
import json, pathlib, sys

out = pathlib.Path("artifacts/t26/'$TS'")

def json_ok(p):
    try:
        json.loads(p.read_text())
        return True
    except Exception:
        return False

def has_status_line(p):
    try:
        content = p.read_text()
        return "HTTP/" in content or "200" in content or "404" in content
    except Exception:
        return False

ok = True

# Check julie_dashboard_body.json
julie_body = out/"julie_dashboard_body.json"
if not julie_body.exists() or not json_ok(julie_body):
    print("FAIL: julie_dashboard_body.json missing or not JSON")
    ok = False
else:
    data = json.loads(julie_body.read_text())
    print(f"OK: julie_dashboard_body.json parsed, keys: {list(data)[:10]}")

# Check headers have status lines
headers_files = ["dashboard_headers.txt", "julie_dashboard_headers.txt", "approve_options_headers.txt"]
for hf in headers_files:
    hp = out/hf
    if not hp.exists() or not has_status_line(hp):
        print(f"FAIL: {hf} missing or no HTTP status line")
        ok = False
    else:
        print(f"OK: {hf} has HTTP status line")

# Check docker ps
docker_ps = out/"docker_ps.txt"
if not docker_ps.exists():
    print("FAIL: docker_ps.txt missing")
    ok = False
else:
    content = docker_ps.read_text()
    if "Up" in content:
        print("OK: docker_ps.txt contains 'Up'")
    else:
        print("WARN: docker_ps.txt does not contain 'Up'")

sys.exit(0 if ok else 1)
PY

if [[ $? == 0 ]]; then
    echo "SUCCESS: T26 evidence complete"
    echo "Update docs/reports/T26_ROYAL_FINANCE_SSOT.md with:"
    echo "  - Status: SEALED (Functional Green)"
    echo "  - Evidence Directory: artifacts/t26/$TS/"
    echo "  - All Green Check: [x]"
else
    echo "FAILURE: T26 evidence incomplete"
fi

echo "EVIDENCE_DIR=$OUT"
ls -la "$OUT"