#!/usr/bin/env bash
set -euo pipefail

say() { printf "%s\n" "$*"; }
ok()  { say "[OK]  $*"; }
warn(){ say "[WARN] $*"; }
fail(){ say "[FAIL] $*"; exit 1; }

say "== AFO DAILY ROLL CALL =="
say "time: $(date -Iseconds)"
say "root: $(git rev-parse --show-toplevel)"
say

say "== 1) GIT STATE =="
git status -sb
if ! git diff --quiet || ! git diff --cached --quiet; then
  fail "Working tree dirty"
fi
ok "working tree clean"
say

say "== 2) CI LOCK (optional) =="
if [ "${RUN_CI_LOCK:-0}" = "1" ]; then
  bash scripts/ci_lock_protocol.sh
  ok "ci_lock_protocol.sh PASS"
else
  warn "SKIP (set RUN_CI_LOCK=1 to run full gate)"
fi
say

say "== 3) DOCKER (optional) =="
if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    ok "docker daemon OK"
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
      docker compose ps || true
    fi
  else
    warn "docker daemon not reachable"
  fi
else
  warn "docker not installed"
fi
say

say "== 4) CORE ENDPOINTS (best-effort) =="
AFO_BASE_URL="${AFO_BASE_URL:-http://127.0.0.1:8010}"
WALLET_URL="${WALLET_URL:-http://127.0.0.1:8011}"
GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3000}"

curl -sf "${AFO_BASE_URL}/health" >/dev/null && ok "soul-engine health: ${AFO_BASE_URL}/health" || warn "soul-engine health not reachable: ${AFO_BASE_URL}/health"
curl -sf "${WALLET_URL}/health" >/dev/null && ok "wallet health: ${WALLET_URL}/health" || warn "wallet health not reachable: ${WALLET_URL}/health"
curl -sf "${GRAFANA_URL}/api/health" >/dev/null && ok "grafana health: ${GRAFANA_URL}/api/health" || warn "grafana health not reachable: ${GRAFANA_URL}/api/health"
say

say "== 5) PRIVACY QUICK SCAN (best-effort) =="
if command -v rg >/dev/null 2>&1; then
  if rg -n "file://|<LOCAL_WORKSPACE>|/Users/|/home/|C:\\\\|\\\\Users\\\\" docs artifacts . >/dev/null 2>&1; then
    warn "absolute path pattern found (review recommended)"
  else
    ok "no obvious absolute-path leakage"
  fi
else
  warn "rg not found; skip leak scan"
fi

say
say "== ROLL CALL RESULT: GREEN (or WARN only) =="
