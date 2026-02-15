#!/bin/bash
# AFO Kingdom Pre-Work Hook
# 작업 시작 시 자동으로 실행되어 메모리를 불러옵니다
#
# 설치 방법:
#   chmod +x scripts/pre-work-hook.sh
#   ln -s $(pwd)/scripts/pre-work-hook.sh .git/hooks/pre-work
#
# 또는 수동 실행:
#   ./scripts/pre-work-hook.sh

set -euo pipefail

echo "🧠 AFO Kingdom Pre-Work Hook"
echo "================================"
echo ""

# 작업 컨텍스트 감지
TASK_CONTEXT="${TASK_CONTEXT:-$(git branch --show-current 2>/dev/null || echo 'unknown')}"
echo "📍 현재 작업: $TASK_CONTEXT"
echo ""

# 1. 관련 메모리 검색
echo "🔍 관련 메모리 검색 중..."
if [ -f scripts/memory_manager.py ]; then
    python scripts/memory_manager.py search "$TASK_CONTEXT" --limit 3 2>/dev/null || echo "   (메모리 검색 스킵)"
else
    echo "   ⚠️ memory_manager.py 없음"
fi
echo ""

# 2. 최근 세션 확인
echo "🎯 최근 세션:"
if [ -d memory/050_Sessions/$(date +%Y) ]; then
    ls -t memory/050_Sessions/$(date +%Y)/*.md 2>/dev/null | head -3 | while read file; do
        echo "   - $(basename $file)"
    done
else
    echo "   (세션 기록 없음)"
fi
echo ""

# 3. 활성 프로젝트 표시
echo "📁 활성 프로젝트:"
if [ -d memory/010_Projects/ACTIVE ]; then
    ls memory/010_Projects/ACTIVE/ 2>/dev/null | head -5 | while read dir; do
        echo "   - $dir"
    done
else
    echo "   (프로젝트 디렉토리 없음)"
fi
echo ""

# 4. 오늘의 Daily Note 확인
echo "📅 오늘의 노트:"
TODAY_FILE="memory/Daily Notes/$(date +%Y-%m-%d)_$(date +%a | tr 'SunMonTueWedThuFriSat' '일월화수목금토').md"
if [ -f "$TODAY_FILE" ]; then
    echo "   ✅ $TODAY_FILE 존재"
else
    echo "   📝 오늘의 노트가 없습니다. 생성하세요:"
    echo "      python scripts/memory_manager.py daily --activity '작업 시작'"
fi
echo ""

# 5. 세션 시작 제안
echo "🚀 새 세션 시작:"
echo "   python scripts/memory_manager.py session --start --title '$(echo $TASK_CONTEXT)'"
echo ""

echo "================================"
echo "✅ Pre-Work Hook 완료"
echo ""
echo "💡 팁: 중요한 인사이트는 즉시 메모리에 저장하세요"
echo "   python scripts/memory_manager.py fleeting '아이디어'"
echo ""
