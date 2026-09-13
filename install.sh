#!/bin/bash
# HyoDo non-interactive installer (English)
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CHECK="OK"
CROSS="ERR"
WARN="WARN"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -r "$SCRIPT_DIR/VERSION" ]; then
    HYODO_VERSION="v$(tr -d '[:space:]' < "$SCRIPT_DIR/VERSION")"
else
    echo "VERSION is required to select an immutable release ref" >&2
    exit 1
fi
HYODO_REF="${HYODO_REF:-$HYODO_VERSION}"
REPOSITORY_URL="https://github.com/lofibrainwav/HyoDo.git"
if [[ "$HYODO_REF" =~ ^[0-9a-fA-F]{40}$ ]]; then
    EXPECTED_SHA="$HYODO_REF"
else
    EXPECTED_SHA="$(git ls-remote "$REPOSITORY_URL" "refs/tags/$HYODO_REF^{}" | head -n 1 | cut -f1)"
fi
if [ -z "$EXPECTED_SHA" ]; then
    echo "Release tag or 40-character commit SHA not found: $HYODO_REF" >&2
    exit 1
fi
clone_verified() {
    if [[ "$HYODO_REF" =~ ^[0-9a-fA-F]{40}$ ]]; then
        git clone --no-checkout --depth 1 "$REPOSITORY_URL" "$INSTALL_DIR"
        git -C "$INSTALL_DIR" fetch --depth 1 origin "$HYODO_REF"
        git -C "$INSTALL_DIR" checkout --detach "$HYODO_REF"
    else
        git clone --depth 1 --branch "$HYODO_REF" "$REPOSITORY_URL" "$INSTALL_DIR"
    fi
}

echo ""
echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}     HyoDo installer${NC}"
echo -e "${BLUE}         ${HYODO_VERSION}${NC}"
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
clone_verified
ACTUAL_SHA="$(git -C "$INSTALL_DIR" rev-parse HEAD)"
if [ "$ACTUAL_SHA" != "$EXPECTED_SHA" ]; then
    echo "Ref changed during clone; expected $EXPECTED_SHA, got $ACTUAL_SHA" >&2
    exit 1
fi
echo -e "  ${CHECK} Source commit: $ACTUAL_SHA"

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
echo -e "  1. ${YELLOW}cd $INSTALL_DIR && python3 -m pip install .${NC}"
echo -e "  2. ${YELLOW}hyodo check${NC}"
echo -e "  3. ${YELLOW}hyodo safe${NC}"
echo ""
echo -e "Docs: README.md, QUICK_START.md"
echo ""
