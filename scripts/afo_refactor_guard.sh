#!/usr/bin/env bash
set -euo pipefail

mode="${1:-warn}"
max_loc="${AFO_MAX_LOC:-700}"
hard_loc="${AFO_HARD_LOC:-1200}"
max_artifact_bytes="${AFO_MAX_ARTIFACT_BYTES:-10485760}"

touch docs/reports/REFACTOR_QUEUE.md

append_queue() {
  local msg="$1"
  local ts
  ts="$(date +%Y-%m-%dT%H:%M:%S%z)"
  printf "%s | %s\n" "$ts" "$msg" >> docs/reports/REFACTOR_QUEUE.md
}

# Only check staged changes (fast, deterministic)
files=$(git diff --cached --name-only || true)
[[ -z "$files" ]] && exit 0

hard_fail=0

for f in $files; do
  [[ ! -f "$f" ]] && continue

  # Large artifacts: auto-generate summary if possible
  if [[ "$f" == artifacts/* ]]; then
    size=$(wc -c < "$f" | tr -d ' ')
    if (( size > max_artifact_bytes )); then
      if command -v rg >/dev/null 2>&1; then
        if [[ "$f" == *bandit*.txt ]]; then
          sum="${f%.txt}_summary.txt"
          rg -n "Issue:|Severity:|Location:|B[0-9]{3}" "$f" > "$sum" || true
          git add "$sum" || true
          append_queue "Generated summary: $sum (from $f, ${size} bytes)"
        fi
      fi
      echo "REFAC-GUARD: large artifact detected: $f (${size} bytes)"
      if [[ "$mode" == "enforce" ]]; then
        hard_fail=1
      fi
    fi
    continue
  fi

  # Large code files: create refactor ticket entry
  if [[ "$f" == *.py || "$f" == *.ts || "$f" == *.tsx || "$f" == *.js || "$f" == *.jsx ]]; then
    loc=$(wc -l < "$f" | tr -d ' ')
    if (( loc > max_loc )); then
      append_queue "Consider refactor: $f (${loc} LOC > ${max_loc})"
      echo "REFAC-GUARD: consider refactor: $f (${loc} LOC)"
    fi
    if (( loc > hard_loc )); then
      echo "REFAC-GUARD: hard limit exceeded: $f (${loc} LOC > ${hard_loc})"
      if [[ "$mode" == "enforce" ]]; then
        hard_fail=1
      fi
    fi
  fi
done

git add docs/reports/REFACTOR_QUEUE.md >/dev/null 2>&1 || true

if [[ "$hard_fail" == "1" ]]; then
  echo "REFAC-GUARD: blocked (enforce mode). Fix large files or set AFO_OVERRIDE_MAIN_GATES=1 for emergency."
  exit 1
fi

exit 0
