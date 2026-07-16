#!/bin/bash
# AFO Kingdom Pre-Work Hook
#       
#
#  :
#   chmod +x scripts/pre-work-hook.sh
#   ln -s $(pwd)/scripts/pre-work-hook.sh .git/hooks/pre-work
#
#   :
#   ./scripts/pre-work-hook.sh

set -euo pipefail

echo "🧠 AFO Kingdom Pre-Work Hook"
echo "================================"
echo ""

#   
TASK_CONTEXT="${TASK_CONTEXT:-$(git branch --show-current 2>/dev/null || echo 'unknown')}"
echo "📍  : $TASK_CONTEXT"
echo ""

# 1.   
echo "🔍    ..."
if [ -f scripts/memory_manager.py ]; then
    python scripts/memory_manager.py search "$TASK_CONTEXT" --limit 3 2>/dev/null || echo "   (  )"
else
    echo "   ⚠️ memory_manager.py "
fi
echo ""

# 2.   
echo "🎯  :"
if [ -d memory/050_Sessions/$(date +%Y) ]; then
    ls -t memory/050_Sessions/$(date +%Y)/*.md 2>/dev/null | head -3 | while read file; do
        echo "   - $(basename $file)"
    done
else
    echo "   (  )"
fi
echo ""

# 3.   
echo "📁  :"
if [ -d memory/010_Projects/ACTIVE ]; then
    ls memory/010_Projects/ACTIVE/ 2>/dev/null | head -5 | while read dir; do
        echo "   - $dir"
    done
else
    echo "   (  )"
fi
echo ""

# 4.  Daily Note 
echo "📅  :"
TODAY_FILE="memory/Daily Notes/$(date +%Y-%m-%d)_$(date +%a | tr 'SunMonTueWedThuFriSat' '').md"
if [ -f "$TODAY_FILE" ]; then
    echo "   ✅ $TODAY_FILE "
else
    echo "   📝   . :"
    echo "      python scripts/memory_manager.py daily --activity ' '"
fi
echo ""

# 5.   
echo "🚀   :"
echo "   python scripts/memory_manager.py session --start --title '$(echo $TASK_CONTEXT)'"
echo ""

echo "================================"
echo "✅ Pre-Work Hook "
echo ""
echo "💡 :     "
echo "   python scripts/memory_manager.py fleeting ''"
echo ""
