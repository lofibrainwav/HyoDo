#!/bin/bash
# AFO Kingdom - SSOT ScoreCard Autogen v1.2.1
# [眞善美孝영] Antigravity Chancellor Script

AS_OF=$(date +"%Y-%m-%d (%Z)")
BRANCH=$(git branch --show-current)
SHA=$(git rev-parse --short HEAD)

# Toolchain Anchoring
PY_VER=$(python -V 2>&1 | awk '{print $2}')
NODE_VER=$(node -v)
PNPM_VER=$(pnpm -v)
PYRIGHT_VER=$(npx pyright --version | awk '{print $2}')
RUFF_VER=$(ruff --version | awk '{print $2}')

# Runtime Status Detection
if lsof -i :8010 > /dev/null; then
    RUNTIME="ONLINE | Port 8010 Active"
else
    RUNTIME="OFFLINE | Docker Daemon / Soul Engine 미기동"
fi

# Trinity Score Decomposition [Target (Simulation)]
TR_SH="95.5%"
PI_TR="94"
PI_GD="97"
PI_BT="95"
PI_SR="96"
PI_ET="95"

# Debt Status Collection
RUFF_DEBT=2285
PYRIGHT_FILE="packages/afo-core/AFO/pyright_baseline.txt"
if [ -f "$PYRIGHT_FILE" ]; then
    PYRIGHT_BASELINE=$(grep -c "error:" "$PYRIGHT_FILE")
else
    PYRIGHT_BASELINE="N/A"
fi

# Pyright Full-Run Truth (JSON)
# Note: This might differ from baseline if config or files changed
# PYRIGHT_JSON="/tmp/pyright_ssot.json"
# npx pyright --outputjson > "$PYRIGHT_JSON" 2>/dev/null
# PYRIGHT_FULL=$(python3 -c "import json, sys; d=json.load(open('$PYRIGHT_JSON')); print(d.get('summary', {}).get('errorCount', 'N/A'))")
# For v1.2 simplicity, we align with the Baseline Seal.
PYRIGHT_DEBT="$PYRIGHT_BASELINE"

cat <<EOF
## 🧾 SSOT ScoreCard (Current Pillar Status)
> [!NOTE]
> **As-of**: $AS_OF
> **Repo Anchor**: Branch \`$BRANCH\` | SHA \`$SHA\`
> **Toolchain**: Py $PY_VER | Node $NODE_VER | pnpm $PNPM_VER | Pyright $PYRIGHT_VER | Ruff $RUFF_VER
> **Runtime Status**: **$RUNTIME**
> **Trinity Score [Target (Simulation)]**: **$TR_SH**
> **AESTHETIC (眞/善/美/孝/영) [Target (Simulation)]**: **$PI_TR/$PI_GD/$PI_BT/$PI_SR/$PI_ET**
> **Debt Status**: Ruff: Frozen=$RUFF_DEBT | Pyright(strict): Baseline=$PYRIGHT_DEBT
EOF
