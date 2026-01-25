#!/bin/bash
# Grafana 외부 접근 검증 스크립트

set -euo pipefail

echo "==================================================="
echo "   ✅ Grafana 외부 접근 검증                        "
echo "==================================================="
echo ""

echo "📊 로컬 접근 테스트 (포트 3000)..."
LOCAL_3000=$(curl -sS -I --max-time 5 http://127.0.0.1:3000 2>&1 | head -n 1 || echo "FAIL")
LOCAL_3100=$(curl -sS -I --max-time 5 http://127.0.0.1:3100 2>&1 | head -n 1 || echo "FAIL")

echo "   3000: $LOCAL_3000"
echo "   3100: $LOCAL_3100"
echo ""

echo "🌐 외부 접근 테스트..."
EXTERNAL=$(curl -sS -I --max-time 10 https://afo-grafana.brnestrm.com 2>&1 | head -n 1 || echo "FAIL")

echo "   https://afo-grafana.brnestrm.com: $EXTERNAL"
echo ""

if echo "$EXTERNAL" | grep -q "302\|200"; then
    echo "✅ 성공! 외부 접근 정상 작동"
    exit 0
else
    echo "❌ 실패: 외부 접근 불가"
    echo ""
    echo "💡 확인 사항:"
    echo "   1. Cloudflare Dashboard에서 Service가 localhost:3000으로 설정되었는지 확인"
    echo "   2. Tunnel이 재시작되었는지 확인"
    echo "   3. 30초 정도 대기 후 재시도"
    exit 1
fi
