#!/bin/bash
set -euo pipefail

VAULT="config/obsidian/vault"
echo "== OBSIDIAN VAULT HEALTH CHECK =="
echo "Target: $VAULT"
echo

echo "== 1) STRUCTURE VERIFICATION =="
if [ ! -d "$VAULT" ]; then
    echo "[FAIL] Vault directory NOT FOUND!"
    exit 1
fi

check_path() {
    if [ -e "$1" ]; then echo "[OK] Found: $1"; else echo "[FAIL] Missing: $1"; fi
}

check_path "$VAULT/00_HOME.md"
check_path "$VAULT/src"
check_path "$VAULT/_moc"
check_path "$VAULT/templates"
check_path "$VAULT/scripts"
echo

echo "== 2) SYMLINK INTEGRITY (External SSOT) =="
# Check if key documentation is symlinked or present
count=$(find "$VAULT/src" -name "*.md" | wc -l)
echo "[INFO] Total Note Count in src/: $count"
find "$VAULT" -type l -maxdepth 3 | header "Symlinks detected (Top 5)" | head -n 5 || true
echo

echo "== 3) PRIVACY LEAK SCAN (Absolute Paths) =="
if command -v rg >/dev/null 2>&1; then
    # Scan for common absolute path patterns
    LEAKS=$(rg -n "file://|/Users/|/home/|C:\\\\" "$VAULT" --glob "*.md" || true)
    if [ -z "$LEAKS" ]; then
        echo "[OK] No absolute path leaks detected."
    else
        echo "[WARN] Absolute path leaks found:"
        echo "$LEAKS" | head -n 10
    fi
else
    echo "[SKIP] ripgrep (rg) not found, skipping leak scan."
fi
echo

echo "== CHECK COMPLETE =="
