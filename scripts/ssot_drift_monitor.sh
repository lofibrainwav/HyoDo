#!/usr/bin/env bash
# SSOT Drift Monitor - 매일 설정 변화 감지
# Usage: ./scripts/ssot_drift_monitor.sh
# 기대값과 현재값을 비교하여 드리프트 경보

set -euo pipefail

EXPECTED_TRINITY_MIN="${EXPECTED_TRINITY_MIN:-0.90}"
EXPECTED_ORGANS_MIN="${EXPECTED_ORGANS_MIN:-6}"
OUT="artifacts/drift_$(date +%Y%m%d-%H%M%S)"

mkdir -p "$OUT"

echo "🔍 SSOT Drift Monitor Starting..."
echo "   Min Trinity: $EXPECTED_TRINITY_MIN"
echo "   Min Organs: $EXPECTED_ORGANS_MIN"
echo ""

# 1. Git State
echo "📋 Checking Git state..."
git fetch origin main 2>/dev/null || true
AHEAD=$(git rev-list HEAD..origin/main --count 2>/dev/null || echo "0")
BEHIND=$(git rev-list origin/main..HEAD --count 2>/dev/null || echo "0")
echo "git_ahead: $BEHIND" > "$OUT/git_drift.txt"
echo "git_behind: $AHEAD" >> "$OUT/git_drift.txt"

if [[ "$AHEAD" != "0" ]] || [[ "$BEHIND" != "0" ]]; then
    echo "⚠️  Git drift detected: ahead=$BEHIND, behind=$AHEAD"
    GIT_DRIFT="YES"
else
    echo "✅ Git synced (0/0)"
    GIT_DRIFT="NO"
fi

# 2. Trinity Score
echo ""
echo "🏛️ Checking Trinity Score..."
HEALTH_JSON=$(curl -sS http://localhost:8010/health 2>/dev/null || echo '{"error":"offline"}')
echo "$HEALTH_JSON" > "$OUT/health.json"

TRINITY=$(echo "$HEALTH_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('trinity',{}).get('trinity_score', 0))" 2>/dev/null || echo "0")
ORGANS=$(echo "$HEALTH_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('healthy_organs', 0))" 2>/dev/null || echo "0")

TRINITY_DRIFT=$(python3 -c "print('YES' if float('$TRINITY') < float('$EXPECTED_TRINITY_MIN') else 'NO')")
ORGANS_DRIFT=$(python3 -c "print('YES' if int('$ORGANS') < int('$EXPECTED_ORGANS_MIN') else 'NO')")

echo "trinity_score: $TRINITY" > "$OUT/trinity_drift.txt"
echo "trinity_drift: $TRINITY_DRIFT" >> "$OUT/trinity_drift.txt"
echo "organs_healthy: $ORGANS" >> "$OUT/trinity_drift.txt"
echo "organs_drift: $ORGANS_DRIFT" >> "$OUT/trinity_drift.txt"

# 3. Summary
echo ""
echo "=== Drift Summary ==="
echo "  Git Drift: $GIT_DRIFT"
echo "  Trinity: $TRINITY (min $EXPECTED_TRINITY_MIN) → $([[ $TRINITY_DRIFT == 'YES' ]] && echo '❌ DRIFT' || echo '✅ OK')"
echo "  Organs: $ORGANS (min $EXPECTED_ORGANS_MIN) → $([[ $ORGANS_DRIFT == 'YES' ]] && echo '❌ DRIFT' || echo '✅ OK')"

# Final verdict
if [[ "$GIT_DRIFT" == "NO" && "$TRINITY_DRIFT" == "NO" && "$ORGANS_DRIFT" == "NO" ]]; then
    echo ""
    echo "✅ SSOT Drift Monitor: ALL CLEAR - No drift detected"
    echo "status: PASS" > "$OUT/verdict.txt"
    exit 0
else
    echo ""
    echo "⚠️  SSOT Drift Monitor: DRIFT DETECTED"
    echo "status: DRIFT_DETECTED" > "$OUT/verdict.txt"
    echo "git_drift: $GIT_DRIFT" >> "$OUT/verdict.txt"
    echo "trinity_drift: $TRINITY_DRIFT" >> "$OUT/verdict.txt"
    echo "organs_drift: $ORGANS_DRIFT" >> "$OUT/verdict.txt"
    exit 1
fi
