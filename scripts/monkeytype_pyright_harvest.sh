#!/bin/bash
# scripts/monkeytype_pyright_harvest.sh
set -euo pipefail

# AFO 왕국 MonkeyType + Pyright 통합 수확 스크립트
# 1. MonkeyType으로 런타임 타입 수집
# 2. 수집된 타입을 코드에 적용
# 3. Pyright로 타입 안전성 즉시 검증

echo "=== 🐵 Phase 28: MonkeyType + Pyright 통합 수확 시작 ==="

# 1. MonkeyType 수집
export MONKEYTYPE_TRACEBACKS=1
export MONKEYTYPE_MAX_TRACEBACKS=80

echo "[Step 1] MonkeyType 수집 중..."
# trinity 관련 테스트를 실행하여 타입 수집
pytest --monkeytype-output=monkeytype_harvest.sqlite3 \
  packages/afo-core/tests/test_trinity*.py -v --tb=short

# 2. 타입 적용
echo "[Step 2] 수집된 타입 적용 중..."
# 핵심 도메인 로직에 타입 적용
monkeytype apply AFO.domain.metrics.trinity

# 3. 즉시 Pyright 검증
echo "[Step 3] Pyright로 타입 검증 중..."
# trinity.py 파일 검증
npx pyright packages/afo-core/AFO/domain/metrics/trinity.py

echo "=== 🏯 수확 및 검증 완료! ==="
echo "git diff를 통해 변경사항을 확인하고 커밋하세요."
