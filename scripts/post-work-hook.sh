#!/bin/bash
# AFO Kingdom Post-Work Hook
# 작업 완료 시 자동으로 실행되어 메모리를 저장합니다
#
# 설치 방법:
#   chmod +x scripts/post-work-hook.sh
#   ln -s $(pwd)/scripts/post-work-hook.sh .git/hooks/post-work
#
# 또는 수동 실행:
#   ./scripts/post-work-hook.sh

set -euo pipefail

echo "🧠 AFO Kingdom Post-Work Hook"
echo "================================"
echo ""

# Git 정보 수짨
BRANCH=$(git branch --show-current 2>/dev/null || echo 'unknown')
LAST_COMMIT=$(git log -1 --pretty=format:"%h %s" 2>/dev/null || echo 'no commits')
FILES_CHANGED=$(git diff --name-only HEAD~1 2>/dev/null | head -10 || echo '')

echo "📍 작업 브랜치: $BRANCH"
echo "📝 마지막 커밋: $LAST_COMMIT"
echo ""

# 1. 세션 저장 제안
echo "💾 작업 세션을 저장하세요:"
echo ""
echo "   python scripts/memory_manager.py session --save \\"
echo "       --outcomes '구현 완료' \\"
echo "       --files $(echo $FILES_CHANGED | tr '\n' ' ' | cut -d' ' -f1-3) \\"
echo "       --decisions '의사결정 내용' \\"
echo "       --insights '새로운 인사이트'"
echo ""

# 2. Daily Note 업데이트 제안
echo "📅 일일 노트 업데이트:"
echo "   python scripts/memory_manager.py daily \\"
echo "       --activity '작업 완료: $BRANCH' \\"
echo "       --insight '학습한 내용'"
echo ""

# 3. Fleeting Notes 정리 제안
echo "📝 일시노트 정리:"
FLEETING_COUNT=$(ls memory/040_Fleeting/TEMP/*.md 2>/dev/null | wc -l)
if [ "$FLEETING_COUNT" -gt 0 ]; then
    echo "   ⚠️ $FLEETING_COUNT개의 일시노트가 정리 대기 중입니다"
    echo "   memory/040_Fleeting/TEMP/ 에서 영구노트로 전환하세요"
else
    echo "   ✅ 정리할 일시노트 없음"
fi
echo ""

# 4. mem에 저장 제안
echo "🧠 중요한 지식은 mem에 저장:"
echo "   echo '지식 내용' | memory create_entity --type knowledge"
echo ""

# 5. 다음 작업 제안
echo "🚀 다음 단계:"
echo "   1. 메모리 인덱스 업데이트"
echo "      python scripts/memory_manager.py index rebuild"
echo ""
echo "   2. 관련 승상들에게 공유"
echo "      (memory/000_Index.md에 문서화된 내용 공유)"
echo ""

echo "================================"
echo "✅ Post-Work Hook 완료"
echo ""
echo "💡 '메모리는 우리 시스템의 시작과 끝'"
echo ""
