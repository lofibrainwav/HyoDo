#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
mkdir -p artifacts

# Detect Python
PYTHON_BIN="python3"
if [ -f "packages/afo-core/.venv/bin/python" ]; then
    PYTHON_BIN="packages/afo-core/.venv/bin/python"
fi
echo "Using Python: $PYTHON_BIN"

# --- Probes ---

# 1. Penpot (Mock/Real HTTP)
echo "Probing Penpot..."
if curl -s --head --request GET "http://localhost:9001" | grep "200 OK" > /dev/null; then
    echo '{"status": "healthy", "version": "unknown", "ts": "'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'"}' > artifacts/penpot-health.json
else
    echo '{"status": "offline", "error": "connection refused", "ts": "'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'"}' > artifacts/penpot-health.json
fi

# 2. Coolify (Mock/Real HTTP)
echo "Probing Coolify..."
if curl -s --head --request GET "http://localhost:8000" | grep "200 OK" > /dev/null; then
    echo '{"status": "healthy", "version": "unknown", "ts": "'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'"}' > artifacts/coolify-health.json
else
    echo '{"status": "offline", "error": "connection refused", "ts": "'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'"}' > artifacts/coolify-health.json
fi

# 3. Mattermost (Mock/Real HTTP)
echo "Probing Mattermost..."
if curl -s --head --request GET "http://localhost:8065" | grep "200 OK" > /dev/null; then
    echo '{"status": "healthy", "version": "unknown", "ts": "'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'"}' > artifacts/mattermost-health.json
else
    echo '{"status": "offline", "error": "connection refused", "ts": "'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'"}' > artifacts/mattermost-health.json
fi

# 4. LangGraph (Python Import)
echo "Probing LangGraph..."
if "$PYTHON_BIN" -c "import langgraph" > /dev/null 2>&1; then
    VERSION=$("$PYTHON_BIN" -c "import langgraph; print(langgraph.__version__ if hasattr(langgraph, '__version__') else 'unknown')")
    echo "{\"status\": \"healthy\", \"version\": \"$VERSION\", \"ts\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}" > artifacts/langgraph-version.json
else
    echo '{"status": "uninstalled", "error": "module not found", "ts": "'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'"}' > artifacts/langgraph-version.json
fi

# 5. Optuna (Python Import)
echo "Probing Optuna..."
if "$PYTHON_BIN" -c "import optuna" > /dev/null 2>&1; then
    VERSION=$("$PYTHON_BIN" -c "import optuna; print(optuna.__version__)")
    echo "{\"status\": \"healthy\", \"version\": \"$VERSION\", \"ts\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}" > artifacts/optuna-version.json
else
    echo '{"status": "uninstalled", "error": "module not found", "ts": "'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'"}' > artifacts/optuna-version.json
fi

# 6. Fairlearn (Python Import)
echo "Probing Fairlearn..."
if "$PYTHON_BIN" -c "import fairlearn" > /dev/null 2>&1; then
    VERSION=$("$PYTHON_BIN" -c "import fairlearn; print(fairlearn.__version__ if hasattr(fairlearn, '__version__') else 'unknown')")
    echo "{\"status\": \"healthy\", \"version\": \"$VERSION\", \"ts\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}" > artifacts/fairlearn-version.json
else
    echo '{"status": "uninstalled", "error": "module not found", "ts": "'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'"}' > artifacts/fairlearn-version.json
fi

# 7. TFLite (Python Import)
echo "Probing TFLite..."
if "$PYTHON_BIN" -c "import tflite_runtime" > /dev/null 2>&1; then
    echo "{\"status\": \"healthy\", \"version\": \"runtime\", \"ts\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}" > artifacts/tflite-version.json
elif "$PYTHON_BIN" -c "from tensorflow import lite" > /dev/null 2>&1; then
    echo "{\"status\": \"healthy\", \"version\": \"tensorflow.lite\", \"ts\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}" > artifacts/tflite-version.json
else
    echo '{"status": "uninstalled", "error": "module not found", "ts": "'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'"}' > artifacts/tflite-version.json
fi

# 8. K8s Ops (Kubectl Check)
echo "Probing K8s Ops..."
if command -v kubectl > /dev/null 2>&1; then
    CONTEXT=$(kubectl config current-context 2>/dev/null || echo "none")
    echo "{\"status\": \"healthy\", \"context\": \"$CONTEXT\", \"ts\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}" > artifacts/k8s-ops-status.json
else
    echo '{"status": "unavailable", "error": "kubectl not found", "ts": "'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'"}' > artifacts/k8s-ops-status.json
fi

echo "Probes complete. Evidence saved to artifacts/."
