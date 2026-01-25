#!/bin/bash
set -euo pipefail

: "${GRAFANA_URL:=http://localhost:3000}"
: "${GRAFANA_USER:=admin}"
: "${GRAFANA_PASS:=admin}"

echo "📡 Exporting Grafana Alerts from ${GRAFANA_URL}..."

EXPORT_DIR="packages/afo-core/config/observability/grafana/provisioning/alerting/export"
mkdir -p "$EXPORT_DIR"

# 1) Export Alert Rules
curl -sfu "${GRAFANA_USER}:${GRAFANA_PASS}" \
  "${GRAFANA_URL}/api/v1/provisioning/alert-rules" \
  -o "${EXPORT_DIR}/alert-rules.json"

echo "✅ Alert Rules exported to ${EXPORT_DIR}/alert-rules.json"

# 2) Export Contact Points
curl -sfu "${GRAFANA_USER}:${GRAFANA_PASS}" \
  "${GRAFANA_URL}/api/v1/provisioning/contact-points" \
  -o "${EXPORT_DIR}/contact-points.json"

echo "✅ Contact Points exported to ${EXPORT_DIR}/contact-points.json"

# 3) Export Policies
curl -sfu "${GRAFANA_USER}:${GRAFANA_PASS}" \
  "${GRAFANA_URL}/api/v1/provisioning/policies" \
  -o "${EXPORT_DIR}/policies.json"

echo "✅ Policies exported to ${EXPORT_DIR}/policies.json"
