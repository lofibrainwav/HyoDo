#!/usr/bin/env bash
# AFO Kingdom Release Tag Helper
# Usage: ./scripts/afo_release_tag.sh vX.Y.Z
# Creates a release tag after Trinity Gate validation

set -euo pipefail
trap 'echo "❌ Release failed at line $LINENO"; exit 1' ERR

TAG="${1:-}"
if [[ -z "$TAG" ]]; then
    echo "Usage: scripts/afo_release_tag.sh vX.Y.Z"
    exit 2
fi

# Validate semver format
if ! [[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Invalid version format. Use vX.Y.Z (e.g., v1.0.0)"
    exit 2
fi

# Check working tree
if ! git diff --quiet; then
    echo "❌ Working tree not clean. Commit or stash changes first."
    exit 2
fi

if ! git diff --cached --quiet; then
    echo "❌ Index not clean. Commit changes first."
    exit 2
fi

# Check branch
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$BRANCH" != "main" ]]; then
    echo "❌ Not on main branch: $BRANCH"
    exit 2
fi

# Run Trinity Gate
echo "🏛️ Running Trinity Gate check..."
if [[ -x ./afo ]]; then
    ./afo trinity
else
    bash ./scripts/trinity_check.sh
fi

# Create and push tag
echo "🏷️ Creating tag: $TAG"
git tag -a "$TAG" -m "Release $TAG"
git push origin "$TAG"

echo "✅ Tag $TAG pushed successfully!"
echo "📋 GitHub Actions will now create the release."
