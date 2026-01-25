#!/bin/bash
set -euo pipefail

: "${REVALIDATE_URL:?}"
: "${REVALIDATE_SECRET:?}"
: "${FRAGMENT_URL:?}"

mkdir -p packages/dashboard/public/ops
ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

fragment_status="$(curl -s -o /dev/null -w "%{http_code}" "$FRAGMENT_URL")"
revalidate_status="$(curl -s -o /dev/null -w "%{http_code}" -X POST "${REVALIDATE_URL%/}/api/revalidate" \
  -H "x-revalidate-secret: ${REVALIDATE_SECRET}" \
  -H "content-type: application/json" \
  -d '{"fragmentKey":"home-hero"}')"

cat > packages/dashboard/public/ops/revalidate_canary.json <<JSON
{
  "as_of_utc": "$ts",
  "fragment_url": "$FRAGMENT_URL",
  "fragment_http": $fragment_status,
  "revalidate_url": "${REVALIDATE_URL%/}/api/revalidate",
  "revalidate_http": $revalidate_status
}
JSON