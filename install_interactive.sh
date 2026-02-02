#!/bin/bash

# ─────────────────────────────────────────────────────────────────
# HyoDo (孝道) 대화형 설치 스크립트
# "세종대왕의 정신: 백성을 위한 실용적 혁신"
# 버전: v3.1.0-beginner-friendly
# ─────────────────────────────────────────────────────────────────

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 아이콘
SWORD="⚔️"
SHIELD="🛡️"
BRIDGE="🌉"
CHECK="✅"
CROSS="❌"
WARN="⚠️"
ROCKET="🚀"
BOOK="📚"
GEAR="⚙️"

# 기본 설정
INSTALL_DIR="${HOME}/.hyodo"
MINIMAL_MODE=false
SKIP_OLLAMA=true
API_KEY=""

# ─────────────────────────────────────────────────────────────────
# 헬퍼 함수
# ─────────────────────────────────────────────────────────────────

print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}     HyoDo (孝道) - 초보자용 대화형 설치${NC}"
    echo -e "${BLUE}         v3.1.0-beginner-friendly${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}HyoDo는 AI 코드 품질 자동화 도구입니다.${NC}"
    echo -e "${CYAN}5분이면 설치 완료!${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}[${1}/${2}]${NC} ${3}"
}

ask_yes_no() {
    local prompt="$1"
    local default="${2:-y}"
    
    while true; do
        if [ "$default" = "y" ]; then
            read -p "$prompt [Y/n]: " yn
            yn=${yn:-Y}
        else
            read -p "$prompt [y/N]: " yn
            yn=${yn:-N}
        fi
        
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Y 또는 N을 입력하세요.";;
        esac
    done
}

# ─────────────────────────────────────────────────────────────────
# 1단계: 환영 및 모드 선택
# ─────────────────────────────────────────────────────────────────

step_welcome() {
    print_step "1" "5" "${ROCKET} 설치 모드 선택"
    echo ""
    
    echo -e "${CYAN}설치 모드를 선택하세요:${NC}"
    echo ""
    echo -e "  ${GREEN}1) 최소 설치 (추천)${NC}"
    echo "     - Claude Code만 필요"
    echo "     - 2분 완료"
    echo "     - 기본 기능만 사용"
    echo ""
    echo -e "  ${YELLOW}2) 전체 설치${NC}"
    echo "     - Redis + PostgreSQL + Ollama 필요"
    echo "     - 10분 완료"
    echo "     - 모든 기능 사용"
    echo ""
    
    read -p "선택 (1 또는 2): " mode_choice
    
    case $mode_choice in
        1)
            MINIMAL_MODE=true
            echo -e "\n${GREEN}✓ 최소 설치 모드 선택됨${NC}"
            ;;
        2)
            MINIMAL_MODE=false
            echo -e "\n${GREEN}✓ 전체 설치 모드 선택됨${NC}"
            ;;
        *)
            MINIMAL_MODE=true
            echo -e "\n${YELLOW}⚠ 기본값(최소 설치)으로 진행합니다${NC}"
            ;;
    esac
    
    echo ""
}

# ─────────────────────────────────────────────────────────────────
# 2단계: 시스템 요구사항 확인
# ─────────────────────────────────────────────────────────────────

step_requirements() {
    print_step "2" "5" "${GEAR} 시스템 확인"
    echo ""
    
    local all_ok=true
    
    # Git 확인
    if command -v git &> /dev/null; then
        echo -e "  ${CHECK} Git: $(git --version)"
    else
        echo -e "  ${CROSS} ${RED}Git이 설치되어 있지 않습니다${NC}"
        echo -e "     ${CYAN}→ 설치: https://git-scm.com/downloads${NC}"
        all_ok=false
    fi
    
    # Python 확인
    if command -v python3 &> /dev/null; then
        local py_version=$(python3 --version 2>&1 | awk '{print $2}')
        echo -e "  ${CHECK} Python: $py_version"
        
        # 버전 체크 (3.10+)
        local major=$(echo $py_version | cut -d. -f1)
        local minor=$(echo $py_version | cut -d. -f2)
        if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 10 ]); then
            echo -e "  ${WARN} ${YELLOW}Python 3.10+ 권장${NC}"
        fi
    else
        echo -e "  ${CROSS} ${RED}Python이 설치되어 있지 않습니다${NC}"
        all_ok=false
    fi
    
    # Claude Code 확인
    if command -v claude &> /dev/null; then
        echo -e "  ${CHECK} Claude Code: 설치됨"
    else
        echo -e "  ${WARN} Claude Code: 미설치 (선택사항)"
        echo -e "     ${CYAN}→ 설치: https://claude.ai/code${NC}"
    fi
    
    # 전체 설치 시 추가 확인
    if [ "$MINIMAL_MODE" = false ]; then
        echo ""
        echo -e "${YELLOW}전체 설치 모드 추가 확인:${NC}"
        
        # Docker 확인
        if command -v docker &> /dev/null; then
            echo -e "  ${CHECK} Docker: $(docker --version | awk '{print $3}' | sed 's/,//')"
        else
            echo -e "  ${CROSS} ${RED}Docker가 필요합니다${NC}"
            echo -e "     ${CYAN}→ 설치: https://docs.docker.com/get-docker/${NC}"
            all_ok=false
        fi
        
        # Docker Compose 확인
        if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
            echo -e "  ${CHECK} Docker Compose: 설치됨"
        else
            echo -e "  ${WARN} Docker Compose: 확인 필요"
        fi
    fi
    
    if [ "$all_ok" = false ]; then
        echo ""
        echo -e "${RED}필수 요구사항이 충족되지 않았습니다. 설치를 중단합니다.${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}✓ 모든 요구사항 충족!${NC}"
    echo ""
}

# ─────────────────────────────────────────────────────────────────
# 3단계: API 키 설정
# ─────────────────────────────────────────────────────────────────

step_api_key() {
    print_step "3" "5" "${SHIELD} API 키 설정"
    echo ""
    
    echo -e "${CYAN}Anthropic API 키가 필요합니다.${NC}"
    echo -e "${CYAN}→ 키 발급: https://console.anthropic.com/${NC}"
    echo ""
    
    while true; do
        read -sp "API 키 입력 (sk-ant-...): " API_KEY
        echo ""
        
        if [[ $API_KEY == sk-ant-* ]]; then
            echo -e "${GREEN}✓ 유효한 API 키 형식입니다${NC}"
            break
        elif [ -z "$API_KEY" ]; then
            echo -e "${YELLOW}⚠ 나중에 .env 파일에 직접 입력할 수 있습니다${NC}"
            if ask_yes_no "지금 설정을 건너뛸까요?" "n"; then
                API_KEY="YOUR_API_KEY_HERE"
                break
            fi
        else
            echo -e "${YELLOW}⚠ API 키 형식이 올바르지 않습니다 (sk-ant-...로 시작)${NC}"
            if ask_yes_no "그대로 진행할까요?" "n"; then
                break
            fi
        fi
    done
    
    echo ""
}

# ─────────────────────────────────────────────────────────────────
# 4단계: 설치 실행
# ─────────────────────────────────────────────────────────────────

step_install() {
    print_step "4" "5" "${SWORD} 설치 진행"
    echo ""
    
    # 기존 설치 확인
    if [ -d "$INSTALL_DIR" ]; then
        echo -e "${WARN} 기존 설치 발견: $INSTALL_DIR"
        if ask_yes_no "덮어쓸까요?" "n"; then
            rm -rf "$INSTALL_DIR"
            echo -e "${CHECK} 기존 설치 제거됨"
        else
            echo -e "${YELLOW}설치 취소${NC}"
            exit 0
        fi
    fi
    
    # 클론
    echo -e "${CYAN}레포지토리 다운로드 중...${NC}"
    if git clone --depth 1 https://github.com/lofibrainwav/HyoDo.git "$INSTALL_DIR" 2>/dev/null; then
        echo -e "${CHECK} 다운로드 완료"
    else
        echo -e "${CROSS} ${RED}다운로드 실패. 인터넷 연결을 확인하세요.${NC}"
        exit 1
    fi
    
    # .env 파일 생성
    echo -e "${CYAN}환경 설정 파일 생성 중...${NC}"
    
    if [ "$MINIMAL_MODE" = true ]; then
        # 최소 설치용 .env
        cat > "$INSTALL_DIR/.env" << EOF
# HyoDo 최소 설치 설정
# 생성일: $(date)

# Claude API (필수)
ANTHROPIC_API_KEY=$API_KEY

# 기본 설정
DEFAULT_COST_TIER=FREE
TRINITY_AUTO_RUN_THRESHOLD=90
TRINITY_ASK_COMMANDER_THRESHOLD=70
SAFETY_GATE_ENABLED=true
EVIDENCE_LOG_ENABLED=true
METRICS_ENABLED=true
DEBUG=false
LOG_LEVEL=INFO
EOF
    else
        # 전체 설치용 .env (기존 예시 복사 후 수정)
        cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
        sed -i '' "s/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$API_KEY/" "$INSTALL_DIR/.env" 2>/dev/null || \
        sed -i "s/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$API_KEY/" "$INSTALL_DIR/.env"
    fi
    
    echo -e "${CHECK} .env 파일 생성 완료"
    
    # Python 패키지 설치 (선택)
    if ask_yes_no "Python 패키지를 지금 설치할까요?" "y"; then
        echo -e "${CYAN}패키지 설치 중...${NC}"
        cd "$INSTALL_DIR"
        if pip install -e "." 2>/dev/null; then
            echo -e "${CHECK} 패키지 설치 완료"
        else
            echo -e "${WARN} 패키지 설치 실패 (나중에 수동으로: pip install -e .)"
        fi
    fi
    
    echo ""
}

# ─────────────────────────────────────────────────────────────────
# 5단계: 완료 및 다음 단계
# ─────────────────────────────────────────────────────────────────

step_finish() {
    print_step "5" "5" "${ROCKET} 설치 완료!"
    echo ""
    
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}     🎉 HyoDo 설치가 완료되었습니다!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo ""
    
    echo -e "${CYAN}📍 설치 경로:${NC} ${INSTALL_DIR}"
    echo ""
    
    echo -e "${CYAN}🚀 바로 시작하기:${NC}"
    echo ""
    echo -e "  ${YELLOW}1) Claude Code 열기:${NC}"
    echo -e "     ${GREEN}cd $INSTALL_DIR && claude${NC}"
    echo ""
    echo -e "  ${YELLOW}2) 첫 명령어 실행:${NC}"
    echo -e "     ${GREEN}/start${NC}    - 시작 가이드"
    echo -e "     ${GREEN}/check${NC}    - 코드 품질 검사"
    echo -e "     ${GREEN}/score${NC}    - Trinity Score 확인"
    echo ""
    
    if [ "$MINIMAL_MODE" = false ]; then
        echo -e "  ${YELLOW}3) 인프라 시작 (전체 설치):${NC}"
        echo -e "     ${GREEN}cd $INSTALL_DIR && docker-compose up -d${NC}"
        echo ""
    fi
    
    echo -e "${CYAN}📚 더 알아보기:${NC}"
    echo -e "  - 퀵스타트: ${INSTALL_DIR}/QUICK_START.md"
    echo -e "  - README:   ${INSTALL_DIR}/README.md"
    echo -e "  - 도움말:   ${INSTALL_DIR}/docs/"
    echo ""
    
    if [ "$API_KEY" = "YOUR_API_KEY_HERE" ]; then
        echo -e "${YELLOW}⚠️  알림: API 키를 설정해야 합니다${NC}"
        echo -e "   ${CYAN}→ $INSTALL_DIR/.env 파일을 편집하세요${NC}"
        echo ""
    fi
    
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  "지피지기 백전백승" - HyoDo와 함께 코드 품질을 향상시켜보세요!${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

# ─────────────────────────────────────────────────────────────────
# 메인 실행
# ─────────────────────────────────────────────────────────────────

main() {
    print_header
    step_welcome
    step_requirements
    step_api_key
    step_install
    step_finish
}

# 스크립트 실행
main "$@"
