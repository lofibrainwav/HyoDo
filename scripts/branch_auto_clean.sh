#!/bin/bash
# AFO Kingdom Branch Auto Clean Script (Final Version)
# Purpose: Auto-prune merged remote branches + backup tags (WIP excluded)
# Usage: ./branch_auto_clean.sh [dry|wet]

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

MODE="${1:-dry}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
CURRENT_BRANCH=$(git branch --show-current)

# === SAFETY GUARD: Block wet mode on main branch ===
if [[ "$MODE" == "wet" && "$CURRENT_BRANCH" == "main" ]]; then
    if [[ "${AFO_ALLOW_MAIN_WET:-}" != "true" ]]; then
        echo "❌ [BLOCKED] wet mode on main branch is prohibited"
        echo "   Switch to a work branch first:"
        echo "   git switch -c chore/branch-prune-ops"
        echo ""
        echo "   Or set AFO_ALLOW_MAIN_WET=true to override (not recommended)"
        exit 1
    fi
    echo "⚠️  [WARN] Running wet mode on main (AFO_ALLOW_MAIN_WET override)"
fi

echo "=== AFO Kingdom Branch Auto Clean (Mode: $MODE) ==="
echo "Current branch: $CURRENT_BRANCH"
echo ""

git fetch --all --prune

BRANCHES=$(git branch -r --merged origin/main \
    | grep -v '^ *origin/HEAD' \
    | grep -v '^ *origin/main' \
    | grep -Ev 'wip/|release/|hotfix/' \
    | sed 's| *origin/||' || true)

COUNT=$(echo "$BRANCHES" | grep -c . || echo "0")
echo "Found $COUNT merged branches to process"
echo ""

if [[ -z "$BRANCHES" || "$COUNT" -eq 0 ]]; then
    echo "✅ No branches to clean. Already optimal."
    exit 0
fi

for branch in $BRANCHES; do
    if git rev-parse "origin/$branch" >/dev/null 2>&1; then
        TAG="archive/remote-$branch-$TIMESTAMP"
        echo "📦 Backup: $TAG"
        git tag "$TAG" "origin/$branch"
        git push origin "$TAG" 2>/dev/null || echo "   (tag push skipped)"
    fi
done

echo ""
if [[ "$MODE" == "wet" ]]; then
    echo "🗑️  Deleting branches..."
    for branch in $BRANCHES; do
        echo "   → $branch"
        git push origin --delete "$branch" 2>/dev/null || echo "     (already deleted)"
    done
else
    echo "📋 DRY_RUN: Branches to be deleted:"
    for branch in $BRANCHES; do
        echo "   → $branch"
    done
    echo ""
    echo "Run './scripts/branch_auto_clean.sh wet' to execute deletion"
fi

echo ""
echo "=== Cleanup complete ($COUNT branches processed) ==="
