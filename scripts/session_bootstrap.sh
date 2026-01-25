#!/bin/bash
# Kingdom Session Bootstrap (眞善美孝永)
# 세션 시작 시 Identity Memory에서 핵심 컨텍스트 로드
#
# Usage:
#   source scripts/session_bootstrap.sh
#   # 또는
#   ./scripts/session_bootstrap.sh > /tmp/afo_identity.md

KINGDOM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$KINGDOM_ROOT/packages/afo-core" || exit 1

echo "🏰 AFO Kingdom Identity Bootstrap"
echo "================================="
echo ""

# Python 스크립트 실행
python scripts/kingdom_identity_memory.py --bootstrap 2>/dev/null

echo ""
echo "================================="
echo "✅ Identity Context Loaded"
