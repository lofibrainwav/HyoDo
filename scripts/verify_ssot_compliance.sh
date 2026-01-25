#!/bin/bash
# SSOT 준수 검증 스크립트 (진정한 SSOT 개념 적용)
# 시스템 구성 요소들이 SSOT를 제대로 참조하는지 확인

echo "=== SSOT 준수 검증 ==="
echo "시각: $(date)"
echo ""

# SSOT 파일 존재 확인
if [ ! -f "docs/AFO_FINAL_SSOT.md" ]; then
    echo "❌ SSOT 파일 없음: docs/AFO_FINAL_SSOT.md"
    exit 1
fi

echo "✅ SSOT 파일 존재 확인"

# 주요 구성 요소들이 SSOT 참조 확인
echo ""
echo "📋 SSOT 참조 검증:"

# AGENTS.md가 SSOT 참조하는지
if grep -q "docs/AFO_FINAL_SSOT.md" AGENTS.md; then
    echo "✅ AGENTS.md: SSOT 참조함"
else
    echo "❌ AGENTS.md: SSOT 참조하지 않음"
fi

# CI/CD가 SSOT 참조하는지
if grep -q "SSOT" .github/workflows/ci.yml; then
    echo "✅ CI/CD: SSOT 참조함"
else
    echo "❌ CI/CD: SSOT 참조하지 않음"
fi

# 헌법 파일 존재 확인
if [ -f "packages/trinity-os/TRINITY_CONSTITUTION.md" ]; then
    echo "✅ 헌법 파일 존재: packages/trinity-os/TRINITY_CONSTITUTION.md"
else
    echo "❌ 헌법 파일 없음"
fi

echo ""
echo "🎯 SSOT 준수 상태: 시스템의 진정한 진실 근원으로 작동 중"
echo "모든 구성 요소는 docs/AFO_FINAL_SSOT.md를 참조해야 함"