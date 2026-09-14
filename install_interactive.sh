#!/bin/bash
# HyoDo interactive installer (English)
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

CHECK="OK"
CROSS="ERR"
WARN="WARN"

INSTALL_DIR="${HOME}/.hyodo"
API_KEY=""
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

print_header() {
    echo ""
    echo -e "${BLUE}=======================================================${NC}"
    echo -e "${BLUE}     HyoDo interactive installer${NC}"
    echo -e "${BLUE}         ${HYODO_VERSION}${NC}"
    echo -e "${BLUE}=======================================================${NC}"
    echo ""
    echo -e "${CYAN}HyoDo is a model-agnostic quality-gate kit for AI-assisted code.${NC}"
    echo -e "${CYAN}Public path: Python + CLI. No container runtime is required.${NC}"
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
            read -r -p "$prompt [Y/n]: " yn
            yn=${yn:-Y}
        else
            read -r -p "$prompt [y/N]: " yn
            yn=${yn:-N}
        fi

        case $yn in
            [Yy]*) return 0 ;;
            [Nn]*) return 1 ;;
            *) echo "Please enter Y or N." ;;
        esac
    done
}

step_welcome() {
    print_step "1" "5" "Public CLI installation"
    echo ""
    echo -e "${GREEN}Python 3.10+ and the public HyoDo CLI will be installed.${NC}"
    echo ""
}

step_requirements() {
    print_step "2" "5" "Check system requirements"
    echo ""

    local all_ok=true

    if command -v git &>/dev/null; then
        echo -e "  ${CHECK} Git: $(git --version)"
    else
        echo -e "  ${CROSS} ${RED}Git is required${NC}"
        echo -e "     ${CYAN}-> https://git-scm.com/downloads${NC}"
        all_ok=false
    fi

    if command -v python3 &>/dev/null; then
        local py_version
        py_version=$(python3 --version 2>&1 | awk '{print $2}')
        echo -e "  ${CHECK} Python: $py_version"
        local major minor
        major=$(echo "$py_version" | cut -d. -f1)
        minor=$(echo "$py_version" | cut -d. -f2)
        if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 10 ]; }; then
            echo -e "  ${WARN} ${YELLOW}Python 3.10+ recommended${NC}"
        fi
    else
        echo -e "  ${CROSS} ${RED}Python 3 is required${NC}"
        all_ok=false
    fi

    if command -v claude &>/dev/null; then
        echo -e "  ${CHECK} Claude Code: found (optional adapter)"
    else
        echo -e "  ${WARN} Claude Code: not found (optional)"
    fi

    if [ "$all_ok" = false ]; then
        echo ""
        echo -e "${RED}Required tools are missing. Aborting.${NC}"
        exit 1
    fi

    echo ""
    echo -e "${GREEN}${CHECK} Requirements satisfied${NC}"
    echo ""
}

step_api_key() {
    print_step "3" "5" "Optional provider API key"
    echo ""
    echo -e "${CYAN}Provider API keys are optional for core CLI gates (check/score/safe).${NC}"
    echo -e "${CYAN}If you use Claude adapters, you may set ANTHROPIC_API_KEY now.${NC}"
    echo -e "${CYAN}-> https://console.anthropic.com/${NC}"
    echo ""

    while true; do
        read -r -sp "API key (sk-ant-... or empty to skip): " API_KEY
        echo ""

        if [[ $API_KEY == sk-ant-* ]]; then
            echo -e "${GREEN}${CHECK} Key format looks valid${NC}"
            break
        elif [ -z "$API_KEY" ]; then
            echo -e "${YELLOW}${WARN} Skipping for now. You can edit .env later.${NC}"
            API_KEY="YOUR_API_KEY_HERE"
            break
        else
            echo -e "${YELLOW}${WARN} Unexpected key format${NC}"
            if ask_yes_no "Continue with this value?" "n"; then
                break
            fi
        fi
    done
    echo ""
}

step_install() {
    print_step "4" "5" "Install"
    echo ""

    if [ -d "$INSTALL_DIR" ]; then
        echo -e "${WARN} Existing install found: $INSTALL_DIR"
        if ask_yes_no "Overwrite?" "n"; then
            rm -rf "$INSTALL_DIR"
            echo -e "${CHECK} Removed previous install"
        else
            echo -e "${YELLOW}Install cancelled${NC}"
            exit 0
        fi
    fi

    echo -e "${CYAN}Cloning repository...${NC}"
    if clone_verified 2>/dev/null; then
        ACTUAL_SHA="$(git -C "$INSTALL_DIR" rev-parse HEAD)"
        if [ "$ACTUAL_SHA" != "$EXPECTED_SHA" ]; then
            echo -e "${CROSS} ${RED}Ref changed during clone; refusing unverified source${NC}"
            exit 1
        fi
        echo -e "${CHECK} Clone complete ($ACTUAL_SHA)"
    else
        echo -e "${CROSS} ${RED}Clone failed. Check network access.${NC}"
        exit 1
    fi

    echo -e "${CYAN}Writing environment file...${NC}"
    cat >"$INSTALL_DIR/.env" <<EOF
# HyoDo minimal install
# Created: $(date)

# Optional provider key (not required for local CLI gates)
ANTHROPIC_API_KEY=$API_KEY

DEFAULT_COST_TIER=FREE
SAFETY_GATE_ENABLED=true
EVIDENCE_LOG_ENABLED=true
METRICS_ENABLED=true
DEBUG=false
LOG_LEVEL=INFO
EOF
    echo -e "${CHECK} .env created"

    if ask_yes_no "Install Python package now (python3 -m pip install .)?" "y"; then
        echo -e "${CYAN}Installing package...${NC}"
        cd "$INSTALL_DIR"
        if python3 -m pip install "." 2>/dev/null; then
            echo -e "${CHECK} Package installed"
        else
            echo -e "${WARN} Package install failed (later: cd $INSTALL_DIR && python3 -m pip install .)"
        fi
    fi
    echo ""
}

step_finish() {
    print_step "5" "5" "Done"
    echo ""
    echo -e "${GREEN}=======================================================${NC}"
    echo -e "${GREEN}     HyoDo install complete${NC}"
    echo -e "${GREEN}=======================================================${NC}"
    echo ""
    echo -e "${CYAN}Install path:${NC} ${INSTALL_DIR}"
    echo ""
    echo -e "${CYAN}Start with the CLI (recommended):${NC}"
    echo -e "  ${GREEN}cd $INSTALL_DIR && python3 -m pip install .${NC}"
    echo -e "  ${GREEN}hyodo check${NC}"
    echo -e "  ${GREEN}hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --hyo 0.9${NC}"
    echo -e "  ${GREEN}hyodo safe${NC}"
    echo ""

    echo -e "${CYAN}Docs:${NC}"
    echo -e "  - $INSTALL_DIR/QUICK_START.md"
    echo -e "  - $INSTALL_DIR/README.md"
    echo -e "  - $INSTALL_DIR/docs/EXTERNAL_CLAIM_AUDIT.md"
    echo ""

    if [ "$API_KEY" = "YOUR_API_KEY_HERE" ]; then
        echo -e "${YELLOW}${WARN} No provider key stored. Edit $INSTALL_DIR/.env if needed.${NC}"
        echo ""
    fi
}

main() {
    print_header
    step_welcome
    step_requirements
    step_api_key
    step_install
    step_finish
}

main "$@"
