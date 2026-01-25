#!/usr/bin/env bash
set -euo pipefail

override="${AFO_OVERRIDE_MAIN_GATES:-0}"

fail() {
  echo "SSOT-GATE: $1"
  exit 1
}

# 1) BLOCKED gate prevents main, unless override
if rg -n "BLOCKED-SECURITY|SECURITY_PENDING|NOT SEALED" docs/reports/*.md >/dev/null 2>&1; then
  if [[ "$override" != "1" ]]; then
    fail "Found BLOCKED/SECURITY_PENDING/NOT SEALED in docs/reports. Resolve or set AFO_OVERRIDE_MAIN_GATES=1."
  fi
fi

# 2) Any artifacts/ path mentioned in reports must exist (prevents 'SEALED' without evidence)
missing=0
while IFS= read -r p; do
  [[ -z "$p" ]] && continue
  if [[ ! -e "$p" ]]; then
    echo "SSOT-GATE: Missing evidence path referenced in report: $p"
    missing=1
  fi
done < <(rg -No "artifacts/[A-Za-z0-9/_-]+" docs/reports/*.md 2>/dev/null | sort -u)

if [[ "$missing" == "1" && "$override" != "1" ]]; then
  fail "Evidence paths missing. Create artifacts folders/files or set AFO_OVERRIDE_MAIN_GATES=1 (will require justification)."
fi

exit 0
