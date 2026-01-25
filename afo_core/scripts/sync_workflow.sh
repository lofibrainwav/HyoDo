#!/bin/bash
# AFO 왕국 워크플로우 동기화 스크립트
# 지갑에서 키 추출 → 환경 변수 설정 → 시스템 검증

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AFO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_KEYS_FILE="/tmp/afo_env_keys_clean.sh"

echo "🔄 AFO 왕국 워크플로우 동기화 시작..."
echo ""

# 1. 지갑에서 키 추출
echo "📦 Step 1: 지갑에서 API 키 추출"
cd "$AFO_ROOT"
python3 scripts/export_keys.py 2>/dev/null | grep -v "^DEBUG:" > "$ENV_KEYS_FILE"

if [ ! -s "$ENV_KEYS_FILE" ]; then
    echo "❌ 키 추출 실패"
    exit 1
fi

echo "✅ 키 추출 완료: $ENV_KEYS_FILE"
echo ""

# 2. 환경 변수 로드
echo "🔧 Step 2: 환경 변수 설정"
source "$ENV_KEYS_FILE"

if [ -z "$OPENAI_API_KEY" ] || [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  일부 키가 설정되지 않았습니다"
else
    echo "✅ 환경 변수 설정 완료"
    echo "   - OPENAI_API_KEY: ${OPENAI_API_KEY:0:20}..."
    echo "   - ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:0:20}..."
fi
echo ""

# 3. 시스템 검증
echo "🔍 Step 3: 시스템 검증"

# 3.1 API 서버 건강 상태
# Phase 2-4: settings에서 포트 가져오기 (기본값 8010)
API_SERVER_PORT=${API_SERVER_PORT:-8010}
HEALTH=$(curl -s http://localhost:${API_SERVER_PORT}/health 2>/dev/null || echo "{}")
if echo "$HEALTH" | grep -q "health_percentage"; then
    PERCENTAGE=$(echo "$HEALTH" | python3 -c "import sys, json; print(json.load(sys.stdin)['health_percentage'])" 2>/dev/null || echo "N/A")
    echo "   - API 서버 건강 상태: ${PERCENTAGE}%"
else
    echo "   ⚠️  API 서버 응답 없음"
fi

# 3.2 OpenAI API 키 검증
if python3 -c "from langchain_openai import OpenAIEmbeddings; import os; e = OpenAIEmbeddings(); print('OK')" 2>/dev/null; then
    echo "   ✅ OpenAI API 키: 정상"
else
    echo "   ⚠️  OpenAI API 키: 검증 실패"
fi

# 3.3 PostgreSQL 연결
if psql -h localhost -p 15432 -U afo -d afo_memory -c "SELECT 1;" >/dev/null 2>&1; then
    echo "   ✅ PostgreSQL: 연결 성공"
else
    echo "   ⚠️  PostgreSQL: 연결 실패"
fi

echo ""
echo "✅ 워크플로우 동기화 완료"
echo ""
echo "💡 다음 명령으로 환경 변수를 로드하세요:"
echo "   source $ENV_KEYS_FILE"
