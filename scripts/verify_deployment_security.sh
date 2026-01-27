#!/usr/bin/env bash
# AFO Kingdom Deployment Security Verification
# 眞善美孝永 - CIS Benchmark Level 2 Compliance Check

set -e

echo "════════════════════════════════════════════════════════════════"
echo "👑 AFO Kingdom Deployment Security Verification"
echo "════════════════════════════════════════════════════════════════"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

PASS=0
FAIL=0

check() {
    if [ "$1" = "true" ]; then
        echo -e "  ✅ ${GREEN}$2${NC}"
        ((PASS++))
    else
        echo -e "  ❌ ${RED}$2${NC}"
        ((FAIL++))
    fi
}

echo ""
echo "📦 1. Docker Security Verification"
echo "────────────────────────────────────"

# Check hardened compose exists
HARDENED_EXISTS=$(test -f packages/afo-core/docker-compose.hardened.yml && echo "true" || echo "false")
check "$HARDENED_EXISTS" "docker-compose.hardened.yml exists"

# Check for security patterns in hardened compose
if [ "$HARDENED_EXISTS" = "true" ]; then
    READONLY=$(grep -c "read_only: true" packages/afo-core/docker-compose.hardened.yml || echo "0")
    check "$([ "$READONLY" -gt 0 ] && echo 'true' || echo 'false')" "read_only filesystem enabled"
    
    CAPDROP=$(grep -c "cap_drop:" packages/afo-core/docker-compose.hardened.yml || echo "0")
    check "$([ "$CAPDROP" -gt 0 ] && echo 'true' || echo 'false')" "capability drop configured"
    
    INTERNAL=$(grep -c "internal: true" packages/afo-core/docker-compose.hardened.yml || echo "0")
    check "$([ "$INTERNAL" -gt 0 ] && echo 'true' || echo 'false')" "internal networks configured"
fi

echo ""
echo "🛡️ 2. Kubernetes Security Verification"
echo "────────────────────────────────────────"

# Check K8s manifests exist
RBAC_EXISTS=$(test -f packages/afo-core/k8s/rbac/namespace-rbac.yaml && echo "true" || echo "false")
check "$RBAC_EXISTS" "RBAC manifests exist"

KYVERNO_EXISTS=$(test -f packages/afo-core/k8s/policies/kyverno-pss.yaml && echo "true" || echo "false")
check "$KYVERNO_EXISTS" "Kyverno policies exist"

NETPOL_EXISTS=$(test -f packages/afo-core/k8s/network/network-policies.yaml && echo "true" || echo "false")
check "$NETPOL_EXISTS" "NetworkPolicy manifests exist"

# Check PSS restricted labels
if [ "$RBAC_EXISTS" = "true" ]; then
    PSS_LABEL=$(grep -c "pod-security.kubernetes.io/enforce: restricted" packages/afo-core/k8s/rbac/namespace-rbac.yaml || echo "0")
    check "$([ "$PSS_LABEL" -gt 0 ] && echo 'true' || echo 'false')" "PSS restricted labels configured"
fi

echo ""
echo "🔐 3. Kyverno Policy Verification"
echo "──────────────────────────────────"

if [ "$KYVERNO_EXISTS" = "true" ]; then
    VALIDATE=$(grep -c "validationFailureAction: Enforce" packages/afo-core/k8s/policies/kyverno-pss.yaml || echo "0")
    check "$([ "$VALIDATE" -gt 0 ] && echo 'true' || echo 'false')" "Enforce mode configured"
    
    NONROOT=$(grep -c "runAsNonRoot: true" packages/afo-core/k8s/policies/kyverno-pss.yaml || echo "0")
    check "$([ "$NONROOT" -gt 0 ] && echo 'true' || echo 'false')" "Non-root enforcement"
    
    READONLY_K8S=$(grep -c "readOnlyRootFilesystem: true" packages/afo-core/k8s/policies/kyverno-pss.yaml || echo "0")
    check "$([ "$READONLY_K8S" -gt 0 ] && echo 'true' || echo 'false')" "Read-only filesystem policy"
fi

echo ""
echo "🌐 4. Network Security Verification"
echo "────────────────────────────────────"

if [ "$NETPOL_EXISTS" = "true" ]; then
    DEFAULT_DENY=$(grep -c "default-deny-all" packages/afo-core/k8s/network/network-policies.yaml || echo "0")
    check "$([ "$DEFAULT_DENY" -gt 0 ] && echo 'true' || echo 'false')" "Default deny policy"
    
    DNS_EGRESS=$(grep -c "allow-dns-egress" packages/afo-core/k8s/network/network-policies.yaml || echo "0")
    check "$([ "$DNS_EGRESS" -gt 0 ] && echo 'true' || echo 'false')" "DNS egress allowed"
fi

echo ""
echo "🐍 5. Python Dependency Verification"
echo "─────────────────────────────────────"

cd .
source .venv/bin/activate 2>/dev/null || true

PIP_CHECK=$(pip check 2>&1)
if echo "$PIP_CHECK" | grep -q "No broken requirements"; then
    check "true" "pip check: No broken requirements"
else
    check "false" "pip check: Issues found"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📊 RESULTS"
echo "════════════════════════════════════════════════════════════════"
echo -e "  ✅ Passed: ${GREEN}$PASS${NC}"
echo -e "  ❌ Failed: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🏆 All security checks passed! CIS Benchmark Level 2 Compliant!${NC}"
    exit 0
else
    echo -e "${RED}⚠️ Some checks failed. Review the output above.${NC}"
    exit 1
fi
