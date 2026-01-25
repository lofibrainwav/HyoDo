#!/bin/bash
# Phase 19: The Final Ascension - Production Deployment
set -e

echo "⚔️  [Antigravity] Phase 19: Deploying Kingdom to Production Cloud..."

# 1. Pre-flight Check
if ! command -v helm &> /dev/null; then
    echo "❌ Helm not found. Please install Helm."
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo "❌ Kubectl not found. Please install Kubectl."
    exit 1
fi

# 2. Add Dependencies (Best Practice #9: Prometheus)
echo "🔍 [Observability] Adding Prometheus Repo..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# 3. Deploy Kingdom
echo "🚀 [Ascension] Deploying AFO Kingdom Helm Chart..."
helm upgrade --install afo-kingdom packages/afo-core/k8s/chart \
  --namespace afo-kingdom \
  --create-namespace \
  --values packages/afo-core/k8s/chart/values.yaml

# 4. Verification
echo "🛡️ [Goodness] Verifying Rollout..."
kubectl rollout status deployment/afo-kingdom -n afo-kingdom

# 5. Access
echo "☁️  [Service] Getting Service IP..."
kubectl get svc -n afo-kingdom

echo "👑 The Kingdom has ascended. Long live the King!"
