#!/bin/bash
# RAG 시스템 의존성 설치 스크립트 (가상환경 사용)

set -e

echo "=== RAG 시스템 의존성 설치 (가상환경) ==="
echo ""

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VENV_DIR="$REPO_ROOT/venv_rag"

# 가상환경 생성
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 가상환경 생성 중..."
    python3 -m venv "$VENV_DIR"
    echo "✅ 가상환경 생성 완료"
fi

# 가상환경 활성화
echo "🔧 가상환경 활성화..."
source "$VENV_DIR/bin/activate"

# 의존성 설치
echo "📥 의존성 설치 중..."
pip install -q python-frontmatter langchain-qdrant qdrant-client

# 설치 확인
echo ""
echo "🔍 설치 확인 중..."
python3 -c "
import frontmatter
import langchain_qdrant
import qdrant_client
print('✅ python-frontmatter')
print('✅ langchain-qdrant')
print('✅ qdrant-client')
print('')
print('✅ 모든 의존성 설치 완료!')
"

echo ""
echo "💡 가상환경 사용 방법:"
echo "  source $VENV_DIR/bin/activate"
echo "  python3 scripts/rag/test_rag_system.py"

