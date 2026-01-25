#!/bin/bash
set -euo pipefail

# Deployment Script for Remote Server (Pull Only)
# Option A: CI Build -> Server Pull

IMAGE_NAME="${AFO_IMAGE_NAME:-ghcr.io/brnestrm/afo-core}"
TAG="${AFO_IMAGE_TAG:-latest}"

echo "🚀 Starting Remote Deploy (Pull Only)"
echo "Image: ${IMAGE_NAME}:${TAG}"

# 1. Pull latest image
docker-compose pull

# 2. Restart services (Quick)
docker-compose up -d --remove-orphans

echo "✅ Deploy Complete (Phase 4 Seal)"
