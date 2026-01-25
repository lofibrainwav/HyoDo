#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Trinity Metrics Consistency Gate
# - Runtime: /health(trinity_score) vs /metrics(METRIC_NAME) within EPS
# - Source: ensure metric creation/set patterns exist exactly once in "active" python (exclude docs/legacy/tests)
#
# Prereqs: bash + git + curl + python3 + grep + sed + wc + tr

info()  { echo "[info] $*"; }
warn()  { echo "[warn] $*" >&2; }
error() { echo "[error] $*" >&2; }
die()   { error "$*"; exit 2; }

need_cmd() { command -v "$1" >/dev/null 2>&1 || die "missing prereq: $1"; }

curl_s() {
  # stdout: body, exit non-zero on HTTP error / connection error
  curl -fsS --max-time 10 "$1"
}

repo_root() {
  git rev-parse --show-toplevel 2>/dev/null || die "not a git repo (run from inside repo)"
}

# ----- env -----
AFO_BASE_URL="${AFO_BASE_URL:-http://localhost:8010}"
TRINITY_EPSILON="${TRINITY_EPSILON:-0.0001}"
AFO_TRINITY_METRIC_NAME="${AFO_TRINITY_METRIC_NAME:-afo_trinity_score_total}"
AFO_REQUIRE_TRINITY_METRIC="${AFO_REQUIRE_TRINITY_METRIC:-0}"   # 1이면 /metrics에 없을 때 FAIL

BASE_URL="$AFO_BASE_URL"
EPS="$TRINITY_EPSILON"
METRIC_NAME="$AFO_TRINITY_METRIC_NAME"

# excludes any path segment: docs/, legacy/, tests/
EXCLUDE_RE='(^|/)(docs|legacy|tests)/'

# ----- prereqs -----
need_cmd git
need_cmd curl
need_cmd python3
need_cmd grep
need_cmd sed
need_cmd wc
need_cmd tr

ROOT="$(repo_root)"
cd "$ROOT"

info "BASE_URL=$BASE_URL EPS=$EPS METRIC_NAME=$METRIC_NAME"
info "prereqs: bash git curl python3 grep sed wc tr"

# ----- helpers -----
git_grep_raw() {
  # prints matches (possibly empty). exit non-zero only on "real error".
  local pattern="$1"
  local out ec

  if out="$(git grep -n -E "$pattern" -- '*.py')"; then
    ec=0
  else
    ec=$?
  fi

  # git grep: 0=match, 1=no match(ok), >=2=error(fail)
  if [[ $ec -eq 1 ]]; then
    out=""
  elif [[ $ec -ne 0 ]]; then
    die "git grep failed (exit=$ec) pattern=$pattern"
  fi

  printf '%s\n' "$out"
}

filter_active_hits() {
  # input: git grep -n output lines (path:line:content...)
  # output: excludes any path with /docs/, /legacy/, /tests/ segment (or starting with those)
  python3 - "$EXCLUDE_RE" <<'PY'
import sys, re
exclude = re.compile(sys.argv[1])
for line in sys.stdin:
    line = line.rstrip("\n")
    if not line:
        continue
    path = line.split(":", 1)[0]
    if exclude.search(path):
        continue
    print(line)
PY
}

count_lines() {
  # counts non-empty lines
  sed '/^$/d' | wc -l | tr -d ' '
}

parse_health_trinity_score() {
  # reads JSON from stdin, prints score or empty
  python3 - <<'PY'
import sys, json
try:
    data = json.load(sys.stdin)
except Exception:
    print("")
    sys.exit(0)

if not isinstance(data, dict):
    print("")
    sys.exit(0)

score = None

# accept either {"trinity_score": 0.9} or {"trinity": {"trinity_score": 0.9}}
v = data.get("trinity_score")
if isinstance(v, (int, float)):
    score = float(v)
else:
    t = data.get("trinity")
    if isinstance(t, dict):
        v2 = t.get("trinity_score")
        if isinstance(v2, (int, float)):
            score = float(v2)

print("" if score is None else score)
PY
}

parse_metrics_value() {
  # stdin: /metrics text
  # stdout: either "MISSING", "MULTI", or a float number
  python3 - "$METRIC_NAME" <<'PY'
import sys, re
name = sys.argv[1]
pat = re.compile(r'^' + re.escape(name) + r'(\{| )')
vals = []
for ln in sys.stdin.read().splitlines():
    if not ln or ln.startswith("#"):
        continue
    if pat.match(ln):
        parts = ln.split()
        if len(parts) < 2:
            continue
        try:
            vals.append(float(parts[-1]))
        except Exception:
            print("PARSE_ERROR", file=sys.stderr)
            sys.exit(2)

if not vals:
    print("MISSING")
    sys.exit(0)
if len(vals) != 1:
    print("MULTI")
    sys.exit(0)

print(vals[0])
PY
}

compare_eps() {
  # args: a b eps -> prints "OK" or "FAIL"
  python3 - "$1" "$2" "$3" <<'PY'
import sys, math
a = float(sys.argv[1])
b = float(sys.argv[2])
eps = float(sys.argv[3])
d = abs(a - b)
print("OK" if d <= eps else "FAIL")
PY
}

# ----- runtime checks -----
health_json="$(curl_s "$BASE_URL/health")" || die "/health failed: $BASE_URL/health"
metrics_text="$(curl_s "$BASE_URL/metrics")" || die "/metrics failed: $BASE_URL/metrics"

health_score="$(printf '%s' "$health_json" | parse_health_trinity_score)"
if [[ -z "$health_score" ]]; then
  die "cannot read trinity_score from /health JSON (expected trinity_score or trinity.trinity_score)"
fi

metric_val="$(printf '%s\n' "$metrics_text" | parse_metrics_value)" || die "failed to parse /metrics for $METRIC_NAME"

if [[ "$metric_val" == "MULTI" ]]; then
  die "metric $METRIC_NAME has multiple time series in /metrics (expected exactly 1)"
fi

if [[ "$metric_val" == "MISSING" ]]; then
  warn "Trinity Score metric not found in /metrics (METRIC_NAME=$METRIC_NAME)"
  if [[ "$AFO_REQUIRE_TRINITY_METRIC" == "1" ]]; then
    die "AFO_REQUIRE_TRINITY_METRIC=1 but metric missing"
  fi
  info "Skipping runtime consistency check (metric missing)"
else
  verdict="$(compare_eps "$health_score" "$metric_val" "$EPS")"
  if [[ "$verdict" != "OK" ]]; then
    die "health vs metrics mismatch: health=$health_score metrics=$metric_val eps=$EPS"
  fi
  info "runtime consistency OK: health=$health_score metrics=$metric_val (eps=$EPS)"
fi

# ----- source checks (SSOT: active py only) -----
# NOTE: if METRIC_NAME is overridden to a non-canonical name, the source patterns below may not apply.
CANONICAL_METRIC="afo_trinity_score_total"
if [[ "$METRIC_NAME" != "$CANONICAL_METRIC" ]]; then
  warn "METRIC_NAME overridden ($METRIC_NAME != $CANONICAL_METRIC) → skipping source-pattern checks"
  info "check_trinity_metrics.sh PASS"
  exit 0
fi

create_pat='get_or_create_metric\(.*afo_trinity_score_total'
set_pat='trinity_score_total\.set\('

create_out="$(git_grep_raw "$create_pat" | filter_active_hits)"
echo "[debug] metric create hits (active py only):"
if [[ -n "$create_out" ]]; then echo "$create_out"; else echo "(none)"; fi
create_count="$(printf '%s\n' "$create_out" | count_lines)"
test "$create_count" = "1" || die "expected 1 create hit, got $create_count"

set_out="$(git_grep_raw "$set_pat" | filter_active_hits)"
echo "[debug] metric set hits (active py only):"
if [[ -n "$set_out" ]]; then echo "$set_out"; else echo "(none)"; fi
set_count="$(printf '%s\n' "$set_out" | count_lines)"
test "$set_count" = "1" || die "expected 1 set hit, got $set_count"

info "check_trinity_metrics.sh PASS"