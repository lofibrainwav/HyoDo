#!/bin/bash
# ============================================================================
# Drift Detector - Agent Resilience Framework (ARF)
# Purpose: SSOT 드리프트 자동 감지 및 경고
# Usage: ./scripts/drift_detector.sh [--fix]
# ============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
WARNINGS=0
ERRORS=0

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}🔍 AFO Kingdom - SSOT Drift Detector${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ============================================================================
# 1. Git Status Check (uncommitted changes)
# ============================================================================
echo -e "${YELLOW}[1/5] Checking uncommitted changes...${NC}"

UNCOMMITTED=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ "$UNCOMMITTED" -gt 0 ]; then
    echo -e "  ${YELLOW}⚠️  $UNCOMMITTED uncommitted changes detected${NC}"

    # Check for SSOT document changes
    SSOT_CHANGES=$(git status --porcelain | grep -E "(CLAUDE|AGENTS|ROYAL_LIBRARY)" || true)
    if [ -n "$SSOT_CHANGES" ]; then
        echo -e "  ${RED}🚨 SSOT documents modified - review required:${NC}"
        echo "$SSOT_CHANGES" | sed 's/^/     /'
        ((ERRORS++))
    fi

    # Check for artifacts drift
    ARTIFACT_CHANGES=$(git status --porcelain | grep -E "^.M.*artifacts/" || true)
    if [ -n "$ARTIFACT_CHANGES" ]; then
        echo -e "  ${YELLOW}📊 CI artifacts out of sync - run 'make check'${NC}"
        ((WARNINGS++))
    fi
else
    echo -e "  ${GREEN}✅ Working tree clean${NC}"
fi
echo ""

# ============================================================================
# 2. Forbidden Zone Check
# ============================================================================
echo -e "${YELLOW}[2/5] Checking forbidden zones...${NC}"

FORBIDDEN_PATTERNS=(
    "config/antigravity.py"
    "chancellor_graph.py"
    "SECRET"
    "credentials"
    ".env"
)

STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || git diff --name-only HEAD~1 2>/dev/null || echo "")

for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
    VIOLATIONS=$(echo "$STAGED_FILES" | grep -i "$pattern" || true)
    if [ -n "$VIOLATIONS" ]; then
        echo -e "  ${RED}🚨 FORBIDDEN ZONE TOUCHED: $pattern${NC}"
        echo "$VIOLATIONS" | sed 's/^/     /'
        ((ERRORS++))
    fi
done

if [ "$ERRORS" -eq 0 ]; then
    echo -e "  ${GREEN}✅ No forbidden zone violations${NC}"
fi
echo ""

# ============================================================================
# 3. Lock File Drift Check
# ============================================================================
echo -e "${YELLOW}[3/5] Checking lock file integrity...${NC}"

LOCK_CHANGES=$(git status --porcelain | grep -E "\.(lock|lock\.yaml)$" || true)
if [ -n "$LOCK_CHANGES" ]; then
    echo -e "  ${YELLOW}⚠️  Lock files modified - verify intentional:${NC}"
    echo "$LOCK_CHANGES" | sed 's/^/     /'
    ((WARNINGS++))
else
    echo -e "  ${GREEN}✅ Lock files intact${NC}"
fi
echo ""

# ============================================================================
# 4. CI/CD Config Drift Check
# ============================================================================
echo -e "${YELLOW}[4/5] Checking CI/CD configuration...${NC}"

CI_CHANGES=$(git status --porcelain | grep -E "\.github/workflows/|\.gitlab-ci|Jenkinsfile" || true)
if [ -n "$CI_CHANGES" ]; then
    echo -e "  ${RED}🚨 CI/CD configuration modified - requires review:${NC}"
    echo "$CI_CHANGES" | sed 's/^/     /'
    ((ERRORS++))
else
    echo -e "  ${GREEN}✅ CI/CD configuration stable${NC}"
fi
echo ""

# ============================================================================
# 5. Branch Sync Check
# ============================================================================
echo -e "${YELLOW}[5/5] Checking branch synchronization...${NC}"

# Fetch latest (silent)
git fetch origin --quiet 2>/dev/null || true

CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
BEHIND=$(git rev-list --count HEAD..origin/$CURRENT_BRANCH 2>/dev/null || echo "0")
AHEAD=$(git rev-list --count origin/$CURRENT_BRANCH..HEAD 2>/dev/null || echo "0")

if [ "$BEHIND" -gt 0 ]; then
    echo -e "  ${YELLOW}⚠️  Branch is $BEHIND commits behind origin/${CURRENT_BRANCH}${NC}"
    ((WARNINGS++))
fi

if [ "$AHEAD" -gt 0 ]; then
    echo -e "  ${BLUE}📤 Branch is $AHEAD commits ahead of origin/${CURRENT_BRANCH}${NC}"
fi

if [ "$BEHIND" -eq 0 ] && [ "$AHEAD" -eq 0 ]; then
    echo -e "  ${GREEN}✅ Branch synchronized with origin${NC}"
fi
echo ""

# ============================================================================
# Summary
# ============================================================================
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}📊 Drift Detection Summary${NC}"
echo -e "${BLUE}============================================${NC}"

if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}❌ ERRORS: $ERRORS (requires immediate attention)${NC}"
fi

if [ "$WARNINGS" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  WARNINGS: $WARNINGS (review recommended)${NC}"
fi

if [ "$ERRORS" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo -e "${GREEN}✅ SSOT ALIGNED - No drift detected${NC}"
    exit 0
elif [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}🚨 DRIFT DETECTED - Fix before proceeding${NC}"
    exit 1
else
    echo -e "${YELLOW}⚠️  Minor drift detected - Review warnings${NC}"
    exit 0
fi
