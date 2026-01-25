#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT/packages/afo-core${PYTHONPATH+:$PYTHONPATH}"
export AFO_API_BASE_URL="${AFO_API_BASE_URL:-http://127.0.0.1:8010}"
export PYTHONUNBUFFERED=1

exec "$ROOT/.venv-mcp/bin/python" -m AFO.mcp.afo_skills_mcp
