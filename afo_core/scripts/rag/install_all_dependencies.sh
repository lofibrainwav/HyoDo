#!/bin/bash
# RAG 시스템 전체 의존성 설치 스크립트 (가상환경)

set -e

echo "=== RAG 시스템 전체 의존성 설치 ==="
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

# requirements.txt에서 설치
if [ -f "$(dirname "$0")/requirements.txt" ]; then
    echo "📥 requirements.txt에서 의존성 설치 중..."
    pip install -q -r "$(dirname "$0")/requirements.txt"
else
    echo "📥 개별 패키지 설치 중..."
    pip install -q python-frontmatter langchain langchain-openai langchain-community langchain-qdrant langchain-text-splitters langgraph qdrant-client watchdog openai
fi

# 설치 확인
echo ""
echo "🔍 설치 확인 중..."
python3 -c "
import site
import sys

all_packages = {
    'frontmatter': 'python-frontmatter',
    'langchain': 'langchain',
    'langchain_openai': 'langchain-openai',
    'langchain_community': 'langchain-community',
    'langchain_qdrant': 'langchain-qdrant',
    'langchain_text_splitters': 'langchain-text-splitters',
    'langgraph': 'langgraph',
    'qdrant_client': 'qdrant-client',
    'watchdog': 'watchdog',
    'openai': 'openai'
}

installed = []
missing = []

for mod, name in all_packages.items():
    try:
        __import__(mod)
        installed.append(name)
    except ImportError:
        missing.append(name)

print('✅ 설치 완료:', len(installed), '개')
for pkg in installed:
    print(f'  ✅ {pkg}')

if missing:
    print('❌ 설치 필요:', len(missing), '개')
    for pkg in missing:
        print(f'  ❌ {pkg}')
else:
    print('')
    print('✅ 모든 의존성 설치 완료!')
"

echo ""
echo "💡 가상환경 사용 방법:"
echo "  source $VENV_DIR/bin/activate"
echo "  python3 scripts/rag/test_rag_system.py"

