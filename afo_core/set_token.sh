#!/bin/bash
# 🔑 Discord Bot Token 설정 도우미
# Usage: ./set_token.sh [TOKEN]

set -e

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env 파일이 없습니다."
    echo "   먼저 실행: cp .env.example .env"
    exit 1
fi

# 토큰이 인자로 전달된 경우
if [ -n "$1" ]; then
    TOKEN="$1"
    echo "🔑 Discord Bot Token 설정 중..."
    
    # macOS와 Linux 모두 지원
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/DISCORD_BOT_TOKEN=.*/DISCORD_BOT_TOKEN=$TOKEN/" "$ENV_FILE"
    else
        # Linux
        sed -i "s/DISCORD_BOT_TOKEN=.*/DISCORD_BOT_TOKEN=$TOKEN/" "$ENV_FILE"
    fi
    
    echo "✅ Token 설정 완료!"
    echo ""
    echo "확인:"
    grep "DISCORD_BOT_TOKEN=" "$ENV_FILE" | sed 's/\(.\{20\}\).*\(.\{10\}\)/\1...\2/'
    exit 0
fi

# 대화형 모드
echo "🔑 Discord Bot Token 설정"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Discord Bot Token을 입력해주세요."
echo "(입력한 토큰은 화면에 표시되지 않습니다)"
echo ""
read -sp "Token: " TOKEN
echo ""
echo ""

if [ -z "$TOKEN" ]; then
    echo "❌ 토큰이 입력되지 않았습니다."
    exit 1
fi

# macOS와 Linux 모두 지원
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/DISCORD_BOT_TOKEN=.*/DISCORD_BOT_TOKEN=$TOKEN/" "$ENV_FILE"
else
    # Linux
    sed -i "s/DISCORD_BOT_TOKEN=.*/DISCORD_BOT_TOKEN=$TOKEN/" "$ENV_FILE"
fi

echo "✅ Token 설정 완료!"
echo ""
echo "다음 명령어로 봇을 실행하세요:"
echo "   ./quick_start.sh"
echo ""

