#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || "${1:-}" == "" ]]; then
  cat <<'USAGE'
usage:
  ./scripts/md_to_ticket.sh <md_path> [priority] [serenity]

examples:
  ./scripts/md_to_ticket.sh docs/MIPROv2_123025_standard.md high 9
USAGE
  exit 0
fi

python3 scripts/md_to_ticket.py "$@"
