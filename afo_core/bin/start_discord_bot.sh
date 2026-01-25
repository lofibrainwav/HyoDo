#!/bin/bash
# AFO Kingdom Discord Bot 실행 스크립트
# Trinity Score: 93.0 (Spokesman Layer)

# 프로젝트 루트 설정
export PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONPATH="$PROJECT_ROOT/packages/afo-core:$PROJECT_ROOT/packages/trinity-os"
export AFO_API_URL="http://localhost:8010"

# uv를 사용하여 실행 (환경 격리)
cd "$PROJECT_ROOT/packages/afo-core"

echo "🚀 AFO Kingdom Discord Bot 시작... (Spokesman Layer)"
echo "   - API URL: $AFO_API_URL"
echo "   - Python Path: $PYTHONPATH"

# uv run으로 의존성과 함께 실행
uv run python -m AFO.services.discord_bot_service
