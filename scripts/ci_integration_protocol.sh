#!/bin/bash
# 🌉 AFO Kingdom Integration Protocol (Precision Gate)
# Runs slow and integration tests that are skipped by the main CI lock.
set -e

echo "🌉 [Integration Protocol] Initiating Deep Verification..."

# 1. Check Environment
if [ ! -f .env ]; then
    echo "❌ .env file missing! Integration tests require API keys."
    exit 1
fi

echo "🔍 Environment Check: OK"

# 2. Run Integration Tests (Marked @integration or @slow)
# We treat failures here as WARNINGS initially, to avoid blocking development,
# but ideally they should pass.
echo "🧪 Running Integration & Slow Tests..."

pytest -m "integration or slow" packages/afo-core/tests -v
EXIT_CODE=$?

if [ "$EXIT_CODE" -eq 0 ]; then
    echo "✅ [Integration Protocol] All Systems Nominal."
    exit 0
else
    echo "⚠️ [Integration Protocol] Completed with Issues (Exit Code: $EXIT_CODE)."
    echo "   Check logs above. These are non-blocking for now but indicate broken external connections."
    exit $EXIT_CODE
fi
