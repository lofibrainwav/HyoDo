#!/bin/bash
# RAG 시스템 의존성 설치 스크립트

set -e

echo "=== RAG 시스템 의존성 설치 ==="
echo ""

# Python 버전 확인
python3 --version

# 사용자 site-packages 경로 확인
USER_SITE=$(python3 -m site --user-site)
echo "사용자 site-packages: $USER_SITE"
echo ""

# requirements.txt 확인
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt 파일이 없습니다."
    exit 1
fi

echo "📋 설치할 패키지:"
cat requirements.txt
echo ""

# 개별 패키지 설치
echo "🔧 의존성 설치 중..."
python3 -m pip install --user python-frontmatter
python3 -m pip install --user langchain
python3 -m pip install --user langchain-openai
python3 -m pip install --user langchain-community
python3 -m pip install --user langchain-qdrant
python3 -m pip install --user langgraph
python3 -m pip install --user qdrant-client
python3 -m pip install --user watchdog
python3 -m pip install --user openai

echo ""
echo "✅ 설치 완료!"
echo ""

# 설치 확인
echo "🔍 설치 확인 중..."
python3 -c "
import site
import sys
user_site = site.getusersitepackages()
sys.path.insert(0, user_site)

packages = {
    'frontmatter': 'python-frontmatter',
    'langchain': 'langchain',
    'langchain_openai': 'langchain-openai',
    'langchain_community': 'langchain-community',
    'langchain_qdrant': 'langchain-qdrant',
    'langgraph': 'langgraph',
    'qdrant_client': 'qdrant-client',
    'watchdog': 'watchdog',
    'openai': 'openai'
}

results = []
for module, package in packages.items():
    try:
        __import__(module)
        results.append(f'✅ {package}')
    except ImportError:
        results.append(f'❌ {package}')

print('\n'.join(results))
"

echo ""
echo "✅ 의존성 설치 및 확인 완료!"

