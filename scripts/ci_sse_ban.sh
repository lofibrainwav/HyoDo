#!/usr/bin/env bash
set -euo pipefail

# PH20-05: CI Gate for forbidden SSE paths
# Banned: "/api/stream/logs", "/api/system/logs/stream"
# Exceptions: 
# - packages/afo-core/api/routes/system_health.py (Redirects)
# - packages/dashboard/next.config.ts (Rewrites)
# - scripts/smoke/kingdom_smoke.sh (Tests)
# - scripts/ci_sse_ban.sh (Self)

echo "🔍 Scanning for forbidden SSE paths..."

# Define patterns
PATTERNS="/api/stream/logs|/api/system/logs/stream"

# Find files containing patterns, excluding allowed files
# We use grep with exclude-from logic or just filter logic. Since exclude list is short, we filter with grep -v.

# 1. Run grep recursively defined patterns
# 2. Filter out allowed files
# 3. If any results remain, FAIL.

MATCHES=$(grep -rnE "$PATTERNS" . \
  --exclude-dir=node_modules \
  --exclude-dir=.git \
  --exclude-dir=.next \
  --exclude-dir=__pycache__ \
  --exclude-dir=artifacts \
  --exclude-dir=docs \
  --exclude-dir=.lighthouseci \
  --exclude-dir=lighthouse-reports \
  --exclude="*.log" \
  --exclude="bandit.json" \
  --exclude="*.html" \
  --exclude="*.tsbuildinfo" \
  --exclude="kingdom_dashboard.js" \
  | grep -v "packages/afo-core/api/routes/system_health.py" \
  | grep -v "packages/dashboard/next.config.ts" \
  | grep -v "scripts/smoke/kingdom_smoke.sh" \
  | grep -v "scripts/ci_sse_ban.sh" \
  | grep -v "task.md" \
  | grep -v "walkthrough.md" \
  | grep -v "implementation_plan.md" \
  || true)

if [ -n "$MATCHES" ]; then
  echo "❌ Forbidden SSE paths found in:"
  echo "$MATCHES"
  echo ""
  echo "CRITICAL: Use SSOT Canonical Path: /api/logs/stream"
  exit 1
fi

echo "✅ No forbidden SSE paths found. SSOT Enforced."
exit 0
