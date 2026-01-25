#!/bin/bash
set -euo pipefail

echo "=== Phase 27: Monkeytype + mypy Integration Harvest (Corrected CLI) ==="

# 1. Clean previous run
rm -f monkeytype.sqlite3 || true
echo "Cleaned monkeytype.sqlite3"

# 2. Harvest Types via pytest-monkeytype plugin
# We rely on the plugin to trace execution and write to DB.
export MONKEYTYPE_TRACEBACKS=1
export MONKEYTYPE_MAX_TRACEBACKS=80

echo "Running Pytest with MonkeyType tracing..."
# Note: we use 'python3 -m pytest' to ensure sys.path is correct
python3 -m pytest -v --tb=short \
  --monkeytype-output=monkeytype.sqlite3 \
  packages/afo-core/tests

echo "Harvest complete."

# 3. Preview & Apply
# Target 1: AFO.domain.metrics.trinity
TARGET_1="AFO.domain.metrics.trinity"
echo ""
echo "--- Preview for $TARGET_1 ---"
# monkeytype CLI reads from monkeytype.sqlite3 by default in CWD
monkeytype show $TARGET_1 > artifacts/monkeytype_preview_trinity.txt || echo "No types collected for $TARGET_1"
head -n 20 artifacts/monkeytype_preview_trinity.txt || true

# Target 2: services.trinity_score_monitor
TARGET_2="services.trinity_score_monitor"
echo ""
echo "--- Preview for $TARGET_2 ---"
monkeytype show $TARGET_2 > artifacts/monkeytype_preview_score_monitor.txt || echo "No types collected for $TARGET_2"
head -n 20 artifacts/monkeytype_preview_score_monitor.txt || true

echo ""
echo "=== Phase 1 Harvest Ready for Review ==="
echo "Artifacts generated:"
echo " - artifacts/monkeytype_preview_trinity.txt"
echo " - artifacts/monkeytype_preview_score_monitor.txt"
echo ""
echo "Run 'monkeytype apply --ignore-missing <module>' to apply."
