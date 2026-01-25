#!/bin/bash
echo "🔍 Verifying System Fingerprints (眞)..."

BACKEND_VERSION=$(curl -s http://localhost:8010/health | jq -r '.build_version // "unknown"')
DASHBOARD_VERSION=$(curl -s http://localhost:3000/api/kingdom-status | jq -r '.buildVersion // "unknown"')

echo "----------------------------------------"
echo "Backend Fingerprint:   $BACKEND_VERSION"
echo "Dashboard Fingerprint: $DASHBOARD_VERSION"
echo "----------------------------------------"

if [ "$BACKEND_VERSION" == "$DASHBOARD_VERSION" ] && [ "$BACKEND_VERSION" != "unknown" ]; then
    echo "✅ SUCCESS: Fingerprints match. The system is truthful."
    exit 0
else
    echo "❌ FAILURE: Fingerprint mismatch or unknown status!"
    echo "Possible 'Ghost Code' or cache issues detected."
    exit 1
fi
