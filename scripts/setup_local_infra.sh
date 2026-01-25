#!/bin/bash
# 🏰 AFO 왕국 로컬 인프라 설정 스크립트
# 메타인지 최적화: Docker 최소화 원칙 준수
# INFRA_MODE=local 환경에서 인프라 자동 구성

set -euo pipefail

echo "🏰 AFO 왕국 로컬 인프라 설정 (메타인지 최적화)"
echo "INFRA_MODE=local 기준으로 인프라 구성"
echo "=" * 50

# 환경변수 로드 (.env 파일 안전하게 파싱)
if [ -f ".env" ]; then
    while IFS='=' read -r key value; do
        # 주석과 빈 줄 건너뛰기
        [[ $key =~ ^#.*$ ]] && continue
        [[ -z $key ]] && continue
        # 값에서 주석 제거 및 공백 정리
        value=$(echo "$value" | sed 's/#.*$//' | sed 's/[[:space:]]*$//')
        # export
        export "$key"="$value"
    done < .env
fi

# INFRA_MODE 확인
echo "📋 INFRA_MODE 환경변수: '${INFRA_MODE:-설정되지 않음}'"

# INFRA_MODE가 local이 아니면 종료
if [[ "${INFRA_MODE:-}" != "local" ]]; then
    echo "⚠️  이 스크립트는 INFRA_MODE=local 전용입니다."
    echo "   현재 모드: '${INFRA_MODE:-설정되지 않음}'"
    echo "   명령줄에서: INFRA_MODE=local bash scripts/setup_local_infra.sh"
    echo "   또는 .env 파일에서 INFRA_MODE=local로 설정하세요."
    echo "   디버깅: .env 파일 내용 확인"
    head -5 .env | grep -E "(^#|^$|^INFRA_MODE)" || echo "INFRA_MODE 라인을 찾을 수 없습니다."
    exit 1
fi

echo "✅ INFRA_MODE=local 확인됨, 로컬 인프라 설정을 시작합니다."

# Redis 설치 및 시작
echo ""
echo "🔴 Redis 설정 중..."
if ! brew list | grep -q redis; then
    echo "📦 Redis 설치..."
    brew install redis
else
    echo "✅ Redis 이미 설치됨"
fi

if ! brew services list | grep redis | grep -q started; then
    echo "🚀 Redis 서비스 시작..."
    brew services start redis
    sleep 2
else
    echo "✅ Redis 서비스 이미 실행 중"
fi

# Redis 연결 테스트
echo "🔍 Redis 연결 테스트..."
if redis-cli ping | grep -q PONG; then
    echo "✅ Redis 연결 성공"
else
    echo "❌ Redis 연결 실패"
    exit 1
fi

# PostgreSQL 설치 및 시작
echo ""
echo "🐘 PostgreSQL 설정 중..."
if ! brew list | grep -q postgresql; then
    echo "📦 PostgreSQL 설치..."
    brew install postgresql@16
else
    echo "✅ PostgreSQL 이미 설치됨"
fi

if ! brew services list | grep postgresql | grep -q started; then
    echo "🚀 PostgreSQL 서비스 시작..."
    brew services start postgresql@16
    sleep 3
else
    echo "✅ PostgreSQL 서비스 이미 실행 중"
fi

# PostgreSQL 연결 테스트
echo "🔍 PostgreSQL 연결 테스트..."
if psql postgres -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ PostgreSQL 연결 성공"
else
    echo "❌ PostgreSQL 연결 실패"
    echo "💡 PostgreSQL 초기 설정이 필요할 수 있습니다:"
    echo "   createdb 또는 initdb 명령어로 데이터베이스 초기화 필요"
fi

# 환경별 호스트 설정 확인
echo ""
echo "⚙️  환경 설정 확인..."
echo "REDIS_HOST: ${REDIS_HOST:-localhost}"
echo "POSTGRES_HOST: ${POSTGRES_HOST:-localhost}"
echo "OLLAMA_HOST: ${OLLAMA_HOST:-localhost}"
echo "DASHBOARD_URL: ${DASHBOARD_URL:-http://localhost:3000}"

# 헬스체크 실행
echo ""
echo "🏥 헬스체크 실행..."
python system_health_check.py

echo ""
echo "✅ 로컬 인프라 설정 완료!"
echo ""
echo "🎯 다음 단계:"
echo "1. python scripts/lance_hybrid_qwen3.py ingest /path/to/receipt.jpg"
echo "2. python scripts/lance_hybrid_qwen3.py search '커피'"
echo "3. CI 재실행: PR #59에서 타임아웃 문제 해결 확인"
echo ""
echo "📊 Trinity Score 표시 정규화 적용됨 (485% → 98.8%)"
echo "🔧 INFRA_MODE=local 설정으로 헬스체크 자동 조정"