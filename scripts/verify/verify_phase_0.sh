#!/bin/bash
echo "=== Phase 0 Verification Start ==="
lsof -ti:8010 | xargs kill -9 || true
./START.sh > server_verification.log 2>&1 &
SERVER_PID=$!
sleep 15

echo "--- 1. Root Health Check ---"
curl -s http://localhost:8010/api/health
echo ""

echo "--- 2. Comprehensive Health Check ---"
curl -s http://localhost:8010/api/health/comprehensive | grep -o 'status":"[^"]*"'
echo ""

echo "--- 3. Trinity SSE Check ---"
curl -s --max-time 10 http://localhost:8010/api/trinity/stream | head -n 4

echo "--- 4. Core Quality (Pytest) ---"
PYTHONPATH=$PYTHONPATH:$(pwd)/packages/afo-core ./.venv/bin/python -m pytest tests/coverage_crusade/test_julie_core.py

echo "--- 5. Cleanup ---"
kill $SERVER_PID || true
lsof -ti:8010 | xargs kill -9 || true
echo "=== Phase 0 Verification End ==="
