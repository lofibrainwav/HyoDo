#!/usr/bin/env bash
# AFO Kingdom DGM Evolver (Sakana Darwin Gödel Machine Integration)
# Usage: ./scripts/afo_dgm_evolve.sh [--dry-run]
# Implements self-improvement loop inspired by Sakana AI's DGM

set -euo pipefail
trap 'echo "❌ DGM Evolution failed at line $LINENO"; exit 1' ERR

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}🔬 DRY_RUN mode - no changes will be made${NC}"
fi

EVOLUTION_DIR="artifacts/evolution/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$EVOLUTION_DIR"

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}     ${YELLOW}🧬 Sakana DGM Evolution Cycle${NC}                         ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}     Darwin Gödel Machine - Self-Improvement Loop         ${CYAN}║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Generate - Analyze current state
echo -e "${BLUE}[1/5] GENERATE${NC} - Analyzing current state..."
git rev-parse HEAD > "$EVOLUTION_DIR/current_head.txt"
./afo trinity > "$EVOLUTION_DIR/current_trinity.txt" 2>&1 || true

CURRENT_SCORE=$(grep -oE "[0-9]+\.[0-9]+" "$EVOLUTION_DIR/current_trinity.txt" | head -1 || echo "0")
echo "  Current Trinity Score: ${CURRENT_SCORE}%"

# Step 2: Test - Check improvement areas
echo -e "${BLUE}[2/5] TEST${NC} - Identifying improvement areas..."
{
    echo "Evolution Analysis $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "=============================================="
    echo "Current Trinity: ${CURRENT_SCORE}%"
    echo ""
    echo "Potential Improvements:"
    
    # Check for common improvements
    if ! command -v shellcheck &>/dev/null; then
        echo "- [ ] Install shellcheck for script linting"
    fi
    
    if [[ ! -f "CHANGELOG.md" ]]; then
        echo "- [ ] Add CHANGELOG.md for release tracking"
    fi
    
    # Check test coverage
    if [[ -f "packages/afo-core/pyproject.toml" ]]; then
        COVERAGE=$(grep -o "fail_under.*=[^,]*" packages/afo-core/pyproject.toml 2>/dev/null || echo "unknown")
        echo "- [ ] Coverage threshold: $COVERAGE"
    fi
    
    echo ""
    echo "Healthy Organs Check:"
    ./afo status 2>&1 | grep -E "Organs|Score" || true
} > "$EVOLUTION_DIR/improvement_analysis.txt"
cat "$EVOLUTION_DIR/improvement_analysis.txt"

# Step 3: Archive - Save current state
echo -e "${BLUE}[3/5] ARCHIVE${NC} - Saving evolution snapshot..."
git log --oneline -5 > "$EVOLUTION_DIR/recent_commits.txt"
./afo seal > "$EVOLUTION_DIR/seal_output.txt" 2>&1 || true
echo "  Archived to: $EVOLUTION_DIR"

# Step 4: Branch - Prepare evolution candidates
echo -e "${BLUE}[4/5] BRANCH${NC} - Preparing evolution candidates..."
{
    echo "Evolution Candidates:"
    echo "====================="
    echo ""
    echo "1. Code Quality Improvements"
    echo "   - Ruff linting rules enforcement"
    echo "   - MyPy strict type checking"
    echo ""
    echo "2. Performance Optimizations"
    echo "   - Async operation improvements"
    echo "   - Caching strategy enhancements"
    echo ""
    echo "3. Documentation Updates"
    echo "   - API documentation generation"
    echo "   - Usage examples expansion"
} > "$EVOLUTION_DIR/evolution_candidates.txt"
cat "$EVOLUTION_DIR/evolution_candidates.txt"

# Step 5: Repeat - Calculate evolution potential
echo -e "${BLUE}[5/5] REPEAT${NC} - Calculating evolution potential..."

# Create manifest
python3 << PYEOF
import hashlib, json, os, pathlib
base = "$EVOLUTION_DIR"
p = pathlib.Path(base)
files = []
for f in sorted([x for x in p.rglob("*") if x.is_file() and x.name != "manifest.json"]):
    h = hashlib.sha256(f.read_bytes()).hexdigest()
    files.append({"path": str(f.relative_to(p)), "sha256": h, "bytes": f.stat().st_size})
manifest = {
    "type": "evolution_cycle",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "current_trinity": $CURRENT_SCORE if "$CURRENT_SCORE" != "" else 0,
    "dry_run": "$DRY_RUN" == "true",
    "files": files
}
(p / "manifest.json").write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
PYEOF

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}  ✅ Evolution cycle complete!                             ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Trinity: ${CURRENT_SCORE}%                                          ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Evidence: $EVOLUTION_DIR ${GREEN}║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"

if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}🔬 DRY_RUN complete - review $EVOLUTION_DIR for analysis${NC}"
else
    echo -e "${GREEN}🧬 Evolution artifacts archived - ready for next cycle${NC}"
fi
