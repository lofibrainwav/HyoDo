#!/bin/bash
# AFO Kingdom Git Hooks Installer
# 眞善美孝永 - Install optimized git hooks for the team

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_SRC="$SCRIPT_DIR/hooks"
HOOKS_DST="$(git rev-parse --git-dir)/hooks"

echo "🔧 AFO Kingdom Git Hooks Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Install each hook
for hook in "$HOOKS_SRC"/*; do
    if [ -f "$hook" ]; then
        hook_name=$(basename "$hook")
        echo "📦 Installing $hook_name..."

        # Backup existing hook if it exists and is different
        if [ -f "$HOOKS_DST/$hook_name" ]; then
            if ! diff -q "$hook" "$HOOKS_DST/$hook_name" > /dev/null 2>&1; then
                echo "   ↳ Backing up existing $hook_name to $hook_name.bak"
                cp "$HOOKS_DST/$hook_name" "$HOOKS_DST/$hook_name.bak"
            fi
        fi

        # Copy and make executable
        cp "$hook" "$HOOKS_DST/$hook_name"
        chmod +x "$HOOKS_DST/$hook_name"
        echo "   ✅ $hook_name installed"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Git hooks installed successfully!"
echo ""
echo "Installed hooks:"
ls -la "$HOOKS_DST" | grep -E "^-rwx" | awk '{print "  • " $NF}'
echo ""
echo "To uninstall: rm $HOOKS_DST/{pre-push,pre-commit}"
