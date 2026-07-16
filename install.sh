#!/bin/bash
# HyoDo non-interactive installer (English)
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CHECK="OK"
CROSS="ERR"
WARN="WARN"

echo ""
echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}     HyoDo installer${NC}"
echo -e "${BLUE}         v3.1.2${NC}"
echo -e "${BLUE}=======================================================${NC}"
echo ""

echo -e "${YELLOW}[1/3] Checking requirements...${NC}"

if command -v git &>/dev/null; then
    echo -e "  ${CHECK} Git: $(git --version)"
else
    echo -e "  ${CROSS} Git is required"
    exit 1
fi

if command -v python3 &>/dev/null; then
    echo -e "  ${CHECK} Python: $(python3 --version 2>&1)"
else
    echo -e "  ${WARN} Python 3 not found (needed for hyodo CLI)"
fi

if command -v claude &>/dev/null; then
    echo -e "  ${CHECK} Claude Code: found (optional)"
else
    echo -e "  ${WARN} Claude Code not found (optional adapter)"
fi

echo ""
echo -e "${YELLOW}[2/3] Installing to ~/.hyodo ...${NC}"

INSTALL_DIR="${HOME}/.hyodo"

if [ -d "$INSTALL_DIR" ]; then
    echo -e "  ${WARN} Existing install found: $INSTALL_DIR"
    read -r -p "  Overwrite? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo -e "  ${CROSS} Install cancelled"
        exit 0
    fi
    rm -rf "$INSTALL_DIR"
fi

echo -e "  ${CHECK} Cloning repository..."
git clone --depth 1 https://github.com/lofibrainwav/HyoDo.git "$INSTALL_DIR"

echo ""
echo -e "${YELLOW}[3/3] Writing config...${NC}"

if [ ! -f "$INSTALL_DIR/.env" ]; then
    if [ -f "$INSTALL_DIR/.env.minimal" ]; then
        cp "$INSTALL_DIR/.env.minimal" "$INSTALL_DIR/.env"
    elif [ -f "$INSTALL_DIR/.env.example" ]; then
        cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
    fi
    echo -e "  ${CHECK} .env created"
    echo -e "  ${WARN} Provider keys are optional for local CLI gates"
fi

if command -v pre-commit &>/dev/null; then
    cd "$INSTALL_DIR"
    pre-commit install 2>/dev/null || true
    echo -e "  ${CHECK} pre-commit hooks installed"
fi

echo ""
echo -e "${GREEN}=======================================================${NC}"
echo -e "${GREEN}     Install complete${NC}"
echo -e "${GREEN}=======================================================${NC}"
echo ""
echo -e "Path: ${BLUE}$INSTALL_DIR${NC}"
echo ""
echo -e "Next:"
echo -e "  1. ${YELLOW}cd $INSTALL_DIR && pip install -e \".[dev]\"${NC}"
echo -e "  2. ${YELLOW}hyodo check${NC}"
echo -e "  3. ${YELLOW}hyodo safe${NC}"
echo ""
echo -e "Docs: README.md, QUICK_START_SIMPLE.md"
echo ""
