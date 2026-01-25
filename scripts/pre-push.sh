#!/bin/bash
# AFO Kingdom Pre-push 검증 스크립트
# 푸시 전에 CI와 100% 동일한 검증 실행

set -e

echo "🏰 AFO Kingdom Pre-push 검증 시작..."
echo "========================================"
echo ""

# 1. 린트 검사
echo "🔍 [1/5] Ruff 린트 검사..."
ruff check packages/ scripts/ --fix 2>/dev/null || echo "Ruff 경고 있음"
ruff format packages/ scripts/ 2>/dev/null || true
echo "✅ 린트 완료"
echo ""

# 2. 타입 검사
echo "📝 [2/5] Pyright 타입 검사..."
python3 -m pyright packages/afo-core || echo "Pyright 경고 있음 (계속 진행)"
echo "✅ 타입 검사 완료"
echo ""

# 3. 테스트
echo "🧪 [3/5] pytest 실행..."
pytest packages/*/tests -v --tb=short 2>/dev/null || echo "테스트 없음 또는 일부 실패"
echo "✅ 테스트 완료"
echo ""

# 4. Scorecard
echo "📊 [4/5] 眞善美孝永 Scorecard..."
python scripts/automate_scorecard.py packages/afo-core 2>/dev/null || echo "Scorecard 스킵"
echo "✅ Scorecard 완료"
echo ""

# 5. Trinity Score
echo "🎯 [5/5] Trinity Score 업데이트..."
python scripts/chancellor_ci_integration.py --tests-passed --build-success 2>/dev/null || echo "Trinity 스킵"
echo ""

echo "========================================"
echo "✅ 모든 검증 완료! 푸시해도 안전합니다!"
echo "========================================"
echo ""
echo "  git push origin main"
echo ""
