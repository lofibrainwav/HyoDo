#!/bin/bash
# AFO Ultimate MCP Server Launcher
# MCP 공식 스펙에 따라 STDIO 기반 JSON-RPC 통신을 제공

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 환경 변수 검증 및 설정
export PYTHONPATH="$PROJECT_ROOT/packages/trinity-os:$PROJECT_ROOT/packages/afo-core:$PYTHONPATH"

# Python 버전 확인
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found" >&2
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "INFO: Using Python $PYTHON_VERSION" >&2

# 프로젝트 디렉토리 존재 확인
if [[ ! -d "$PROJECT_ROOT/packages/trinity-os" ]]; then
    echo "ERROR: Trinity-OS package not found at $PROJECT_ROOT/packages/trinity-os" >&2
    exit 1
fi

if [[ ! -d "$PROJECT_ROOT/packages/afo-core" ]]; then
    echo "ERROR: AFO Core package not found at $PROJECT_ROOT/packages/afo-core" >&2
    exit 1
fi

# MCP 서버 모듈 존재 확인
SERVER_MODULE="$PROJECT_ROOT/packages/trinity-os/trinity_os/servers/afo_ultimate_mcp_server.py"
if [[ ! -f "$SERVER_MODULE" ]]; then
    echo "ERROR: AFO Ultimate MCP Server module not found at $SERVER_MODULE" >&2
    exit 1
fi

echo "INFO: Starting AFO Ultimate MCP Server..." >&2
echo "INFO: Project root: $PROJECT_ROOT" >&2
echo "INFO: Python path: $PYTHONPATH" >&2

# MCP 서버 실행 (에러 발생 시 로그 출력)
python3 -c "
import sys
import logging
import traceback

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

try:
    sys.path.insert(0, '$PROJECT_ROOT/packages/trinity-os')
    sys.path.insert(0, '$PROJECT_ROOT/packages/afo-core')

    from trinity_os.servers.afo_ultimate_mcp_server import AfoUltimateMCPServer
    print('INFO: AFO Ultimate MCP Server loaded successfully', file=sys.stderr)
    AfoUltimateMCPServer.run_loop()

except ImportError as e:
    print(f'ERROR: Import error: {e}', file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f'ERROR: Unexpected error: {e}', file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
"