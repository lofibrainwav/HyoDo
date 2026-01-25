#!/bin/bash

# AFO Kingdom - 포트 8000 종료 스크립트
# 포트 통합 완료 후 사용

echo "🛑 포트 8000 (kingdom_dashboard.html) 종료 중..."

# 포트 8000에서 실행 중인 프로세스 찾기
PID=$(lsof -ti:8000)

if [ -z "$PID" ]; then
    echo "✅ 포트 8000에서 실행 중인 프로세스가 없습니다."
    exit 0
fi

echo "📋 발견된 프로세스: PID $PID"
echo "🔍 프로세스 정보:"
ps -p $PID -o pid,comm,args

read -p "정말 종료하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kill -9 $PID
    echo "✅ 포트 8000 프로세스 종료 완료"
    echo "📝 이제 http://localhost:3000/docs 에서 모든 문서를 확인할 수 있습니다."
else
    echo "❌ 종료 취소됨"
    exit 1
fi

