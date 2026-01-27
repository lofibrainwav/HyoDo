#!/bin/bash
cd .

set -euo pipefail

TS="$(date +%Y%m%d_%H%M%S)"
OUT="artifacts/antigravity/${TS}"
mkdir -p "$OUT"

git rev-parse HEAD >"$OUT/git_head.txt"
git status -sb >"$OUT/git_status.txt"
git diff --stat >"$OUT/git_diff_stat.txt" || true

python3 -V >"$OUT/python_version.txt" 2>&1 || true
which python3 >"$OUT/python_which.txt" 2>&1 || true

python3 - <<'PY' >"$OUT/chancellor_decision.json" 2>"$OUT/chancellor_err.txt" || true
import json, math, os, sys
from AFO.chancellor_graph import chancellor_graph

r = chancellor_graph.invoke("test")
d = r.get("decision", {}) if isinstance(r, dict) else {}

def f(x):
    try:
        return float(x)
    except Exception:
        return None

truth = f(d.get("pillar_scores", {}).get("truth"))
good  = f(d.get("pillar_scores", {}).get("goodness"))
beaut = f(d.get("pillar_scores", {}).get("beauty"))

calc_trinity = None
calc_risk = None
if None not in (truth, good, beaut):
    calc_trinity = (truth*0.35 + good*0.35 + beaut*0.20) * 100
    calc_risk = (1.0 - good) * 100

payload = {
    "raw_result": r,
    "derived": {
        "calc_trinity_35_35_20": round(calc_trinity, 2) if calc_trinity is not None else None,
        "calc_risk_from_goodness": round(calc_risk, 2) if calc_risk is not None else None,
        "env": {
            "AUTO_DEPLOY": os.getenv("AUTO_DEPLOY"),
            "DRY_RUN_DEFAULT": os.getenv("DRY_RUN_DEFAULT"),
            "ENVIRONMENT": os.getenv("ENVIRONMENT"),
        },
        "python": {
            "executable": sys.executable,
            "version": sys.version,
        }
    }
}
print(json.dumps(payload, indent=2, sort_keys=True))
PY

python3 - <<'PY'
import json, math, pathlib, sys

p = sorted(pathlib.Path("artifacts/antigravity").glob("*/chancellor_decision.json"))[-1]
data = json.loads(p.read_text())
r = data["raw_result"]
d = (r.get("decision", {}) if isinstance(r, dict) else {})
mode = d.get("mode")
ts = float(d.get("trinity_score"))
rs = float(d.get("risk_score"))
truth = float(d["pillar_scores"]["truth"])
good  = float(d["pillar_scores"]["goodness"])
beaut = float(d["pillar_scores"]["beauty"])

calc_ts = (truth*0.35 + good*0.35 + beaut*0.20) * 100
calc_rs = (1.0 - good) * 100

def near(a,b,eps=0.02):
    return abs(a-b) <= eps

assert mode in ("AUTO_RUN","ASK_COMMANDER","ERROR")
assert 0.0 <= ts <= 100.0 and 0.0 <= rs <= 100.0
assert 0.0 <= truth <= 1.0 and 0.0 <= good <= 1.0 and 0.0 <= beaut <= 1.0
assert near(ts, calc_ts), (ts, calc_ts)
assert near(rs, calc_rs), (rs, calc_rs)

reasons = d.get("reasons", [])
if mode == "ASK_COMMANDER":
    assert isinstance(reasons, list) and len(reasons) >= 1
print("SEAL_OK")
PY

echo "OK: $OUT"
