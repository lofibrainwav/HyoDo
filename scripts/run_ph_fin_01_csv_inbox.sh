#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

: "${AFO_FIN_ENABLED:=0}"
export AFO_FIN_ENABLED

PYTHONPATH="$ROOT/packages/afo-core:${PYTHONPATH:-}" \
python3 -m AFO.julie_cpa.csv_inbox_labeler "$@"
