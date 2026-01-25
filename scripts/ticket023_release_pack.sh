#!/usr/bin/env bash
set -euo pipefail

ADAPTER_DIR="${1:?usage: $0 <adapter_dir> <train_log> [name]}"
TRAIN_LOG="${2:?usage: $0 <adapter_dir> <train_log> [name]}"
NAME="${3:-lora_adapter}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
GIT_SHA="$(cd "$ROOT" && git rev-parse HEAD 2>/dev/null || echo unknown)"

OUT="$ROOT/artifacts/ticket023_release_${NAME}_${TS}"
mkdir -p "$OUT"

if [ -f "$TRAIN_LOG" ]; then
  cp "$TRAIN_LOG" "$OUT/train.log"
fi

ls -la "$ADAPTER_DIR" > "$OUT/adapter_ls.txt" || true
du -sh "$ADAPTER_DIR" > "$OUT/adapter_size.txt" || true

if [ -d "$ADAPTER_DIR" ]; then
  find "$ADAPTER_DIR" -type f -maxdepth 3 -print0 2>/dev/null \
    | sort -z \
    | xargs -0 shasum -a 256 > "$OUT/adapter_sha256.txt"
fi

python - <<PY > "$OUT/manifest.json"
import json, os
out = ${OUT!r}
root = ${ROOT!r}
adapter_dir = ${ADAPTER_DIR!r}
train_log = ${TRAIN_LOG!r}
git_sha = ${GIT_SHA!r}
ts = ${TS!r}

def sha256_file(p):
    import hashlib
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda: f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()

m = {
  "ticket": "TICKET-023",
  "ts_utc": ts,
  "git_sha": git_sha,
  "adapter_dir": os.path.relpath(adapter_dir, root) if adapter_dir.startswith(root) else adapter_dir,
  "train_log": os.path.relpath(train_log, root) if train_log.startswith(root) else train_log,
  "files": {}
}

sha_path = os.path.join(out, "adapter_sha256.txt")
if os.path.exists(sha_path):
    m["files"]["adapter_sha256.txt"] = {"sha256": sha256_file(sha_path), "bytes": os.path.getsize(sha_path)}

man_path = os.path.join(out, "manifest.json")
m["files"]["manifest.json"] = {"bytes": 0}

print(json.dumps(m, ensure_ascii=False, separators=(",",":")))
PY

python - <<PY
import json, os
out = ${OUT!r}
p = os.path.join(out,"manifest.json")
m = json.load(open(p,"r",encoding="utf-8"))
m["files"]["manifest.json"]["bytes"] = os.path.getsize(p)
json.dump(m, open(p,"w",encoding="utf-8"), ensure_ascii=False, separators=(",",":"))
print("RELEASE_DIR="+out)
PY

ls -la "$OUT" | sed -n '1,80p'
