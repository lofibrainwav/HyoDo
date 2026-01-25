#!/bin/bash
# AFO 왕국 코드 자동 포맷팅 스크립트
# ruff format 실행

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AFO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$AFO_ROOT"

echo "=== 🎨 AFO 왕국 코드 포맷팅 ==="
echo ""

# Ruff Format 실행
if command -v ruff &> /dev/null || python3 -m ruff --version &> /dev/null; then
    echo "📋 Ruff Format 실행 중..."
    python3 -m ruff format .
    echo "✅ 포맷팅 완료"
else
    echo "⚠️  Ruff가 설치되지 않았습니다. 설치 중..."
    pip install --user ruff || pip install ruff
    echo "📋 Ruff Format 실행 중..."
    python3 -m ruff format .
    echo "✅ 포맷팅 완료"
fi

echo ""
echo "💡 다음 명령으로 린트 체크: ./scripts/run_quality_checks.sh"

