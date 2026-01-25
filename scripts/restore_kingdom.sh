#!/bin/bash
# restore_kingdom.sh - AFO 왕국 인프라 일괄 복구 스크립트 (승상 제작)

echo "👑 AFO 왕국 복구 프로토콜을 시작합니다..."

# 1. PostgreSQL & Redis (Heart & Lung)
echo "1. [Brain & Heart] PostgreSQL/Redis 깨우는 중..."
docker start afo-postgres afo-redis 2>/dev/null || docker compose -f packages/afo-core/docker-compose.yml up -d postgres redis

# 2. Kill Old Processes
echo "2. [Cleanup] 좀비 프로세스 정리 중..."
lsof -ti :8010 | xargs -r kill -9 2>/dev/null || true
lsof -ti :3000 | xargs -r kill -9 2>/dev/null || true

# 3. Start API Server (Nerves)
echo "3. [Nerves] API 서버(Soul Engine) 가동 중..."
cd packages/afo-core || { echo "❌ Failed to cd to packages/afo-core"; exit 1; }
# shellcheck disable=SC1091
source ../../.venv/bin/activate
PYTHONPATH=. nohup python3 api_server.py > /tmp/afo_api.log 2>&1 &
API_PID=$!
echo "   ✅ API Server PID: $API_PID"

# 4. Start Dashboard (Face)
cd ../dashboard || { echo "❌ Failed to cd to ../dashboard"; exit 1; }
echo "4. [Face] Dashboard 가동 중..."
npm run dev > /tmp/afo_dashboard.log 2>&1 &
DASH_PID=$!
echo "   ✅ Dashboard PID: $DASH_PID"

echo "⏳ 시스템 안정화 대기 중..."
# Wait for API server to be ready (port check)
# shellcheck disable=SC2034
for i in {1..10}; do
    if lsof -ti :8010 > /dev/null 2>&1; then
        echo "   ✅ API Server is listening on port 8010"
        break
    fi
    sleep 1
done
# Additional wait for full initialization
sleep 2

echo "🎉 왕국 복구 완료!"
echo "   - API: http://localhost:8010/docs"
echo "   - Dashboard: http://localhost:3000/aicpa_julie"
echo "   - Logs: tail -f /tmp/afo_api.log"
