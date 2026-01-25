#!/bin/bash

# AFO Kingdom Tunnel Config 업데이트 스크립트
# API를 통한 설정 업데이트용

set -e

echo "🔄 AFO Kingdom Tunnel Config 업데이트 중..."

# 환경 변수 확인
if [ -z "$TF_VAR_tunnel_id" ]; then
    echo "❌ TF_VAR_tunnel_id 환경변수가 설정되지 않았습니다"
    echo "사용법: export TF_VAR_tunnel_id='your-tunnel-uuid' && $0"
    exit 1
fi

if [ -z "$TF_VAR_cloudflare_api_token" ]; then
    echo "❌ TF_VAR_cloudflare_api_token 환경변수가 설정되지 않았습니다"
    exit 1
fi

# 현재 설정 확인
echo "📊 현재 Tunnel 설정 확인:"
curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/$TF_VAR_cloudflare_account_id/cfd_tunnel/$TF_VAR_tunnel_id/configurations" \
  -H "Authorization: Bearer $TF_VAR_cloudflare_api_token" \
  -H "Content-Type: application/json" | jq '.result.config' 2>/dev/null || echo "설정 조회 실패"

# 설정 업데이트
echo "🚀 Tunnel Config 업데이트..."
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$TF_VAR_cloudflare_account_id/cfd_tunnel/$TF_VAR_tunnel_id/configurations" \
  -H "Authorization: Bearer $TF_VAR_cloudflare_api_token" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "ingress": [
        {
          "hostname": "afo-grafana.brnestrm.com",
          "service": "http://localhost:3100"
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
  }' | jq '.success' 2>/dev/null || echo "설정 업데이트 실패"

# 설정 검증
echo "🔍 업데이트된 설정 확인:"
sleep 3
curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/$TF_VAR_cloudflare_account_id/cfd_tunnel/$TF_VAR_tunnel_id/configurations" \
  -H "Authorization: Bearer $TF_VAR_cloudflare_api_token" \
  -H "Content-Type: application/json" | jq '.result.config.ingress' 2>/dev/null || echo "설정 검증 실패"

echo "✅ Config 업데이트 완료!"
echo "⏳ 30초 후 외부 접근 테스트하세요"

# 헬스 체크
echo "🏥 헬스 체크 실행..."
sleep 30

echo "🔍 외부 접근 테스트:"
curl -sS -I --max-time 5 https://afo-grafana.brnestrm.com | head -n 1
curl -sS -I --max-time 5 https://afo-metrics.brnestrm.com | head -n 1

echo "✅ Config 업데이트 프로세스 완료!"