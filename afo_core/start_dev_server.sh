#!/bin/bash
# AFO 왕국 개발 서버 시작 스크립트 (Poetry 최적화 버전)

set -euo pipefail

# 스크립트 위치로 이동 (packages/afo-core)
cd "$(dirname "$0")"

# 개발 환경 최적화 설정
# packages/afo-core를 PYTHONPATH에 추가하여 로컬 AFO 패키지 우선 로드
export PYTHONPATH="${PYTHONPATH:-}:$(pwd):$(pwd)/../../"
export UVICORN_RELOAD_DELAY=1.0

echo "🚀 AFO 왕국 개발 서버 시작 (Poetry 모드)"
echo "📂 Working Directory: $(pwd)"
echo "🐍 PYTHONPATH: $PYTHONPATH"

# uvicorn 실행 (poetry 환경 내에서)
python3 -m uvicorn \
    AFO.api_server:app \
    --reload \
    --reload-delay 1.0 \
    --reload-exclude "*.pyc" \
    --reload-exclude "__pycache__" \
    --reload-exclude "artifacts/*" \
    --reload-exclude "logs/*" \
    --reload-include "*.py" \
    --host 127.0.0.1 \
    --port 8010 \
    --log-level info

echo "✅ AFO 왕국 서버 중지됨"
