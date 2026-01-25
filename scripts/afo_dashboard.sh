#!/usr/bin/env bash
# AFO Kingdom Dashboard Status Card
# Usage: ./scripts/afo_dashboard.sh
# Displays a unified status card with all key metrics

set -euo pipefail
trap 'echo "❌ Dashboard failed at line $LINENO"; exit 1' ERR

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get data
HEAD=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")

# Trinity Score
TRINITY_SCORE="0.0"
ORGANS_HEALTHY="0"
ORGANS_TOTAL="0"
TRINITY_STATUS="❓"

if curl -sS http://localhost:8010/health &>/dev/null; then
    HEALTH_JSON=$(curl -sS http://localhost:8010/health 2>/dev/null)
    TRINITY_SCORE=$(echo "$HEALTH_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('trinity',{}).get('trinity_score', 0))" 2>/dev/null || echo "0")
    ORGANS_HEALTHY=$(echo "$HEALTH_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('healthy_organs', 0))" 2>/dev/null || echo "0")
    ORGANS_TOTAL=$(echo "$HEALTH_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total_organs', 0))" 2>/dev/null || echo "0")
    
    # Calculate percentage
    if (( $(echo "$TRINITY_SCORE >= 0.9" | bc -l 2>/dev/null || echo "0") )); then
        TRINITY_STATUS="✅"
    else
        TRINITY_STATUS="⚠️"
    fi
fi

# Last seal
LAST_SEAL=$(find artifacts -maxdepth 1 \( -name "seal_*" -o -name "ssot_*" \) -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -n 1 | cut -d' ' -f2- || echo "none")
LAST_SEAL_TIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$LAST_SEAL" 2>/dev/null || echo "N/A")

# Last drift check
DRIFT_STATUS="✅"
if [[ -f artifacts/drift/drift_status.txt ]]; then
    if grep -q "DRIFT" artifacts/drift/drift_status.txt 2>/dev/null; then
        DRIFT_STATUS="⚠️ DRIFT"
    fi
fi

# Count scripts and workflows
SCRIPT_COUNT=$(find scripts -maxdepth 1 -name "*.sh" 2>/dev/null | wc -l | tr -d ' ')
WORKFLOW_COUNT=$(find .github/workflows -maxdepth 1 -name "*.yml" 2>/dev/null | wc -l | tr -d ' ')

# Display card
echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}          ${YELLOW}🏰 AFO Kingdom Dashboard${NC}                              ${CYAN}║${NC}"
echo -e "${CYAN}╠═══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║${NC}                                                               ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  ${BLUE}📊 Trinity Score${NC}    ${TRINITY_STATUS} $(printf "%.1f%%" "$(echo "$TRINITY_SCORE * 100" | bc 2>/dev/null || echo "0")") (Organs: ${ORGANS_HEALTHY}/${ORGANS_TOTAL})          ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}                                                               ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  ${BLUE}🔧 Git Status${NC}                                               ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}     HEAD:   ${GREEN}${HEAD}${NC}                                           ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}     Branch: ${GREEN}${BRANCH}${NC}                                             ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}     Tag:    ${GREEN}${LAST_TAG}${NC}                                  ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}                                                               ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  ${BLUE}📦 Infrastructure${NC}                                          ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}     Scripts:   ${SCRIPT_COUNT} files                                       ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}     Workflows: ${WORKFLOW_COUNT} files                                       ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}                                                               ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  ${BLUE}🔐 SSOT Status${NC}                                              ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}     Drift:     ${DRIFT_STATUS}                                            ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}     Last Seal: ${LAST_SEAL_TIME}                               ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}                                                               ${CYAN}║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
