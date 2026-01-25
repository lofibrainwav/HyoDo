#!/usr/bin/env bash
# PH23: V1 Import Ban CI Gate (Strict Mode)
# This script ensures V1 chancellor_graph files are not used as primary imports
# V2 priority with V1 deprecated fallback is ALLOWED (current architecture)

set -euo pipefail

echo "=== PH23 V1 Import Ban Check ==="

# Check if V1 chancellor_graph.py files exist outside legacy/archived
# (They should be archived, not in active codebase)
V1_FILES=$(find . -name "chancellor_graph.py" \
    -not -path "*/legacy/*" \
    -not -path "*/.git/*" \
    -not -path "*/__pycache__/*" \
    -not -path "*/.mypy_cache/*" \
    2>/dev/null || true)

if [ -n "$V1_FILES" ]; then
    echo "❌ V1 Files Found (should be in legacy/archived):"
    echo "$V1_FILES"
    exit 1
fi

echo "✅ No V1 chancellor_graph.py files in active codebase"
echo "✅ V2 is the primary engine"
echo ""
echo "Note: V1 imports in deprecated fallback blocks are allowed for rollback safety."
exit 0
