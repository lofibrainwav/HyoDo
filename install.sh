#!/bin/bash

# ─────────────────────────────────────────────────────────────────
# HyoDo (孝道) 설치 스크립트
# "세종대왕의 정신: 백성을 위한 실용적 혁신"
# ─────────────────────────────────────────────────────────────────

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 아이콘
SWORD="⚔️"
SHIELD="🛡️"
BRIDGE="🌉"
CHECK="✅"
CROSS="❌"
WARN="⚠️"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}     HyoDo (孝道) - AFO Kingdom Plugin Installer        ${NC}"
echo -e "${BLUE}         v3.0.0-ultrawork                               ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# ─────────────────────────────────────────────────────────────────
# 眞 (Truth) - 시스템 요구사항 확인
# ─────────────────────────────────────────────────────────────────

echo -e "${SWORD} ${YELLOW}[眞] 시스템 요구사항 확인...${NC}"

# Git 확인
if command -v git &> /dev/null; then
    echo -e "  ${CHECK} Git: $(git --version)"
else
    echo -e "  ${CROSS} Git이 설치되어 있지 않습니다"
    exit 1
fi

# Claude Code 확인 (선택)
if command -v claude &> /dev/null; then
    echo -e "  ${CHECK} Claude Code: 설치됨"
else
    echo -e "  ${WARN} Claude Code가 설치되어 있지 않습니다 (선택)"
fi

echo ""

# ─────────────────────────────────────────────────────────────────
# 善 (Goodness) - 안전한 설치
# ─────────────────────────────────────────────────────────────────

echo -e "${SHIELD} ${YELLOW}[善] 안전한 설치 진행...${NC}"

# 설치 디렉토리
INSTALL_DIR="${HOME}/.hyodo"

# 기존 설치 확인
if [ -d "$INSTALL_DIR" ]; then
    echo -e "  ${WARN} 기존 설치 발견: $INSTALL_DIR"
    read -p "  덮어쓸까요? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo -e "  ${CROSS} 설치 취소"
        exit 0
    fi
    rm -rf "$INSTALL_DIR"
fi

# 클론
echo -e "  ${CHECK} 레포지토리 클론 중..."
git clone --depth 1 https://github.com/lofibrainwav/HyoDo.git "$INSTALL_DIR" 2>/dev/null

echo ""

# ─────────────────────────────────────────────────────────────────
# 美 (Beauty) - 환경 설정
# ─────────────────────────────────────────────────────────────────

echo -e "${BRIDGE} ${YELLOW}[美] 환경 설정...${NC}"

# .env 파일 생성
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
    echo -e "  ${CHECK} .env 파일 생성됨"
    echo -e "  ${WARN} ANTHROPIC_API_KEY를 .env에 설정하세요"
fi

# pre-commit 설정 (선택)
if command -v pre-commit &> /dev/null; then
    cd "$INSTALL_DIR"
    pre-commit install 2>/dev/null || true
    echo -e "  ${CHECK} pre-commit hooks 설치됨"
fi

echo ""

# ─────────────────────────────────────────────────────────────────
# 설치 완료
# ─────────────────────────────────────────────────────────────────

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}     설치 완료!                                         ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "설치 경로: ${BLUE}$INSTALL_DIR${NC}"
echo ""
echo -e "다음 단계:"
echo -e "  1. ${YELLOW}cd $INSTALL_DIR${NC}"
echo -e "  2. ${YELLOW}편집: .env 파일에 ANTHROPIC_API_KEY 설정${NC}"
echo -e "  3. ${YELLOW}/trinity \"test\"${NC} - Trinity Score 확인"
echo ""
echo -e "문서:"
echo -e "  - QUICK_START.md: ${BLUE}$INSTALL_DIR/QUICK_START.md${NC}"
echo -e "  - README.md: ${BLUE}$INSTALL_DIR/README.md${NC}"
echo ""
echo -e "${BLUE}\"전략가가 지휘하고, 무장이 실행한다\"${NC}"
echo ""
