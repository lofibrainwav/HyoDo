#!/bin/bash
# ============================================================================
# AFO Kingdom - Self-hosted Runner Setup Script
# Purpose: GitHub Actions Self-hosted Runner 설치 및 구성
# Platform: macOS (Apple Silicon)
# ============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
RUNNER_DIR="$HOME/actions-runner"
REPO_URL="https://github.com/lofibrainwav/AFO_Kingdom"
RUNNER_VERSION="2.322.0"  # Check latest: https://github.com/actions/runner/releases

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}🏃 AFO Kingdom Self-hosted Runner Setup${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ============================================================================
# Step 1: Prerequisites Check
# ============================================================================
echo -e "${YELLOW}[1/5] Checking prerequisites...${NC}"

# Check if running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo -e "${RED}❌ This script is for macOS only${NC}"
    exit 1
fi

# Check architecture
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    RUNNER_ARCH="osx-arm64"
    echo -e "  ✅ Architecture: Apple Silicon (arm64)"
else
    RUNNER_ARCH="osx-x64"
    echo -e "  ✅ Architecture: Intel (x64)"
fi

# Check gh CLI
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) not found. Install with: brew install gh${NC}"
    exit 1
fi
echo -e "  ✅ GitHub CLI available"

# Check authentication
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ Not authenticated with GitHub CLI. Run: gh auth login${NC}"
    exit 1
fi
echo -e "  ✅ GitHub CLI authenticated"
echo ""

# ============================================================================
# Step 2: Get Registration Token
# ============================================================================
echo -e "${YELLOW}[2/5] Getting registration token...${NC}"

REGISTRATION_TOKEN=$(gh api \
    --method POST \
    -H "Accept: application/vnd.github+json" \
    /repos/lofibrainwav/AFO_Kingdom/actions/runners/registration-token \
    --jq '.token')

if [[ -z "$REGISTRATION_TOKEN" ]]; then
    echo -e "${RED}❌ Failed to get registration token${NC}"
    exit 1
fi
echo -e "  ✅ Registration token obtained"
echo ""

# ============================================================================
# Step 3: Download and Extract Runner
# ============================================================================
echo -e "${YELLOW}[3/5] Setting up runner directory...${NC}"

# Create runner directory
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

# Download runner if not exists
RUNNER_TAR="actions-runner-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"
if [[ ! -f "$RUNNER_TAR" ]]; then
    echo -e "  Downloading runner v${RUNNER_VERSION}..."
    curl -sL -o "$RUNNER_TAR" \
        "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_TAR}"
    echo -e "  ✅ Downloaded"
else
    echo -e "  ✅ Runner archive already exists"
fi

# Extract if not already done
if [[ ! -f "./config.sh" ]]; then
    echo -e "  Extracting..."
    tar xzf "$RUNNER_TAR"
    echo -e "  ✅ Extracted"
else
    echo -e "  ✅ Runner already extracted"
fi
echo ""

# ============================================================================
# Step 4: Configure Runner
# ============================================================================
echo -e "${YELLOW}[4/5] Configuring runner...${NC}"

# Check if already configured
if [[ -f ".runner" ]]; then
    echo -e "  ${YELLOW}⚠️  Runner already configured. Reconfigure? (y/N)${NC}"
    read -r RECONFIGURE
    if [[ "$RECONFIGURE" != "y" ]]; then
        echo -e "  Skipping configuration"
    else
        ./config.sh remove --token "$REGISTRATION_TOKEN" || true
        ./config.sh --url "$REPO_URL" \
            --token "$REGISTRATION_TOKEN" \
            --name "afo-kingdom-runner" \
            --labels "self-hosted,macOS,ARM64,afo" \
            --work "_work" \
            --unattended
    fi
else
    ./config.sh --url "$REPO_URL" \
        --token "$REGISTRATION_TOKEN" \
        --name "afo-kingdom-runner" \
        --labels "self-hosted,macOS,ARM64,afo" \
        --work "_work" \
        --unattended
fi
echo -e "  ✅ Runner configured"
echo ""

# ============================================================================
# Step 5: Install as Service (launchd)
# ============================================================================
echo -e "${YELLOW}[5/5] Installing as service...${NC}"

# Create launchd plist
PLIST_PATH="$HOME/Library/LaunchAgents/com.github.actions.runner.plist"
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.github.actions.runner</string>
    <key>ProgramArguments</key>
    <array>
        <string>${RUNNER_DIR}/run.sh</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${RUNNER_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${RUNNER_DIR}/runner.log</string>
    <key>StandardErrorPath</key>
    <string>${RUNNER_DIR}/runner.error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

echo -e "  ✅ Launchd plist created: $PLIST_PATH"

# Load the service
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"
echo -e "  ✅ Service loaded"
echo ""

# ============================================================================
# Summary
# ============================================================================
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✅ Self-hosted Runner Setup Complete!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "Runner Directory: ${RUNNER_DIR}"
echo -e "Runner Name: afo-kingdom-runner"
echo -e "Labels: self-hosted, macOS, ARM64, afo"
echo ""
echo -e "${YELLOW}Management Commands:${NC}"
echo -e "  Start:   launchctl load ~/Library/LaunchAgents/com.github.actions.runner.plist"
echo -e "  Stop:    launchctl unload ~/Library/LaunchAgents/com.github.actions.runner.plist"
echo -e "  Status:  gh api /repos/lofibrainwav/AFO_Kingdom/actions/runners"
echo -e "  Logs:    tail -f ${RUNNER_DIR}/runner.log"
echo ""
echo -e "${YELLOW}Workflow Usage:${NC}"
echo -e "  runs-on: [self-hosted, macOS, ARM64]"
echo ""
