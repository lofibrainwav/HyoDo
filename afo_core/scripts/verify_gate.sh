#!/bin/bash
# AFO Kingdom Verification Gate Wrapper (善 - Goodness)
set -eo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TEST_SCRIPT="packages/afo-core/tests/verify_kingdom_full.py"
OUTPUT_DIR="artifacts/verification_gate"

echo "🏰 AFO Kingdom Verification Gate: Starting..."
echo "Repo Root: $REPO_ROOT"

# Ensure environment is set up
cd "$REPO_ROOT"
export PYTHONPATH="$PYTHONPATH:$(pwd)/packages/afo-core"

# Parse optional arguments
FLAGS=""
if [[ "${AFO_REQUIRE_OPENAI:-0}" == "1" ]]; then
    echo "⚠️ OpenAI Enforcement: ACTIVE"
    FLAGS="--require-openai"
fi

# Multi-stage verification with evidence bundle
echo "Running Full Audit..."
python3 "$TEST_SCRIPT" $FLAGS --output-dir "$OUTPUT_DIR"

# Exit handling
if [[ $? -eq 0 ]]; then
    echo "✅ Verification Gate: PASSED"
    exit 0
else
    echo "❌ Verification Gate: FAILED"
    exit 1
fi
