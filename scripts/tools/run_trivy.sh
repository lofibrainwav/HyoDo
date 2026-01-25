#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
mkdir -p artifacts

if ! command -v trivy >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    brew install trivy
  else
    echo "ERROR: trivy not found and brew not available"
    exit 1
  fi
fi

trivy fs \
  --format json \
  --output artifacts/trivy-results.json \
  --skip-dirs .git,node_modules,.venv,.next,dist,build,artifacts,logs \
  .

test -s artifacts/trivy-results.json
echo "OK: artifacts/trivy-results.json"
