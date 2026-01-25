#!/usr/bin/env bash
# SSOT Auto-Seal Bot - 증거폴더 + sha256 + 태그 자동 생성
# Usage: ./scripts/ssot_seal.sh [optional_tag_prefix]
# Trinity Score: 眞善美孝永 자동화 (永 + 孝)

set -euo pipefail

# Configuration
TAG_PREFIX="${1:-ssot-seal}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
HEAD_SHA=$(git rev-parse --short HEAD)
OUT="artifacts/seal_${HEAD_SHA}_${TIMESTAMP}"

echo "🔐 SSOT Auto-Seal Bot Starting..."
echo "   HEAD: ${HEAD_SHA}"
echo "   OUT:  ${OUT}"

# Create evidence folder
mkdir -p "$OUT"

# 1. Git State
echo "📋 Capturing git state..."
git rev-parse HEAD > "$OUT/git_head.txt"
git status -sb > "$OUT/git_status.txt"
git log -1 --oneline > "$OUT/git_log1.txt"
git ls-remote origin refs/heads/main 2>/dev/null > "$OUT/ls_remote_main.txt" || echo "N/A" > "$OUT/ls_remote_main.txt"

# 2. Trinity Score (if server available)
echo "🏛️ Capturing Trinity Score..."
curl -sS http://localhost:8010/health 2>/dev/null > "$OUT/health.json" || echo '{"status":"server_offline"}' > "$OUT/health.json"

# Extract Trinity Score for tag message
TRINITY_SCORE=$(python3 -c "import json; d=json.load(open('$OUT/health.json')); print(d.get('trinity',{}).get('trinity_score', 'N/A'))" 2>/dev/null || echo "N/A")
ORGANS=$(python3 -c "import json; d=json.load(open('$OUT/health.json')); print(f\"{d.get('healthy_organs','?')}/{d.get('total_organs','?')}\")" 2>/dev/null || echo "N/A")

# 3. Docker Status (optional)
echo "🐳 Capturing Docker status..."
docker ps --format 'table {{.Names}}\t{{.Status}}' 2>/dev/null > "$OUT/docker_ps.txt" || echo "Docker not available" > "$OUT/docker_ps.txt"

# 4. Generate SHA256 checksums
echo "🔒 Generating SHA256 checksums..."
shasum -a 256 "$OUT"/*.txt "$OUT"/*.json 2>/dev/null > "$OUT/sha256.txt" || true

# 5. Create summary
cat > "$OUT/SEAL_SUMMARY.md" << EOF
# SSOT Seal Summary

- **Timestamp**: ${TIMESTAMP}
- **Commit**: ${HEAD_SHA}
- **Trinity Score**: ${TRINITY_SCORE}
- **Organs**: ${ORGANS}
- **Evidence**: ${OUT}/

## Files
$(ls -la "$OUT")
EOF

echo "✅ Evidence captured to $OUT"

# 6. Create and push tag (optional - controlled by CI)
if [[ "${AUTO_TAG:-false}" == "true" ]]; then
    TAG="${TAG_PREFIX}-${HEAD_SHA}-${TIMESTAMP}"
    echo "🏷️ Creating tag: $TAG"
    git tag -a "$TAG" -m "SSOT Auto-Seal: Trinity ${TRINITY_SCORE}, Organs ${ORGANS}, HEAD ${HEAD_SHA}"
    
    if [[ "${PUSH_TAG:-false}" == "true" ]]; then
        git push origin "$TAG"
        echo "📤 Tag pushed to origin"
    fi
fi

echo ""
echo "🔐 SSOT Seal Complete!"
echo "   Folder: $OUT"
echo "   Trinity: $TRINITY_SCORE"
echo "   Organs: $ORGANS"
