#!/bin/bash
# AFO 왕국 코드 품질 체크 스크립트 (병렬 실행)
# ruff, pytest, mypy 병렬 실행

set -e

PYTHON_CMD="$(python - <<'PY'
import sys
print(sys.executable)
PY
)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AFO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$AFO_ROOT"

echo "=== 🔍 AFO 왕국 코드 품질 체크 (병렬 실행) ==="
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 임시 파일 디렉토리
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

# 결과 추적
FAILED=0

# 도구 설치 확인 및 설치 함수
install_tool() {
    local tool=$1
    local package=$2
    
    if ! (command -v "$tool" &> /dev/null || "$PYTHON_CMD" -m "$tool" --version &> /dev/null 2>&1); then
        echo -e "${YELLOW}⚠️  ${tool}가 설치되지 않았습니다. 설치 중...${NC}"
        "$PYTHON_CMD" -m pip install --user "$package" 2>&1 || "$PYTHON_CMD" -m pip install "$package" 2>&1
    fi
}

# 1. 도구 설치 확인 (순차)
echo "📦 도구 설치 확인 중..."
install_tool ruff ruff
install_tool mypy mypy
install_tool pytest pytest
echo ""

# 2. 병렬 실행 함수들
run_ruff_lint() {
    local output_file="$TMP_DIR/ruff_lint.log"
    echo -e "${BLUE}📋 [병렬] Ruff Lint 체크 시작...${NC}"
    if "$PYTHON_CMD" -m ruff check . > "$output_file" 2>&1; then
        echo -e "${GREEN}✅ Ruff Lint: 통과${NC}"
        return 0
    else
        cat "$output_file"
        echo -e "${RED}❌ Ruff Lint: 실패${NC}"
        return 1
    fi
}

run_ruff_format() {
    local output_file="$TMP_DIR/ruff_format.log"
    echo -e "${BLUE}📋 [병렬] Ruff Format 체크 시작...${NC}"
    if "$PYTHON_CMD" -m ruff format --check . > "$output_file" 2>&1; then
        echo -e "${GREEN}✅ Ruff Format: 통과${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Ruff Format: 포맷팅 필요${NC}"
        echo "   다음 명령으로 자동 포맷팅: ruff format ."
        return 0  # 경고만, 실패로 처리하지 않음
    fi
}

run_mypy() {
    local output_file="$TMP_DIR/mypy.log"
    echo -e "${BLUE}📋 [병렬] MyPy 타입 체크 시작...${NC}"
    if "$PYTHON_CMD" -m mypy AFO --ignore-missing-imports > "$output_file" 2>&1; then
        echo -e "${GREEN}✅ MyPy: 통과${NC}"
        return 0
    else
        cat "$output_file"
        echo -e "${RED}❌ MyPy: 실패${NC}"
        return 1
    fi
}

run_pytest() {
    local output_file="$TMP_DIR/pytest.log"
    echo -e "${BLUE}📋 [병렬] Pytest 테스트 시작...${NC}"
    
    if [ ! -d "tests" ] || [ "$(find tests -name 'test_*.py' -o -name '*_test.py' 2>/dev/null | wc -l)" -eq 0 ]; then
        echo -e "${YELLOW}⚠️  테스트 파일이 없습니다. tests/ 디렉토리를 생성하세요.${NC}"
        return 0
    fi
    
    if "$PYTHON_CMD" -m pytest tests -v > "$output_file" 2>&1; then
        echo -e "${GREEN}✅ Pytest: 통과${NC}"
        return 0
    else
        cat "$output_file"
        echo -e "${RED}❌ Pytest: 실패${NC}"
        return 1
    fi
}

# 3. 병렬 실행
echo "🚀 병렬 실행 시작..."
echo ""

# 백그라운드로 실행하고 PID 저장
run_ruff_lint &
RUFF_LINT_PID=$!

run_ruff_format &
RUFF_FORMAT_PID=$!

run_mypy &
MYPY_PID=$!

run_pytest &
PYTEST_PID=$!

# 모든 프로세스 완료 대기
wait $RUFF_LINT_PID
RUFF_LINT_RESULT=$?

wait $RUFF_FORMAT_PID
RUFF_FORMAT_RESULT=$?

wait $MYPY_PID
MYPY_RESULT=$?

wait $PYTEST_PID
PYTEST_RESULT=$?

echo ""

# 결과 집계
if [ $RUFF_LINT_RESULT -ne 0 ]; then
    FAILED=1
fi

if [ $MYPY_RESULT -ne 0 ]; then
    FAILED=1
fi

if [ $PYTEST_RESULT -ne 0 ]; then
    FAILED=1
fi

# 최종 결과
echo "=== 🏁 최종 결과 ==="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✨ 모든 코드 품질 체크 통과!${NC}"
    exit 0
else
    echo -e "${RED}❌ 일부 체크 실패${NC}"
    exit 1
fi
