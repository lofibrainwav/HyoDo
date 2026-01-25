#!/bin/bash
# 환경 설정 표준화 스크립트

echo "🔧 환경 설정 표준화 시작..."

# WORKSPACE_ROOT 설정
export WORKSPACE_ROOT="/Users/brnestrm/AFO_Kingdom"
echo "export WORKSPACE_ROOT=\"$WORKSPACE_ROOT\"" >> ~/.zshrc

# PYTHONPATH 정리 및 표준화
export PYTHONPATH="$WORKSPACE_ROOT/packages/afo-core:$WORKSPACE_ROOT/packages/trinity-os"
echo "export PYTHONPATH=\"$PYTHONPATH\"" >> ~/.zshrc

# .env 파일 생성
cat > .env << ENV_EOF
WORKSPACE_ROOT=$WORKSPACE_ROOT
PYTHONPATH=$PYTHONPATH
AFO_ENV=dev
ENV_EOF

echo "✅ 환경 설정 완료"
echo "   WORKSPACE_ROOT: $WORKSPACE_ROOT"
echo "   PYTHONPATH: $PYTHONPATH"