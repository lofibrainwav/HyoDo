#!/bin/bash
#
# AFO Kingdom: OpenCode Vault 완벽한 설정 스크립트
# 
# 사용법:
#   ./opencode_vault_setup.sh [login|sync|test]
#
# 기능:
#   - OpenCode 웹 인증 유도
#   - 토큰 VaultManager에 동기화
#   - 환경변수 자동 export
#   - LLM 사용 테스트
#

set -e  # 에러 발생 시 즉시 종료

# ============================================================================
# 환경 설정
# ============================================================================
AFO_CORE="${AFO_KINGDOM:-/Users/brnestrm/AFO_Kingdom/packages/afo-core}"
OPENCODE_AUTH="$HOME/.local/share/opencode/auth.json"
PYTHON_CMD="python3"

# 컬러 출력
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# 헬퍼 함수
# ============================================================================

usage() {
    echo "사용법: $0 [login|sync|test]"
    echo ""
    echo "명령어:"
    echo "  login    - OpenCode 웹 인증 유도"
    echo "  sync     - OpenCode 토큰을 Vault에 동기화"
    echo "  test     - LLM 사용 테스트"
    echo ""
    echo "예시:"
    echo "  $0 login"
    echo "  $0 sync && eval \\\$($0 sync --export)"
    echo "  $0 test"
    exit 1
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# OpenCode 웹 인증 유도 함수
# ============================================================================

opencode_login() {
    log_info "OpenCode 웹 인터페이스를 실행합니다..."
    log_info "브라우저에서 다음 URL을 열어주세요:"
    log_info "http://127.0.0.1:4096"
    log_info ""
    log_info "웹 인증 단계:"
    log_info "  1. OpenCode 웹 접속 후 /connect 또는 연결 메뉴 클릭"
    log_info "  2. OpenAI: 'Connect to OpenAI' 클릭 → ChatGPT 계정 로그인"
    log_info "  3. Anthropic: 'Connect to Anthropic' 클릭 → Claude 계정 로그인"
    log_info "  4. Google Gemini: 이미 구성됨 (opencode.json에 있음)"
    log_info ""
    log_info "인증 완료 후 auth.json 파일에 토큰이 저장됩니다."
    log_info "인증 완료 후 다음 명령을 실행하세요:"
    log_warning "  $0 sync"
}

# ============================================================================
# Vault 동기화 함수
# ============================================================================

vault_sync() {
    local export_mode=${1:-""}
    
    log_info "Vault 동기화를 시작합니다..."
    
    # Python 모듈 실행
    cd "$AFO_CORE"
    $PYTHON_CMD -m AFO.security.vault.opencode_wallet sync_tokens_from_auth_file
    
    if [ $? -eq 0 ]; then
        log_success "Vault 동기화 완료"
    else
        log_error "Vault 동기화 실패"
        return 1
    fi
    
    # export 모드인지 확인
    if [ "$export_mode" == "--export" ]; then
        log_info "환경변수 export 명령을 생성합니다..."
        cd "$AFO_CORE"
        $PYTHON_CMD -m AFO.security.vault.opencode_wallet print_env_export_commands
    fi
}

# ============================================================================
# Vault 상태 확인 함수
# ============================================================================

vault_status() {
    log_info "Vault 상태를 확인합니다..."
    cd "$AFO_CORE"
    $PYTHON_CMD -c "from AFO.security.vault import vault; print(vault.get_status())"
}

# ============================================================================
# LLM 테스트 함수
# ============================================================================

test_llm() {
    log_info "LLM 사용 테스트를 시작합니다..."
    
    # OpenCode 웹 서버 확인
    if ! curl -s http://127.0.0.1:4096 > /dev/null 2>&1; then
        log_warning "OpenCode 웹 서버가 실행 중이지 않습니다."
        log_info "먼저 'opencode web'를 실행해주세요."
        return 1
    fi
    
    # OpenAI 테스트
    log_info "OpenAI (GPT) 테스트 중..."
    opencode --model openai/gpt-5.2 "Hello from OpenAI!" 2>&1 | head -5
    echo ""
    
    # Anthropic Claude 테스트
    log_info "Anthropic (Claude) 테스트 중..."
    opencode --model anthropic/claude-sonnet-4.5 "Hello from Claude!" 2>&1 | head -5
    echo ""
    
    # Google Gemini 테스트
    log_info "Google Gemini 테스트 중..."
    opencode --model google/antigravity-gemini-3-pro-high "Hello from Gemini!" 2>&1 | head -5
    echo ""
    
    # Ollama 테스트
    log_info "Ollama (로컬) 테스트 중..."
    if ollama list 2>/dev/null | grep -q "qwen"; then
        opencode --model ollama/qwen2.5-coder:7b "Hello from Ollama!" 2>&1 | head -5
    else
        log_warning "Ollama에 qwen2.5-coder 모델이 없습니다."
    fi
    
    log_success "LLM 테스트 완료"
}

# ============================================================================
# 메인 로직
# ============================================================================

# 인자 개수 확인
if [ $# -lt 1 ]; then
    usage
fi

COMMAND=$1
shift

# 명령어 처리
case $COMMAND in
    login)
        opencode_login
        ;;
    sync)
        vault_sync "$@"
        ;;
    test)
        test_llm
        ;;
    status)
        vault_status
        ;;
    *)
        log_error "알 수 없는 명령어: $COMMAND"
        usage
        ;;
esac

exit 0
