#!/usr/bin/env bash
set -euo pipefail

# AFO Kingdom Port Guard
# Usage: ./port_guard.sh <port> [pattern]
# Example: ./port_guard.sh 8010 'uvicorn|python'

PORT="${1:-}"
PATTERN="${2:-}"

if [[ -z "${PORT}" ]]; then
  echo "usage: scripts/port_guard.sh <port> [pattern]"
  exit 2
fi

# Check if port is in use
PIDS="$(lsof -ti "tcp:${PORT}" 2>/dev/null || true)"
if [[ -z "${PIDS}" ]]; then
  echo "[OK] port ${PORT} is free"
  exit 0
fi

echo "[WARN] port ${PORT} is in use:"
lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN || true

# If pattern is provided, verify process command
if [[ -n "${PATTERN}" ]]; then
  MATCHED=""
  while read -r pid; do
    if [[ -z "$pid" ]]; then continue; fi
    cmd="$(ps -o command= -p "${pid}" 2>/dev/null || true)"
    if echo "${cmd}" | grep -Eiq "${PATTERN}"; then
      MATCHED="${MATCHED} ${pid}"
    fi
  done <<< "${PIDS}"

  # Trim leading whitespace
  MATCHED="$(echo "${MATCHED}" | xargs)"

  if [[ -z "${MATCHED}" ]]; then
    echo "[BLOCK] pattern '${PATTERN}' did not match any process. Not killing."
    exit 1
  fi

  PIDS="${MATCHED}"
fi

echo "[ACTION] sending TERM to:${PIDS}"
# Use word splitting for PIDS
# shellcheck disable=SC2086
kill -TERM ${PIDS} 2>/dev/null || true
sleep 2

# Check if still alive
STILL="$(lsof -ti "tcp:${PORT}" 2>/dev/null || true)"
if [[ -n "${STILL}" ]]; then
  echo "[ACTION] sending KILL to:${STILL}"
  # shellcheck disable=SC2086
  kill -KILL ${STILL} 2>/dev/null || true
fi

echo "[OK] port ${PORT} cleared"
