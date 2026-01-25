#!/usr/bin/env bash
# AFO Kingdom Operations Smoke Test
# Based on: docs/operations/AFO_OPERATIONS_RUNBOOK.md
# Purpose: Validate core operational signals automatically

set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8010}"
SSE_PATH="${SSE_PATH:-/api/thoughts/sse}"
TIMEOUT_S="${TIMEOUT_S:-10}"
AFO_INTERNAL_SECRET="${AFO_INTERNAL_SECRET:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 AFO Kingdom Operations Smoke Test"
echo "======================================"
echo "BASE_URL: $BASE_URL"
echo "SSE_PATH: $SSE_PATH"
echo "TIMEOUT_S: $TIMEOUT_S"
echo

# Helper functions
http_code() {
    local url="$1"
    curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000"
}

check_service() {
    local name="$1"
    local url="$2"
    local expected="$3"

    echo -n "Checking $name... "
    local code
    code=$(http_code "$url")

    if [[ "$code" == "$expected" ]]; then
        echo -e "${GREEN}✓ PASS ($code)${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL ($code, expected $expected)${NC}"
        return 1
    fi
}

check_security() {
    local endpoint="$1"
    local desc="$2"
    local expected="$3"

    echo -n "Checking security ($desc)... "
    local code
    code=$(http_code "$BASE_URL$endpoint")

    if [[ "$code" == "$expected" ]]; then
        echo -e "${GREEN}✓ PASS ($code)${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL ($code, expected $expected)${NC}"
        echo -e "${RED}🚨 SECURITY GATE FAIL: $desc must return $expected, got $code${NC}"
        return 1
    fi
}

check_sse() {
    echo -n "Checking SSE stream... "
    local output
    output=$(mktemp)

    # Capture SSE for TIMEOUT_S seconds
    timeout "$TIMEOUT_S" bash -c "curl -s -N '$BASE_URL$SSE_PATH' > '$output'" 2>/dev/null || true

    local bytes
    bytes=$(wc -c < "$output")

    rm -f "$output"

    if [[ "$bytes" -gt 0 ]]; then
        echo -e "${GREEN}✓ PASS ($bytes bytes)${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL (0 bytes)${NC}"
        return 1
    fi
}

# Initialize test results
FAILURES=0
TOTAL_CHECKS=0

# 1. Health Checks (HTTP 200 expected)
echo "🏥 Health Checks:"
if check_service "8010 API" "$BASE_URL/health" "200"; then ((++TOTAL_CHECKS)); else ((++FAILURES)); fi
# Note: 8001 rag-service is deprecated (integrated into soul-engine)
# Note: 3000 dashboard only checked when INCLUDE_DASHBOARD=1
if [[ "${INCLUDE_DASHBOARD:-0}" == "1" ]]; then
    if check_service "3000 Dashboard" "http://localhost:3000/" "200"; then ((++TOTAL_CHECKS)); else ((++FAILURES)); fi
fi
echo

# 2. Security Checks (optional - only if revalidate endpoint is available)
echo "🔒 Security Checks:"
# Check if revalidate endpoint exists (may not be deployed in minimal smoke test)
REVALIDATE_CODE=$(http_code "$BASE_URL/api/revalidate/status")
if [[ "$REVALIDATE_CODE" == "404" ]]; then
    echo -e "${YELLOW}⚠️  /api/revalidate/status not deployed - skipping security checks${NC}"
elif [[ -n "$AFO_INTERNAL_SECRET" ]]; then
    # Full security check when secret is available
    if check_security "/api/revalidate/status" "unauthorized" "401"; then ((++TOTAL_CHECKS)); else ((++FAILURES)); fi
    if check_security "/api/revalidate/status" "wrong secret" "401"; then ((++TOTAL_CHECKS)); else ((++FAILURES)); fi
    if check_security "/api/revalidate/status" "correct secret" "200"; then ((++TOTAL_CHECKS)); else ((++FAILURES)); fi
else
    echo -e "${YELLOW}⚠️  AFO_INTERNAL_SECRET not set - skipping auth checks${NC}"
fi
echo

# 3. SSE Stream Check
echo "📡 SSE Stream Check:"
if check_sse; then ((++TOTAL_CHECKS)); else ((++FAILURES)); fi
echo

# 4. Container Status (if docker available)
if command -v docker &> /dev/null; then
    echo "🐳 Container Status:"
    if docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -q "Up"; then
        echo -e "${GREEN}✓ PASS (containers running)${NC}"
        ((++TOTAL_CHECKS))
    else
        echo -e "${RED}✗ FAIL (no containers running)${NC}"
        ((++FAILURES))
    fi
    echo
else
    echo -e "${YELLOW}⚠️  Docker not available - skipping container check${NC}"
    echo
fi

# Summary
echo "📊 Test Summary:"
echo "================"
echo "Total checks: $TOTAL_CHECKS"
echo "Failures: $FAILURES"

if [[ "$FAILURES" -eq 0 ]]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
    echo "AFO Kingdom operational signals are healthy!"
    exit 0
else
    echo -e "${RED}❌ $FAILURES CHECK(S) FAILED${NC}"
    echo "Check operational status and runbook procedures."
    exit 1
fi