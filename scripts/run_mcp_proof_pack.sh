#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

TICKET="MCP"
TS="$(date +'%Y%m%d-%H%M%S')"
OUTDIR="$ROOT/artifacts/$TICKET/$TS"
mkdir -p "$OUTDIR"

AFO_API_BASE_URL="${AFO_API_BASE_URL:-http://127.0.0.1:8010}"
DASH_URL="${DASH_URL:-http://127.0.0.1:3000}"

PY_MCP="$ROOT/.venv-mcp/bin/python"
if [[ ! -x "$PY_MCP" ]]; then
  PY_MCP="$(command -v python3 || true)"
fi

{
  echo "ticket=$TICKET"
  echo "ts=$TS"
  echo "root=$ROOT"
  echo "python=$PY_MCP"
  echo "AFO_API_BASE_URL=$AFO_API_BASE_URL"
  echo "DASH_URL=$DASH_URL"
  echo "git_head=$(git rev-parse HEAD 2>/dev/null || true)"
  echo "git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
} > "$OUTDIR/meta.txt"

(lsof -nP -iTCP:3000 -sTCP:LISTEN || true) > "$OUTDIR/port_3000.txt"
(lsof -nP -iTCP:8010 -sTCP:LISTEN || true) > "$OUTDIR/port_8010.txt"

curl -sS -D - "$DASH_URL" -o /dev/null > "$OUTDIR/dashboard_headers.txt" || true
curl -sS -D - "$AFO_API_BASE_URL" -o /dev/null > "$OUTDIR/afo_api_headers.txt" || true

if [[ -f "$ROOT/scripts/mcp_smoke_stdio_v2.py" ]]; then
  PYTHONPATH="$ROOT/packages/afo-core${PYTHONPATH+:$PYTHONPATH}" \
  AFO_API_BASE_URL="$AFO_API_BASE_URL" \
  "$PY_MCP" -u "$ROOT/scripts/mcp_smoke_stdio_v2.py" > "$OUTDIR/mcp_smoke.txt" 2>&1 || true
else
  printf "missing: scripts/mcp_smoke_stdio_v2.py\n" > "$OUTDIR/mcp_smoke.txt"
fi

SEAL_FILES=(
  "$OUTDIR/verify_pass.txt"
  "$OUTDIR/seal.json"
  "$OUTDIR/dashboard_headers.txt"
  "$OUTDIR/mcp_smoke.txt"
)

python3 - << 'PY' "$OUTDIR"
import hashlib, json, os, sys
outdir = sys.argv[1]
def sha256(p):
  h = hashlib.sha256()
  with open(p, "rb") as f:
    for b in iter(lambda: f.read(1024*1024), b""):
      h.update(b)
  return h.hexdigest()
manifest = {}
for name in ["dashboard_headers.txt","mcp_smoke.txt","meta.txt","port_3000.txt","port_8010.txt","afo_api_headers.txt"]:
  p = os.path.join(outdir, name)
  if os.path.exists(p):
    manifest[name] = {"bytes": os.path.getsize(p), "sha256": sha256(p)}
seal_path = os.path.join(outdir, "seal.json")
with open(seal_path, "w", encoding="utf-8") as f:
  json.dump({"ticket":"MCP","outdir":outdir,"files":manifest}, f, indent=2, ensure_ascii=False)
print(seal_path)
PY

PASS=1
HDR_BYTES="$(wc -c < "$OUTDIR/dashboard_headers.txt" 2>/dev/null || echo 0)"
if [[ "$HDR_BYTES" -le 0 ]]; then PASS=0; fi

if ! grep -q "HTTP/" "$OUTDIR/dashboard_headers.txt" 2>/dev/null; then PASS=0; fi
if ! grep -q "OK: tools/list" "$OUTDIR/mcp_smoke.txt" 2>/dev/null; then PASS=0; fi
if ! grep -q "PASS: clean exit (0)" "$OUTDIR/mcp_smoke.txt" 2>/dev/null; then PASS=0; fi

if [[ "$PASS" -eq 1 ]]; then
  echo "PASS" > "$OUTDIR/verify_pass.txt"
else
  echo "FAIL" > "$OUTDIR/verify_pass.txt"
fi

REQ=(
  "$OUTDIR/verify_pass.txt"
  "$OUTDIR/seal.json"
  "$OUTDIR/dashboard_headers.txt"
  "$OUTDIR/mcp_smoke.txt"
)

MISSING=0
for f in "${REQ[@]}"; do
  if [[ ! -f "$f" ]]; then
    MISSING=1
  fi
done

if [[ "$MISSING" -eq 1 ]]; then
  echo "FAIL" > "$OUTDIR/verify_pass.txt"
fi

echo "$OUTDIR"
