#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

title="${1:-AFO Report}"
ts="$(python3 - <<'PY'
from datetime import datetime
print(datetime.now().astimezone().strftime("%Y%m%d_%H%M%S"))
PY
)"
out="reports/AFO_REPORT_${ts}.md"

branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "UNKNOWN")"
sha="$(git rev-parse --short HEAD 2>/dev/null || echo "UNKNOWN")"
now_iso="$(python3 - <<'PY'
from datetime import datetime
print(datetime.now().astimezone().isoformat(timespec="seconds"))
PY
)"

cat > "$out" <<MD

# [REPORT] ${title} (AFO Official)

## As-of

* time: ${now_iso}
* branch: ${branch}
* sha: ${sha}

## Summary

*

## Evidence (Contract V1)

MD

./scripts/afo_report_evidence_v1.sh >> "$out"

echo "$out"
