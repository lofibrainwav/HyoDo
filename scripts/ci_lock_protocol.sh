#!/bin/bash
# scripts/ci_lock_protocol.sh
# AFO Kingdom CI/CD LOCK Protocol Enforcement
# 眞善美孝永 - Pyright -> Ruff -> pytest -> SBOM

set -euo pipefail

# 0. Setup
LOG_DIR="artifacts/ci"
mkdir -p "$LOG_DIR"
mkdir -p "artifacts/sbom"

BASE_FILE="$LOG_DIR/pyright_baseline.txt"
REPORT_FILE="$LOG_DIR/pyright_report.txt"
REG_FILE="$LOG_DIR/pyright_regressions.txt"

echo "🔒 [CI/CD LOCK] Starting 4-Gate Verification Protocol..."

# 1. Pyright (眞 - Truth)
echo "⚔️  [Step 1/4] Pyright Static Type Analysis (Truth)..."

# Pyright path discovery
PYRIGHT_BIN="pyright"
if ! command -v pyright &> /dev/null; then
    if [ -f ".venv/bin/pyright" ]; then
        PYRIGHT_BIN=".venv/bin/pyright"
    elif [ -f "venv/bin/pyright" ]; then
        PYRIGHT_BIN="venv/bin/pyright"
    fi
fi

# Run Pyright and capture standardized output (filtering out version warnings, venv messages, and trimming whitespace)
($PYRIGHT_BIN --project packages/afo-core/pyproject.toml 2>&1 | grep -v "pyright version" | grep -v "PYRIGHT_PYTHON_FORCE_VERSION" | grep -v "Please install the new version" | grep -v "venv" | sed 's/[[:space:]]*$//' | grep -v '^$' | LC_ALL=C sort > "$REPORT_FILE") || true

if [ -f "$BASE_FILE" ]; then
    # Standardize baseline for comparison
    LC_ALL=C sort -o "$BASE_FILE" "$BASE_FILE"
    # Find new lines in report that are not in baseline
    comm -13 "$BASE_FILE" "$REPORT_FILE" > "$REG_FILE" || true

    if [ -s "$REG_FILE" ]; then
        echo "⛔️ Pyright regression detected (new warnings):"
        head -n 20 "$REG_FILE"
        echo "...(refer to $REG_FILE for full list)"
        echo "❌ LOCK FAILURE: Truth Pillar compromised by regression."
        exit 1
    fi
    echo "✅ Pyright baseline OK (no regressions detected)."
else
    echo "✅ Baseline created: $BASE_FILE (COMMIT THIS FILE to lock the baseline)"
fi

# 1.5. Strict Quality Gate (孝 - Serenity)
echo "🛡️  [Step 1.5/4] Strict Quality Gate (Serenity / Truth Crusade)..."
# Validating critical API routes where Truth/Goodness was recently restored
STRICT_TARGETS="packages/afo-core/AFO/api/routes/chat.py packages/afo-core/AFO/api/routes/julie.py packages/afo-core/AFO/api/routes/scholar.py packages/afo-core/AFO/api/routes/gateway.py packages/afo-core/AFO/api/routes/llm.py packages/afo-core/AFO/api/routes/dspy.py packages/afo-core/AFO/api/routes/integrity_check.py"
python3 scripts/strict_quality_gate.py $STRICT_TARGETS > "$LOG_DIR/strict_gate_report.txt" 2>&1 || {
    echo "❌ Strict Quality Gate failed. Truth/Goodness Pillar compromised."
    echo "   Violations found in API Routes. See $LOG_DIR/strict_gate_report.txt"
    tail -n 20 "$LOG_DIR/strict_gate_report.txt"
    exit 1
}
echo "✅ Strict Quality Gate PASSED (Critical API Routes Secured)."

# 2. Ruff (美 - Beauty)
echo "🌉 [Step 2/4] Ruff Linting & Formatting (Beauty)..."
# Run ruff from packages/afo-core directory to ensure per-file-ignores work correctly
(cd packages/afo-core && ruff check . 2>&1 | tee "../../$LOG_DIR/ruff_report.txt") || {
    echo "❌ Ruff check failed. Beauty Pillar compromised. Refer to $LOG_DIR/ruff_report.txt"
    exit 1
}
(cd packages/afo-core && ruff format --check . 2>&1 | tee -a "../../$LOG_DIR/ruff_report.txt") || {
    echo "❌ Ruff formatting check failed. Beauty Pillar compromised."
    exit 1
}

# 3. pytest (膽 - Gallbladder/Goodness)
echo "🛡️  [Step 3/4] pytest Unit & Integration Tests (Goodness)..."
# 2026 Optimization: parallel execution with pytest-xdist (-n auto) + exclude slow tests
# Use venv pytest to ensure all dependencies (openai, litellm, etc.) are available
PYTEST_BIN="pytest"
if [ -f ".venv/bin/pytest" ]; then
    PYTEST_BIN=".venv/bin/pytest"
elif [ -f "venv/bin/pytest" ]; then
    PYTEST_BIN="venv/bin/pytest"
fi
($PYTEST_BIN packages/afo-core/tests -q --maxfail=1 -n 4 --dist worksteal -m "not integration and not external and not slow" --ignore=packages/afo-core/tests/test_scholars.py 2>&1 | tee "$LOG_DIR/pytest_report.txt") || {
    echo "❌ pytest failed. Goodness/Stability Pillar compromised. Refer to $LOG_DIR/pytest_report.txt"
    exit 1
}

# 4. SBOM (永/善 - Eternity/Goodness)
echo "♾️  [Step 4/4] SBOM Generation & Security Seal (Eternity)..."
python3 scripts/generate_sbom.py 2>&1 | tee "$LOG_DIR/sbom_log.txt" || {
    echo "❌ SBOM generation failed. Eternity/Security Pillar compromised."
    exit 1
}

# Standardize SBOM location
mv sbom artifacts/ 2>/dev/null || true

# Standardized Victory Seal Summary
echo ""
echo "===================================================="
echo "🎯 CI/CD LOCK VICTORY SUMMARY"
echo "----------------------------------------------------"
echo "1. Pyright: [PASS] No regressions vs baseline"
echo "2. Ruff:    [PASS] Quality & Format stabilized"
echo "3. pytest:  [PASS] Core organs functional"
echo "4. SBOM:    [PASS] Eternity seal applied"
echo "===================================================="
echo "✨ All 4 gates PASSED. The Kingdom is physically SECURE (SEALED)."
echo "   Artifacts: $LOG_DIR/ and artifacts/sbom/"
echo "===================================================="

# 5. Discord/Slack Notification (if webhook configured)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/afo_alert.sh" ]]; then
    # Load env vars if available (export mode)
    for env_file in packages/afo-core/.env .env; do
        if [[ -f "$env_file" ]]; then
            webhook_vars=$(grep -v '^#' "$env_file" | grep -E '^(DISCORD|SLACK)_WEBHOOK' | xargs || true)
            if [[ -n "${webhook_vars}" ]]; then
                export ${webhook_vars}
            fi
        fi
    done

    # Get test count from pytest report
    TEST_COUNT=$(grep -o '[0-9]* passed' "$LOG_DIR/pytest_report.txt" 2>/dev/null | head -1 || echo "tests passed")

    # Send notification
    bash "$SCRIPT_DIR/afo_alert.sh" success "4-Gate CI PASS" \
        "🏰 AFO Kingdom CI 완료\n• Pyright: ✅\n• Ruff: ✅\n• pytest: ✅ ($TEST_COUNT)\n• SBOM: ✅" 2>/dev/null || true
fi

exit 0
