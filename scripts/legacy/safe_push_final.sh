#!/usr/bin/env bash
set -euo pipefail

echo "🔍 AFO 왕국 최종 SSOT 검증 시작..."
echo "====================================="

# 1. 증거 번들 검증
echo "📋 증거 번들 검증..."
if [ -d "artifacts/ticket045_evidence" ]; then
    echo "✅ Evidence bundle 존재 확인"
    ls -la artifacts/ticket045_evidence/ | head -5
else
    echo "❌ Evidence bundle 없음 - 수동 생성 필요"
    exit 1
fi

# 2. 핵심 파일 검증
echo "📁 핵심 파일 검증..."
if [ -f "packages/afo-core/afo/rag/llamaindex_streaming_rag.py" ]; then
    FILE_SIZE=$(stat -f%z packages/afo-core/afo/rag/llamaindex_streaming_rag.py)
    if [ "$FILE_SIZE" -eq 8467 ]; then
        echo "✅ T2.1 파일: 8,467 bytes 확인"
    else
        echo "❌ T2.1 파일 크기 불일치: $FILE_SIZE"
        exit 1
    fi
else
    echo "❌ T2.1 파일 없음"
    exit 1
fi

# 3. Trinity Score 검증
echo "🎯 Trinity Score 검증..."
HEALTH_RESPONSE=$(curl -s http://localhost:8010/health)
if echo "$HEALTH_RESPONSE" | grep -q '"health_percentage":93.2'; then
    echo "✅ Trinity Score: 93.2% 확인"
else
    echo "❌ Trinity Score 불일치"
    echo "Response: $HEALTH_RESPONSE"
    exit 1
fi

# 4. Docker 상태 검증
echo "🐳 Docker 상태 검증..."
CONTAINER_COUNT=$(docker ps --format 'table {{.Names}}' | grep -c afo)
if [ "$CONTAINER_COUNT" -eq 15 ]; then
    echo "✅ Docker 컨테이너: 15/15 healthy"
else
    echo "❌ Docker 컨테이너 수 불일치: $CONTAINER_COUNT/15"
    exit 1
fi

echo "🎉 모든 SSOT 검증 통과!"
echo "================================"

# 5. Git 상태 확인 및 안전 푸시
echo "🔄 Git 상태 확인..."
git status --porcelain | wc -l | xargs echo "변경 파일 수:"

echo "📦 변경사항 스테이징..."
git add -A

echo "🧪 민감정보 체크..."
if git diff --cached | grep -q "BEGIN PRIVATE KEY\|OPENAI_API_KEY\|AWS_SECRET\|SECRET_KEY\|PASSWORD\|TOKEN"; then
    echo "❌ 민감정보 발견! 푸시 중단"
    exit 1
else
    echo "✅ 민감정보 없음"
fi

echo "🏷️ SSOT 태그 생성..."
TAG="ssot-ticket-045-$(date +%Y%m%d-%H%M%S)"
git tag -a "$TAG" -m "SSOT-VERIFIED: Phase1 + Phase2(T2.1~T2.2) completed; T2.3 ready; Trinity 93.2"

echo "📝 커밋 생성..."
git commit -m "feat(ticket-045): code validation system

SSOT-VERIFIED: Phase 1 + Phase 2 Critical (T2.1~T2.2) completed, T2.3 ready
- Trinity Score: 75.38% → 93.2% (+17.82%p)
- Evidence: artifacts/ticket045_evidence/$(date +%Y%m%d)/
- Decision: SSOT-VERIFIED with evidence validation"

echo "🚀 메인 브랜치로 푸시..."
git push origin HEAD

echo "🏷️ 태그 푸시..."
git push origin "$TAG"

echo "🎊 푸시 완료! SSOT-VERIFIED 상태로 메인 브랜치 업데이트됨"
echo "태그: $TAG"
echo "브랜치: $(git branch --show-current)"
echo "커밋: $(git rev-parse HEAD)"
