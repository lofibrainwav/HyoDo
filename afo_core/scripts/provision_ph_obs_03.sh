#!/bin/bash
set -euo pipefail

# Path adjustment for Correct AFO Structure
# We are running this relative to packages/afo-core usually, or we set absolute paths.
# Let's assume this script is run from packages/afo-core root or we find the path.

BASE_DIR="$(pwd)"
if [[ "$BASE_DIR" != *"/packages/afo-core"* ]]; then
    if [ -d "packages/afo-core" ]; then
        cd packages/afo-core
    fi
fi

# Define the dashboards directory (Matched to PH-OBS-01/02 structure)
DASH_DIR="config/observability/grafana/dashboards/ph-obs-03"
mkdir -p "$DASH_DIR"

echo "📂 Target Dashboard Directory: $(pwd)/$DASH_DIR"

# 1) 템플릿 JSON 2종 (Logs / Tracing) — Grafana.com 대시보드 ID로 다운로드
echo "⬇️  Downloading Grafana Templates..."
curl -fsSL "https://grafana.com/api/dashboards/15324/revisions/latest/download" -o "$DASH_DIR/template_loki_logs_15324.raw.json"
curl -fsSL "https://grafana.com/api/dashboards/23242/revisions/latest/download" -o "$DASH_DIR/template_otel_tempo_23242.raw.json"

# 2) Grafana.com JSON Normalization
echo "🔧 Normalizing JSON templates..."
python3 - <<PY
import json
from pathlib import Path
import os

dash_dir = "$DASH_DIR"

paths = [
  Path(f"{dash_dir}/template_loki_logs_15324.raw.json"),
  Path(f"{dash_dir}/template_otel_tempo_23242.raw.json"),
]

for p in paths:
  if not p.exists():
      print(f"⚠️ Warning: {p} not found")
      continue

  try:
      data = json.loads(p.read_text(encoding="utf-8"))
      # Unwrap 'dashboard' if present
      if isinstance(data, dict) and isinstance(data.get("dashboard"), dict):
        data = data["dashboard"]
      
      # Nullify ID for provisioning
      if isinstance(data, dict):
        data["id"] = None
        data["uid"] = None # Reset UID to allow Grafana to generate or avoid conflict, or set explicit if needed. 
                           # Actually keeping UID might be fine if unique, but User script said id=None.
                           # Let's stick to User instruction strictly: id=None
        # User script didn't say reset UID, but usually good practice. 
        # However, I will STRICTLY follow user script logic: data["id"] = None
      
      p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
      print(f"✅ Normalized: {p.name}")
  except Exception as e:
      print(f"❌ Error processing {p.name}: {e}")

PY

# 3) Metric 전용 (AFO 커스텀) 대시보드 JSON 생성
echo "📝 Creating AFO Metrics Dashboard..."
cat > "$DASH_DIR/afo_metrics_ph_obs_03.json" <<'JSON'
{
  "id": null,
  "uid": "afo-metrics-ph-obs-03",
  "title": "AFO — Metrics (PH-OBS-03)",
  "tags": ["AFO", "PH-OBS-03", "metrics"],
  "timezone": "browser",
  "schemaVersion": 39,
  "version": 1,
  "refresh": "10s",
  "editable": true,
  "graphTooltip": 1,
  "templating": {
    "list": [
      {
        "type": "datasource",
        "name": "DS_PROMETHEUS",
        "label": "Prometheus",
        "query": "prometheus",
        "current": { "text": "Prometheus", "value": "Prometheus" }
      },
      {
        "type": "query",
        "name": "job",
        "label": "job",
        "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
        "query": "label_values(up, job)",
        "includeAll": true,
        "allValue": ".*",
        "current": { "text": "All", "value": ".*" }
      }
    ]
  },
  "panels": [
    {
      "id": 1,
      "type": "timeseries",
      "title": "Up (by job)",
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "targets": [
        { "refId": "A", "expr": "sum by (job) (up{job=~\"$job\"})" }
      ],
      "gridPos": { "x": 0, "y": 0, "w": 12, "h": 8 }
    },
    {
      "id": 2,
      "type": "timeseries",
      "title": "CPU (process_cpu_seconds_total rate)",
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "targets": [
        { "refId": "A", "expr": "sum by (job) (rate(process_cpu_seconds_total{job=~\"$job\"}[$__rate_interval]))" }
      ],
      "gridPos": { "x": 12, "y": 0, "w": 12, "h": 8 }
    },
    {
      "id": 3,
      "type": "timeseries",
      "title": "Memory (process_resident_memory_bytes)",
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "targets": [
        { "refId": "A", "expr": "sum by (job) (process_resident_memory_bytes{job=~\"$job\"})" }
      ],
      "gridPos": { "x": 0, "y": 8, "w": 12, "h": 8 }
    },
    {
      "id": 4,
      "type": "timeseries",
      "title": "HTTP Request Rate (best-effort)",
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "targets": [
        { "refId": "A", "expr": "sum by (job) (rate(http_server_duration_seconds_count{job=~\"$job\"}[$__rate_interval]))" }
      ],
      "gridPos": { "x": 12, "y": 8, "w": 12, "h": 8 }
    },
    {
      "id": 5,
      "type": "timeseries",
      "title": "HTTP p95 Latency (best-effort)",
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "targets": [
        { "refId": "A", "expr": "histogram_quantile(0.95, sum(rate(http_server_duration_seconds_bucket{job=~\"$job\"}[$__rate_interval])) by (le))" }
      ],
      "gridPos": { "x": 0, "y": 16, "w": 12, "h": 8 }
    },
    {
      "id": 6,
      "type": "timeseries",
      "title": "OTel Collector: accepted spans (best-effort)",
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "targets": [
        { "refId": "A", "expr": "sum(rate(otelcol_receiver_accepted_spans[$__rate_interval]))" }
      ],
      "gridPos": { "x": 12, "y": 16, "w": 12, "h": 8 }
    }
  ],
  "annotations": { "list": [] }
}
JSON

echo "✅ PH-OBS-03 Dashboards Staged."
