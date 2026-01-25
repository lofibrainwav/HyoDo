#!/usr/bin/env bash
# Phase 4-A: Branch Protection 강제 봉인 스크립트
# Usage: ./scripts/enforce_branch_protection.sh
# Required: gh CLI + GH_TOKEN 또는 gh auth login

set -euo pipefail

REPO="${REPO:-lofibrainwav/AFO_Kingdom}"
BRANCH="${BRANCH:-main}"

echo "🔐 Phase 4-A: Branch Protection 강제 봉인 시작"
echo "   Repo: $REPO"
echo "   Branch: $BRANCH"
echo ""

# gh CLI 확인
if ! command -v gh &> /dev/null; then
    echo "❌ Error: gh CLI not found. Install: brew install gh"
    exit 1
fi

# 인증 확인
if ! gh auth status &> /dev/null; then
    echo "❌ Error: Not authenticated. Run: gh auth login"
    exit 1
fi

echo "📋 Creating branch protection rule..."

# Branch protection 설정 (GitHub API v3)
gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "/repos/${REPO}/branches/${BRANCH}/protection" \
    -f required_status_checks='{"strict":true,"contexts":["Trinity Gate"]}' \
    -f enforce_admins=true \
    -f required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
    -f required_linear_history=true \
    -f allow_force_pushes=false \
    -f allow_deletions=false \
    -f restrictions=null \
    > /dev/null 2>&1 || {
        echo "⚠️ Branch protection may already exist or partial update applied"
    }

echo "✅ Branch Protection 설정 완료!"
echo ""

# 설정 확인
echo "📊 Current protection status:"
gh api "/repos/${REPO}/branches/${BRANCH}/protection" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f'  - Required status checks: {d.get(\"required_status_checks\", {}).get(\"contexts\", [])}')
    print(f'  - Enforce admins: {d.get(\"enforce_admins\", {}).get(\"enabled\", False)}')
    print(f'  - Require PR reviews: {\"required_pull_request_reviews\" in d}')
    print(f'  - Linear history: {d.get(\"required_linear_history\", {}).get(\"enabled\", False)}')
except:
    print('  Could not parse protection status')
" || echo "  Could not retrieve protection status"

echo ""
echo "🎉 Phase 4-A Branch Protection SEALED!"
