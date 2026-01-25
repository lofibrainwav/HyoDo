#!/bin/bash

# AFO Kingdom Cloudflare Tunnel 재시작 스크립트
# 외부 접근 복구용

set -e

echo "🔄 AFO Kingdom Cloudflare Tunnel 재시작 중..."

# 현재 프로세스 확인
echo "📊 현재 cloudflared 프로세스 상태:"
ps aux | grep cloudflared | grep -v grep || echo "실행 중인 cloudflared 프로세스 없음"

# 서비스 상태 확인
echo "📊 cloudflared 서비스 상태:"
sudo systemctl status cloudflared --no-pager -l | head -20

# 기존 프로세스 정리
echo "🧹 기존 cloudflared 프로세스 정리..."
sudo systemctl stop cloudflared 2>/dev/null || true
pkill -f cloudflared 2>/dev/null || true
sleep 2

# 로그 파일 초기화
sudo truncate -s 0 /var/log/cloudflared.log 2>/dev/null || true

# 서비스 재시작
echo "🚀 cloudflared 서비스 재시작..."
sudo systemctl start cloudflared

# 상태 확인
sleep 3
echo "📊 재시작 후 서비스 상태:"
sudo systemctl status cloudflared --no-pager | head -15

# 로그 확인
echo "📋 최근 로그:"
sudo journalctl -u cloudflared -n 10 --no-pager

echo "✅ Tunnel 재시작 완료!"
echo "⏳ 30초 후 외부 접근 테스트하세요"

# 헬스 체크
echo "🏥 헬스 체크 실행..."
sleep 30

echo "🔍 외부 접근 테스트:"
curl -sS -I --max-time 5 https://afo-grafana.brnestrm.com | head -n 1
curl -sS -I --max-time 5 https://afo-metrics.brnestrm.com | head -n 1

echo "✅ 재시작 프로세스 완료!"