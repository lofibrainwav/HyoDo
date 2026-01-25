#!/usr/bin/env bash
# AFO Kingdom Evidence Manifest Generator
# Usage: source scripts/afo_manifest.sh && generate_manifest <command> <output_dir>
# Creates standardized manifest.json + sha256.txt for all evidence

set -euo pipefail

# Generate standardized manifest.json
generate_manifest() {
    local COMMAND="${1:-unknown}"
    local OUT_DIR="${2:-.}"
    local TIMESTAMP
    TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local HEAD_SHA
    HEAD_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    local HEAD_SHORT
    HEAD_SHORT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    
    # Get Trinity Score if available
    local TRINITY_SCORE="0"
    local ORGANS_HEALTHY="0"
    local ORGANS_TOTAL="0"
    
    if curl -sS http://localhost:8010/health &>/dev/null; then
        TRINITY_SCORE=$(curl -sS http://localhost:8010/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('trinity',{}).get('trinity_score', 0))" 2>/dev/null || echo "0")
        ORGANS_HEALTHY=$(curl -sS http://localhost:8010/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('healthy_organs', 0))" 2>/dev/null || echo "0")
        ORGANS_TOTAL=$(curl -sS http://localhost:8010/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total_organs', 0))" 2>/dev/null || echo "0")
    fi
    
    # Create manifest.json
    cat > "$OUT_DIR/manifest.json" << EOF
{
    "version": "1.0",
    "command": "$COMMAND",
    "timestamp": "$TIMESTAMP",
    "git": {
        "head": "$HEAD_SHA",
        "head_short": "$HEAD_SHORT"
    },
    "trinity": {
        "score": $TRINITY_SCORE,
        "organs_healthy": $ORGANS_HEALTHY,
        "organs_total": $ORGANS_TOTAL
    },
    "files": []
}
EOF
    
    # Update files list
    if command -v python3 &>/dev/null; then
        python3 << PYEOF
import json
import os
import hashlib

manifest_path = "$OUT_DIR/manifest.json"
with open(manifest_path) as f:
    manifest = json.load(f)

files = []
for fname in os.listdir("$OUT_DIR"):
    if fname == "manifest.json" or fname == "sha256.txt":
        continue
    fpath = os.path.join("$OUT_DIR", fname)
    if os.path.isfile(fpath):
        with open(fpath, 'rb') as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()
        files.append({"name": fname, "sha256": sha256, "size": os.path.getsize(fpath)})

manifest["files"] = files
with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2)
PYEOF
    fi
    
    # Generate sha256.txt for all files including manifest
    cd "$OUT_DIR" && shasum -a 256 ./* > sha256.txt 2>/dev/null || true
    cd - > /dev/null
    
    echo "$OUT_DIR/manifest.json"
}

# Export function
export -f generate_manifest
