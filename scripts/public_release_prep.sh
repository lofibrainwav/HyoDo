#!/bin/bash
# AFO Kingdom Public Release Preparation (One-shot)
# 眞善美孝永 - Victory Seal Logic

set -e

# Support --ci flag for non-interactive/clean-output mode
CI_MODE=false
if [[ "$1" == "--ci" ]]; then
  CI_MODE=true
  echo "🤖 CI Mode detected. Running with machine-optimized output."
fi

echo "🚀 [1/3] Masking local paths for privacy..."
python3 scripts/mask_local_paths.py

echo "🛡️ [2/3] Running SSOT Document Audit..."
if [ "$CI_MODE" = true ]; then
  python3 scripts/audit_docs_ssot.py --core-only
else
  python3 scripts/audit_docs_ssot.py --core-only
fi

echo "🎨 [3/3] Running Visual SSOT Sync Check..."
python3 scripts/verify_visual_sync.py docs/diagrams

echo "✨ All SSOT gates PASSED. Ready for Victory Seal."
