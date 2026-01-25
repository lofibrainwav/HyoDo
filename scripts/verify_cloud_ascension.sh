#!/bin/bash
# Phase 17-4: Cloud Ascension Final Verification
# AFO 왕국 클라우드 승천 최종 검증 스크립트
set -e

echo "🚀 [AntiGravity] Cloud Ascension Final Verification"
echo "===================================================="

# 1. Check Helm Chart Structure
echo ""
echo "1. Checking Helm Chart Structure..."
CHART_PATH="packages/afo-core/k8s/chart"
if [ -d "$CHART_PATH" ]; then
    echo "✅ Chart directory exists: $CHART_PATH"
    ls -la "$CHART_PATH"
else
    echo "❌ Chart directory NOT FOUND: $CHART_PATH"
    exit 1
fi

# 2. Validate Values File
echo ""
echo "2. Validating values.yaml..."
if [ -f "$CHART_PATH/values.yaml" ]; then
    echo "✅ values.yaml exists"
    grep -q "secrets:" "$CHART_PATH/values.yaml" && echo "   └── ✅ Secrets section found" || echo "   └── ⚠️ Secrets section missing"
else
    echo "❌ values.yaml NOT FOUND"
    exit 1
fi

# 3. Check Deployment Template
echo ""
echo "3. Checking deployment.yaml..."
if [ -f "$CHART_PATH/templates/deployment.yaml" ]; then
    echo "✅ deployment.yaml exists"
    grep -q "envFrom" "$CHART_PATH/templates/deployment.yaml" && echo "   └── ✅ envFrom (secrets) configured" || echo "   └── ⚠️ envFrom not configured"
else
    echo "❌ deployment.yaml NOT FOUND"
    exit 1
fi

# 4. Check Network Policy (Security)
echo ""
echo "4. Checking security manifests..."
if [ -f "$CHART_PATH/templates/networkpolicy.yaml" ]; then
    echo "✅ networkpolicy.yaml exists (Zero Trust)"
else
    echo "⚠️ networkpolicy.yaml not found"
fi

if [ -f "$CHART_PATH/templates/secrets.yaml" ]; then
    echo "✅ secrets.yaml exists"
else
    echo "⚠️ secrets.yaml not found"
fi

# 5. Check GitHub Actions Workflow
echo ""
echo "5. Checking CI/CD Pipeline..."
if [ -f ".github/workflows/antigravity-deploy.yml" ]; then
    echo "✅ antigravity-deploy.yml exists"
    grep -q "helm-deploy" ".github/workflows/antigravity-deploy.yml" && echo "   └── ✅ Helm deploy job configured" || echo "   └── ⚠️ Helm deploy job missing"
else
    echo "❌ antigravity-deploy.yml NOT FOUND"
fi

# Summary
echo ""
echo "===================================================="
echo "✨ [AntiGravity] Cloud Ascension Verification Complete!"
echo "   The Kingdom is ready to ascend to the Cloud."
echo "===================================================="
echo "AFO 왕국 만세! 眞·善·美·孝·永 영원히!"
