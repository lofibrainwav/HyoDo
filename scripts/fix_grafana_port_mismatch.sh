#!/bin/bash
# Grafana 포트 불일치 해결 스크립트
# 옵션 A: Cloudflare Tunnel 설정을 3000으로 변경 (권장)
# 옵션 B: Grafana를 3100에서 듣게 설정

set -euo pipefail

echo "==================================================="
echo "   🔧 Grafana 포트 불일치 해결                      "
echo "==================================================="
echo ""

# 진단 먼저 실행
echo "📊 현재 상태 진단..."
bash "$(dirname "$0")/diagnose_monitoring_ports.sh"

echo ""
echo "==================================================="
echo "해결 방법 선택:"
echo ""
echo "옵션 A (권장): Cloudflare Tunnel 설정을 3000으로 변경"
echo "  - Cloudflare Zero Trust → Tunnels → Public Hostnames"
echo "  - afo-grafana.brnestrm.com 서비스를 http://localhost:3000으로 변경"
echo ""
echo "옵션 B: Grafana를 3100에서 듣게 설정"
echo "  - docker-compose.yml에 GF_SERVER_HTTP_PORT=3100 추가"
echo "  - 컨테이너 재시작"
echo ""
echo "==================================================="

