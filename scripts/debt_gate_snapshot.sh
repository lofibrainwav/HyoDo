#!/usr/bin/env bash
set -euo pipefail

export OUT_JSON="configs/debt_gate/baseline.json"
export TMP_OUT="$(mktemp)"

echo "🔍 Capturing Ruff error statistics..."
# Run ruff and capture statistics. Use --exit-zero to ensure we get the count even if errors exist.
poetry run ruff check . --statistics --exit-zero | tee "$TMP_OUT" >/dev/null

python3 - <<'PY'
import json, re, datetime, pathlib, os, sys

tmp_out_path = pathlib.Path(os.environ["TMP_OUT"])
out_json_path = pathlib.Path(os.environ["OUT_JSON"])

if not tmp_out_path.exists():
    print(f"❌ Temporary output not found: {tmp_out_path}")
    sys.exit(1)

txt = tmp_out_path.read_text(errors="ignore")

# Looking for "Found N errors." or "Found N errors (M fixed)."
m = re.search(r"Found\s+(\d+)\s+error", txt)
if not m:
    count = 0
    print("No errors found in ruff output.")
else:
    count = int(m.group(1))

out = {
  "ruff_errors": count,
  "created_at": datetime.datetime.now().isoformat(timespec="seconds")
}

out_json_path.parent.mkdir(parents=True, exist_ok=True)
out_json_path.write_text(json.dumps(out, indent=2) + "\n")
print(f"✅ baseline updated: {out_json_path}")
print(f"📊 ruff_errors={count}")
PY

rm -f "$TMP_OUT"
