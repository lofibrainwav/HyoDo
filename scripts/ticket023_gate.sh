#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$ROOT/artifacts/ticket023_evidence_$TS"
mkdir -p "$OUT"

RELEASE_DIR="${1:?usage: $0 <release_dir> <smoke_ssot_jsonl>}"
SMOKE_SSOT="${2:?usage: $0 <release_dir> <smoke_ssot_jsonl>}"

cd "$ROOT"
git rev-parse HEAD > "$OUT/git_sha.txt" 2>/dev/null || true
sw_vers > "$OUT/sw_vers.txt" 2>/dev/null || true
uname -a > "$OUT/uname.txt" 2>/dev/null || true

python -V > "$OUT/python_version.txt" 2>/dev/null || true
pip freeze > "$OUT/pip_freeze.txt" 2>/dev/null || true

ls -la "$RELEASE_DIR" > "$OUT/release_ls.txt"
test -s "$RELEASE_DIR/manifest.json" && echo "OK manifest.json" > "$OUT/check_manifest.txt" || echo "FAIL manifest.json" > "$OUT/check_manifest.txt"
test -s "$RELEASE_DIR/adapter_sha256.txt" && echo "OK adapter_sha256.txt" > "$OUT/check_adapter_sha256.txt" || echo "FAIL adapter_sha256.txt" > "$OUT/check_adapter_sha256.txt"

python - <<PY > "$OUT/smoke_summary.json"
import json, sys
p=${SMOKE_SSOT!r}
rows=[json.loads(x) for x in open(p,"r",encoding="utf-8") if x.strip()]
def ok(r):
  return (r["base"]["bullets"]==3 and r["lora"]["bullets"]==3 and r["base"]["kw_hit"]==6 and r["lora"]["kw_hit"]==6)
passed=sum(1 for r in rows if ok(r))
out={"cases":len(rows),"pass":passed,"fail":len(rows)-passed,"ok":(len(rows)==5 and passed==5)}
print(json.dumps(out, ensure_ascii=False, separators=(",",":")))
PY

python - <<PY > "$OUT/gate_result.json"
import json, os
out=${OUT!r}
release=${RELEASE_DIR!r}
manifest_ok=("OK" in open(os.path.join(out,"check_manifest.txt"),"r",encoding="utf-8").read())
sha_ok=("OK" in open(os.path.join(out,"check_adapter_sha256.txt"),"r",encoding="utf-8").read())
sm=json.load(open(os.path.join(out,"smoke_summary.json"),"r",encoding="utf-8"))
gate_ok=bool(manifest_ok and sha_ok and sm.get("ok") is True)
r={
  "ticket":"TICKET-023",
  "ts_utc": os.path.basename(out).replace("ticket023_evidence_",""),
  "release_dir": release,
  "smoke_ssot": ${SMOKE_SSOT!r},
  "manifest_ok": manifest_ok,
  "adapter_sha256_ok": sha_ok,
  "smoke": sm,
  "gate_ok": gate_ok
}
print(json.dumps(r, ensure_ascii=False, separators=(",",":")))
PY

echo "EVIDENCE_DIR=$OUT"
cat "$OUT/gate_result.json"
