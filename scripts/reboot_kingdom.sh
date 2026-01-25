#!/bin/bash

# 🏰 AFO Kingdom Reboot Script
# Operation Clean Slate: Kill everything, then restart in order.

set -e

echo "==================================================="
echo "   🔄 OPERATION CLEAN SLATE: SYSTEM REBOOT         "
echo "==================================================="

# 1. Kill confirmed ports
PORTS=(3000 3001 3002 3003 3004 3005 8000 8010)

echo ">> 🧹 Cleaning ports: ${PORTS[*]}"

for PORT in "${PORTS[@]}"; do
    echo "   -> Checking Port $PORT..."
    # Kill all PIDs on this port, suppressing errors if empty
    lsof -t -i :"$PORT" | xargs -r kill -9 2>/dev/null || true
done

echo ">> ⏳ Waiting for ports to clear..."
sleep 2

# 2. Start Backend (Port 8010)
echo ""
echo ">> 🔌 [1/3] Starting Backend Core (Port 8010)..."
cd packages/afo-core
# Use venv python if exists
if [ -f "../../.venv/bin/python" ]; then
    PYTHON_EXE="../../.venv/bin/python"
else
    PYTHON_EXE="python3"
fi
# Run in background, redirect output
# Note: PORT environment variable is optional - api_server.py uses settings.API_SERVER_PORT (default: 8010)
export PYTHONPATH=".:../trinity-os:$PYTHONPATH"
API_SERVER_PORT=8010 nohup $PYTHON_EXE AFO/api_server.py > ../../api_server_reboot.log 2>&1 &
BACKEND_PID=$!
echo "   -> Backend started (PID: $BACKEND_PID). Logs: api_server_reboot.log"
cd ../..

echo ">> ⏳ Waiting for Backend to initialize (5s)..."
# Wait loop to check if port 8010 is listening
sleep 5

# 3. Start AICPA (Port 3005)
echo ""
echo ">> 🤖 [2/3] Starting AICPA Julie (Port 3005)..."
cd AICPA/aicpa-core
nohup npm run dev > ../../aicpa_reboot.log 2>&1 &
AICPA_PID=$!
echo "   -> AICPA started (PID: $AICPA_PID). Logs: aicpa_reboot.log"
cd ../..

# 4. Start Dashboard (Port 3000)
echo ""
echo ">> 🖥️  [3/3] Starting Trinity Dashboard (Port 3000)..."
cd packages/dashboard
nohup npm run dev > ../../dashboard_reboot.log 2>&1 &
DASH_PID=$!
echo "   -> Dashboard started (PID: $DASH_PID). Logs: dashboard_reboot.log"
cd ../..

echo ""
echo "==================================================="
echo "✅ REBOOT COMPLETE"
echo "   - Backend: PID $BACKEND_PID"
echo "   - AICPA:   PID $AICPA_PID"
echo "   - Dash:    PID $DASH_PID"
echo "==================================================="
