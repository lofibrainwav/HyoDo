#!/bin/bash
# AFO Kingdom Post-Work Hook
#       
#
#  :
#   chmod +x scripts/post-work-hook.sh
#   ln -s $(pwd)/scripts/post-work-hook.sh .git/hooks/post-work
#
#   :
#   ./scripts/post-work-hook.sh

set -euo pipefail

echo "🧠 AFO Kingdom Post-Work Hook"
echo "================================"
echo ""

# Git  
BRANCH=$(git branch --show-current 2>/dev/null || echo 'unknown')
LAST_COMMIT=$(git log -1 --pretty=format:"%h %s" 2>/dev/null || echo 'no commits')
FILES_CHANGED=$(git diff --name-only HEAD~1 2>/dev/null | head -10 || echo '')

echo "📍  : $BRANCH"
echo "📝  : $LAST_COMMIT"
echo ""

# 1.   
echo "💾   :"
echo ""
echo "   python scripts/memory_manager.py session --save \\"
echo "       --outcomes ' ' \\"
echo "       --files $(echo $FILES_CHANGED | tr '\n' ' ' | cut -d' ' -f1-3) \\"
echo "       --decisions ' ' \\"
echo "       --insights ' '"
echo ""

# 2. Daily Note  
echo "📅   :"
echo "   python scripts/memory_manager.py daily \\"
echo "       --activity ' : $BRANCH' \\"
echo "       --insight ' '"
echo ""

# 3. Fleeting Notes  
echo "📝  :"
FLEETING_COUNT=$(ls memory/040_Fleeting/TEMP/*.md 2>/dev/null | wc -l)
if [ "$FLEETING_COUNT" -gt 0 ]; then
    echo "   ⚠️ $FLEETING_COUNT    "
    echo "   memory/040_Fleeting/TEMP/   "
else
    echo "   ✅   "
fi
echo ""

# 4. mem  
echo "🧠   mem :"
echo "   echo ' ' | memory create_entity --type knowledge"
echo ""

# 5.   
echo "🚀  :"
echo "   1.   "
echo "      python scripts/memory_manager.py index rebuild"
echo ""
echo "   2.   "
echo "      (memory/000_Index.md   )"
echo ""

echo "================================"
echo "✅ Post-Work Hook "
echo ""
echo "💡 '    '"
echo ""
