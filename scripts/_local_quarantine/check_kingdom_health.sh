set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

echo "== 0) GIT =="
git status -sb
echo
git log --oneline -5
echo

echo "== 1) CI LOCK =="
bash scripts/ci_lock_protocol.sh
echo

echo "== 2) DOCKER (if any) =="
if command -v docker >/dev/null 2>&1; then
  docker ps --format '{{.Names}}\t{{.Status}}' | sed -n '1,200p' || true
  echo
else
  echo "[SKIP] docker not found"
fi

echo "== 3) GRAFANA PROVISION LOG (best-effort) =="
if command -v docker >/dev/null 2>&1; then
  docker logs grafana --tail 200 2>/dev/null | sed -n '1,200p' || true
  echo
fi

echo "== 4) OBSIDIAN VAULT ABSOLUTE PATH LEAK CHECK =="
VAULT="config/obsidian/vault"
if [ -d "$VAULT" ]; then
  if command -v rg >/dev/null 2>&1; then
    rg -n "file://|<LOCAL_WORKSPACE>|/Users/|/home/|C:\\\\|\\\\Users\\\\" "$VAULT" || true
  else
    echo "[SKIP] rg not found"
  fi
else
  echo "[SKIP] vault not found: $VAULT"
fi
