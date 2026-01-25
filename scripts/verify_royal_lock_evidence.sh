#!/bin/bash
set -euo pipefail

cd /Users/brnestrm/AFO_Kingdom

ts="$(date +%Y%m%d_%H%M%S)"
out="artifacts/royal_lock_verify_${ts}.log"
mkdir -p artifacts

exec > >(tee -a "$out") 2>&1

echo "== TIME =="
date

echo "== PORTS (LISTEN) =="
lsof -nP -iTCP -sTCP:LISTEN || true

echo "== DOCKER PS =="
command -v docker >/dev/null 2>&1 && docker ps || echo "docker not found"

echo "== DOCKER COMPOSE PS =="
command -v docker >/dev/null 2>&1 && docker compose ps || true

echo "== GIT STATUS =="
git status -sb
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD

echo "== VERIFY COMMIT 7431add0 exists =="
git cat-file -t 7431add0
git show -s --format="commit=%H %s" 7431add0

echo "== PUSH PROCESS CHECK =="
pgrep -fl "git push" || echo "no active git push"

echo "== PUSH SYNC CHECK (local vs remote) =="
branch="$(git rev-parse --abbrev-ref HEAD)"
local_sha="$(git rev-parse HEAD)"
remote_sha="$(git ls-remote origin "refs/heads/$branch" | awk '{print $1}')"
echo "branch=$branch"
echo "local=$local_sha"
echo "remote=$remote_sha"
test "$local_sha" = "$remote_sha" && echo "✅ PUSH SYNCED" || echo "❌ NOT SYNCED"

echo "== AFO_EVOLUTION_LOG (tail) =="
test -f AFO_EVOLUTION_LOG.md && tail -n 120 AFO_EVOLUTION_LOG.md || echo "AFO_EVOLUTION_LOG.md not found"

echo "== STRICT RUFF (code-only scope) =="
uv sync --frozen
ruff --version
ruff check packages scripts
ruff format --check packages scripts
echo "✅ RUFF 0-exit"

echo "== STRICT PYRIGHT (code-only scope) =="
uv run pyright packages/afo-core
echo "✅ PYRIGHT 0-exit"

echo "== PYTEST (afo-core scope) =="
uv run pytest -q packages/afo-core/tests
echo "✅ PYTEST 0-exit"

echo "== CI HARDENING GATE =="
if [ -f "./scripts/ci_hardening_gate.sh" ]; then
    bash -x ./scripts/ci_hardening_gate.sh
    echo "✅ CI HARDENING 0-exit"
else
    echo "⚠️ CI HARDENING GATE script not found, skipping"
fi

echo "== DONE =="
echo "evidence_file=$out"
