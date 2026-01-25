#!/bin/bash
# AFO Kingdom QualityGate - 통합 품질 검사 스크립트
# 眞善美孝永 - All Quality Tools in One

set -euo pipefail

REPORT_DIR="artifacts/quality_gate"
mkdir -p "$REPORT_DIR"

echo "🛡️ AFO QualityGate 시작..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Ruff (Fast Linter)
echo "📦 [1/7] Ruff Linting..."
ruff check packages/afo-core --output-format=json > "$REPORT_DIR/ruff_report.json" 2>/dev/null || true
RUFF_ERRORS=$(jq length "$REPORT_DIR/ruff_report.json" 2>/dev/null || echo "0")
echo "   → $RUFF_ERRORS issues"

# 2. Pyright (Type Check)
echo "📦 [2/7] Pyright Type Check..."
pyright --project packages/afo-core/pyproject.toml --outputjson > "$REPORT_DIR/pyright_report.json" 2>/dev/null || true
PYRIGHT_ERRORS=$(jq '.generalDiagnostics | length' "$REPORT_DIR/pyright_report.json" 2>/dev/null || echo "0")
echo "   → $PYRIGHT_ERRORS type errors"

# 3. Vulture (Dead Code)
echo "📦 [3/7] Vulture Dead Code..."
vulture packages/afo-core/AFO --min-confidence 80 > "$REPORT_DIR/vulture_report.txt" 2>/dev/null || true
VULTURE_COUNT=$(wc -l < "$REPORT_DIR/vulture_report.txt" | tr -d ' ')
echo "   → $VULTURE_COUNT dead code items"

# 4. Radon (Complexity)
echo "📦 [4/7] Radon Complexity..."
radon cc packages/afo-core/AFO -s -a --json > "$REPORT_DIR/radon_report.json" 2>/dev/null || true
AVG_COMPLEXITY=$(radon cc packages/afo-core/AFO -s -a 2>/dev/null | tail -1 | grep -o '[A-F]' | head -1 || echo "?")
echo "   → Average: $AVG_COMPLEXITY"

# 5. Hadolint (Dockerfile)
echo "📦 [5/7] Hadolint Dockerfile..."
hadolint packages/afo-core/Dockerfile --format json > "$REPORT_DIR/hadolint_report.json" 2>/dev/null || true
HADOLINT_COUNT=$(jq length "$REPORT_DIR/hadolint_report.json" 2>/dev/null || echo "0")
echo "   → $HADOLINT_COUNT Dockerfile issues"

# 6. pip-audit (Security)
echo "📦 [6/7] pip-audit Security..."
pip-audit --format json > "$REPORT_DIR/pip_audit_report.json" 2>/dev/null || true
VULN_COUNT=$(jq '.dependencies | map(select(.vulns | length > 0)) | length' "$REPORT_DIR/pip_audit_report.json" 2>/dev/null || echo "0")
echo "   → $VULN_COUNT vulnerable packages"

# 7. Coverage (if available)
echo "📦 [7/7] Test Coverage..."
if [ -f "packages/afo-core/.coverage" ]; then
    coverage report --format=json > "$REPORT_DIR/coverage_report.json" 2>/dev/null || true
    COV_PCT=$(jq '.totals.percent_covered' "$REPORT_DIR/coverage_report.json" 2>/dev/null || echo "N/A")
    echo "   → Coverage: $COV_PCT%"
else
    echo "   → No coverage data (run pytest --cov first)"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ QualityGate 완료. 보고서: $REPORT_DIR/"
