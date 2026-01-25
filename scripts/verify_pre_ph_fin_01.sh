#!/bin/bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

echo "== AFO PRE-FIN-01 PREFLIGHT =="
echo "time: $(date -Iseconds)"
echo "root: $ROOT"
echo

fail() { echo "[FAIL] $*"; exit 1; }
warn() { echo "[WARN] $*"; }

echo "== 1) GIT STATE =="
git status -sb
echo

if ! git diff --quiet || ! git diff --cached --quiet; then
  git diff --stat || true
  git diff --cached --stat || true
  fail "Working tree is dirty (uncommitted changes exist). Commit or stash before PH-FIN-01."
fi
echo "[OK] working tree clean"
echo

UPSTREAM="$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || true)"
if [ -z "$UPSTREAM" ]; then
  warn "No upstream tracking branch set (cannot verify pushed state)."
else
  echo "upstream: $UPSTREAM"
  git fetch --prune || true
  AHEAD="$(git rev-list --count "${UPSTREAM}..HEAD" 2>/dev/null || echo "0")"
  BEHIND="$(git rev-list --count "HEAD..${UPSTREAM}" 2>/dev/null || echo "0")"
  echo "ahead: $AHEAD, behind: $BEHIND"
  if [ "$BEHIND" != "0" ]; then
    fail "Branch is behind upstream. Pull/rebase first."
  fi
  if [ "$AHEAD" != "0" ]; then
    warn "You have unpushed commits ($AHEAD). Decide to push or keep local."
  fi
fi
echo
echo "last 5 commits:"
git log --oneline -5
echo

echo "== 2) REQUIRED FILES / SINGLE ENTRY CHECK =="
test -f scripts/ci_lock_protocol.sh || fail "scripts/ci_lock_protocol.sh missing"
echo "[OK] ci_lock_protocol.sh exists"

# Optional but expected docs (warn only)
for f in \
  "docs/tickets/PH-CI-11_Structured_Concurrency_Anyio_Trio.md" \
  "docs/tickets/PH-FIN-01_Julie_CPA_Autopilot.md" \
  "docs/tickets/PH-ST-06_Obsidian_Scripting_Orchestration.md"
do
  if [ -f "$f" ]; then echo "[OK] $f"; else warn "missing: $f"; fi
done
echo

echo "== 3) OBSIDIAN VAULT INTEGRITY =="
VAULT="config/obsidian/vault"
SRC="$VAULT/src"
PH="$VAULT/ph"
test -d "$VAULT" || fail "Vault missing: $VAULT"
test -d "$SRC" || warn "Vault src missing: $SRC"
test -d "$PH" || warn "Vault ph missing: $PH"

# Absolute path / scheme leakage (must be 0)
if command -v rg >/dev/null 2>&1; then
  LEAKS="$(rg -n "file://|<LOCAL_WORKSPACE>|/Users/|/home/|C:\\\\|\\\\Users\\\\" "$VAULT" || true)"
  if [ -n "$LEAKS" ]; then
    echo "$LEAKS"
    fail "Absolute path/scheme leakage detected in vault."
  fi
  echo "[OK] vault leakage: 0"
else
  warn "ripgrep (rg) not found; leakage check skipped"
fi

# Symlink targets must be relative (best-effort check)
python3 - <<'PY'
from pathlib import Path
import os, sys

vault = Path("config/obsidian/vault")
bad = []
for p in vault.rglob("*"):
    if p.is_symlink():
        t = os.readlink(p)
        if t.startswith("/") or ":\\" in t or t.startswith("file://"):
            bad.append((str(p), t))
if bad:
    print("[FAIL] absolute symlink targets detected:")
    for p,t in bad:
        print(f"- {p} -> {t}")
    sys.exit(1)
print("[OK] symlink targets look relative")
PY
echo

echo "== 4) DEBUG / SECRET HARDENING QUICK SCAN =="
# Ensure we are not accidentally binding debugpy publicly
if command -v rg >/dev/null 2>&1; then
  PUBDBG="$(rg -n "debugpy\.listen\(|0\.0\.0\.0" packages/afo-core/AFO 2>/dev/null || true)"
  if [ -n "$PUBDBG" ]; then
    echo "$PUBDBG"
    warn "debugpy/public bind patterns found. Confirm 127.0.0.1 only."
  else
    echo "[OK] no obvious public debug bind patterns"
  fi
else
  warn "rg not found; debug scan skipped"
fi
echo

echo "== 5) CI LOCK (OPTIONAL RUN) =="
if [ "${RUN_CI_LOCK:-0}" = "1" ]; then
  bash scripts/ci_lock_protocol.sh
  echo "[OK] ci_lock_protocol.sh PASS"
else
  echo "[SKIP] set RUN_CI_LOCK=1 to run full CI LOCK gate locally"
fi

echo
echo "== PREFLIGHT RESULT: GREEN (or WARN only) =="
