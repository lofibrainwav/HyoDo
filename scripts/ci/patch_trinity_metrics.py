#!/usr/bin/env python3
from pathlib import Path

script = Path("scripts/ci/check_trinity_metrics.sh")
doc = Path("docs/SSOT_METRICS_TRINITY_SCORE.md")

if not script.exists():
    raise SystemExit("missing: scripts/ci/check_trinity_metrics.sh")
if not doc.exists():
    raise SystemExit("missing: docs/SSOT_METRICS_TRINITY_SCORE.md")

s = script.read_text(encoding="utf-8")

# 1) METRIC_NAME env override
old = 'METRIC_NAME="afo_trinity_score_total"\n'
new = 'METRIC_NAME="${AFO_TRINITY_METRIC_NAME:-afo_trinity_score_total}"\n'
if old in s:
    s = s.replace(old, new, 1)

# 2) Health JSON parsing harden (dict type check 포함)
# 기존 블록을 안전하게 치환 (정확히 매칭되는 경우만)
needle = """HEALTH_VALUE="$(
  printf '%s' "$HEALTH_RAW" | python3 - <<'PY'
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    print("0")
    raise SystemExit(0)

v = 0.0
try:
    v = float((data.get("trinity") or {}).get("trinity_score") or 0.0)
except Exception:
    v = 0.0
print(v)
PY
)"
"""
replacement = """HEALTH_VALUE="$(
  printf '%s' "$HEALTH_RAW" | python3 - <<'PY'
import json, sys

try:
    data = json.load(sys.stdin)
except Exception:
    print("0")
    raise SystemExit(0)

try:
    tr = data.get("trinity") if isinstance(data, dict) else None
    tr = tr if isinstance(tr, dict) else {}
    v = tr.get("trinity_score", 0.0)
    print(float(v))
except Exception:
    print("0")
PY
)"
"""
if needle in s:
    s = s.replace(needle, replacement, 1)

script.write_text(s, encoding="utf-8")

d = doc.read_text(encoding="utf-8")
if "AFO_TRINITY_METRIC_NAME" not in d:
    d = d.replace(
        "## 환경 변수\n- `AFO_BASE_URL` (기본: `http://localhost:8010`)\n- `TRINITY_EPSILON` (기본: `0.0001`)\n",
        "## 환경 변수\n- `AFO_BASE_URL` (기본: `http://localhost:8010`)\n- `TRINITY_EPSILON` (기본: `0.0001`)\n- `AFO_TRINITY_METRIC_NAME` (기본: `afo_trinity_score_total`)\n",
        1,
    )
doc.write_text(d, encoding="utf-8")

print("[ok] patched:")
print(" - scripts/ci/check_trinity_metrics.sh")
print(" - docs/SSOT_METRICS_TRINITY_SCORE.md")
