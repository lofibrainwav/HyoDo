#!/usr/bin/env bash
set -euo pipefail
reason="${1:-}"
[[ -z "$reason" ]] && { echo "Usage: scripts/afo_override_justify.sh \"reason\""; exit 1; }

ts="$(date +%Y%m%d-%H%M)"
f="docs/reports/OVERRIDE_${ts}.md"
cat > "$f" <<EOF
# Override Justification
Timestamp: $ts
Reason: $reason

## What was overridden
- SSOT gates / refactor gates

## Required follow-up
- Create a ticket to remove override condition
- Add missing evidence / fix security / refactor large file
EOF

git add "$f"
echo "Wrote: $f"
