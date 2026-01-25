#!/bin/bash
# scripts/ci_js_syntax_check.sh
# Templater User Scripts의 문법을 미리 검증하는 효(孝)의 관문

set -e

SCRIPT_DIR="docs/Scripts"

echo "🛡️ [CI] JS Syntax Check for Obsidian Scripts..."

if [ ! -d "$SCRIPT_DIR" ]; then
    echo "⚠️ Scripts directory not found. Skipping."
    exit 0
fi

FAILED=0
while IFS= read -r -d '' file; do
    echo "🔍 Checking $file..."
    if ! node --check "$file"; then
        echo "❌ Syntax error in $file"
        FAILED=1
    fi
done < <(find "$SCRIPT_DIR" -name "*.js" -print0)

if [ $FAILED -eq 1 ]; then
    echo "❌ JS Syntax Check: FAIL"
    exit 1
else
    echo "✅ JS Syntax Check: PASS"
    exit 0
fi
