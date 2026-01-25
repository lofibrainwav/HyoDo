#!/bin/bash
set -euo pipefail

# Configuration
IMAGE_NAME="${AFO_IMAGE_NAME:-ghcr.io/brnestrm/afo-core}"
TAG="${AFO_IMAGE_TAG:-latest}"
PLATFORM="linux/amd64"

echo "🚀 Starting CI Build (Option A: Build Speed)"
echo "Target: ${IMAGE_NAME}:${TAG} (${PLATFORM})"

# 1. Build Multi-Arch (or just AMD64 for server)
# Use buildx for cross-compilation (Mac M1 -> Linux AMD64)
docker buildx build \
  --platform "${PLATFORM}" \
  --tag "${IMAGE_NAME}:${TAG}" \
  --file packages/afo-core/Dockerfile \
  --push \
  .

echo "✅ Build & Push Complete: ${IMAGE_NAME}:${TAG}"
