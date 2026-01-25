#!/bin/bash
# Grafana Tunnel 포트 불일치 자동 수정 스크립트
# 옵션 A: Cloudflare API를 통해 Tunnel 설정을 3000으로 변경

set -euo pipefail

EMAIL="bigbananamusic@gmail.com"
KEY="60653be292b5ecb225f02a672b628b759752e"
ACCOUNT_ID="ad3a31d2ccfea3d3a26c28a1c0924edb"
TUNNEL_ID="f88a3b8d-e235-4e55-9a97-84ae03f6f4fc"

echo "==================================================="
echo "   🔧 Grafana Tunnel 포트 설정 수정 (3100 → 3000)  "
echo "==================================================="
echo ""

# 현재 설정 확인
echo "📊 현재 Tunnel 설정 확인 중..."
CURRENT_CONFIG=$(curl -s -X GET \
  "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/tunnels/$TUNNEL_ID/configurations" \
  -H "X-Auth-Email: $EMAIL" \
  -H "X-Auth-Key: $KEY" \
  -H "Content-Type: application/json")

echo "$CURRENT_CONFIG" | python3 -m json.tool 2>/dev/null || echo "$CURRENT_CONFIG"
echo ""

# 새 설정 (Grafana를 3000으로 변경)
read -r -d '' NEW_CONFIG <<'EOM' || true
{
  "config": {
    "ingress": [
      {
        "hostname": "afo-grafana.brnestrm.com",
        "service": "http://localhost:3000"
      },
      {
        "hostname": "afo-metrics.brnestrm.com",
        "service": "http://localhost:9091"
      },
      {
        "service": "http_status:404"
      }
    ]
  }
}
EOM

echo "🔄 Tunnel 설정 업데이트 중..."
RESPONSE=$(curl -s -X PUT \
  "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/tunnels/$TUNNEL_ID/configurations" \
  -H "X-Auth-Email: $EMAIL" \
  -H "X-Auth-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d "$NEW_CONFIG")

echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "✅ Tunnel 설정 업데이트 성공!"
    echo ""
    echo "📝 변경 사항:"
    echo "   - afo-grafana.brnestrm.com: localhost:3100 → localhost:3000"
    echo ""
    echo "🔄 다음 단계:"
    echo "   1. Tunnel 재시작 (필요시):"
    echo "      bash scripts/restart_cloudflare_tunnel.sh"
    echo ""
    echo "   2. 외부 접근 테스트:"
    echo "      curl -I https://afo-grafana.brnestrm.com"
    echo ""
else
    echo "❌ Tunnel 설정 업데이트 실패"
    echo "   응답: $RESPONSE"
    echo ""
    echo "💡 수동으로 Cloudflare Dashboard에서 변경하세요:"
    echo "   https://one.dash.cloudflare.com/networks/tunnels"
    exit 1
fi

