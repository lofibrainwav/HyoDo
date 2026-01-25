#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

title="${1:-SSOT Restore Order}"
ts="$(python3 - <<'PY'
from datetime import datetime
print(datetime.now().astimezone().strftime("%Y%m%d_%H%M%S"))
PY
)"
out="docs/ops/SSOT_Restore_Order_${ts}.md"

branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "UNKNOWN")"
sha="$(git rev-parse --short HEAD 2>/dev/null || echo "UNKNOWN")"
now_iso="$(python3 - <<'PY'
from datetime import datetime
print(datetime.now().astimezone().isoformat(timespec="seconds"))
PY
)"

cat > "$out" <<MD

# [ORDER] ${title} (AFO Official)

## As-of

* time: ${now_iso}
* branch: ${branch}
* sha: ${sha}

## Goal

*

## DRY_RUN

\`\`\`bash
echo "== HEAD =="; git status -sb; git rev-parse --short HEAD
echo "== PORTS =="; lsof -nP -iTCP:8010 -sTCP:LISTEN || true; lsof -nP -iTCP:3000 -sTCP:LISTEN || true
echo "== HTTP =="; curl -sS --max-time 2 -I http://127.0.0.1:8010/health | head -n 5 || true; curl -sS --max-time 2 -I http://127.0.0.1:3000/ | head -n 5 || true
echo "== SSOT_VERIFY (trace) =="; bash -x ssot_verify.sh || true
echo "== PLAYWRIGHT DETECT =="; python3 -c "import importlib.util; print('playwright:', 'OK' if importlib.util.find_spec('playwright') else 'MISSING')" || true
\`\`\`

## WET (Changes)

* Target:
* Action:

## VERIFY

\`\`\`bash
bash ssot_verify.sh
python3 system_health_check.py
curl -sS --max-time 2 -I http://127.0.0.1:8010/health | head -n 5
curl -sS --max-time 2 -I http://127.0.0.1:3000/ | head -n 5
./scripts/afo_report_evidence_v1.sh
\`\`\`
MD

echo "$out"
