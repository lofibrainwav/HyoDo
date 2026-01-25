#!/usr/bin/env bash
set -u

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT" 2>/dev/null || exit 0

ts="$(python3 -c "
from datetime import datetime
print(datetime.now().astimezone().isoformat(timespec='seconds'))
"
)"

branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "UNKNOWN")"
sha="$(git rev-parse --short HEAD 2>/dev/null || echo "UNKNOWN")"

port_status="$(python3 -c "
import socket
def chk(port):
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=0.25):
            return 'OPEN'
    except Exception:
        return 'DOWN'
print(f'8010={chk(8010)} 3000={chk(3000)}')
"
)"

http_8010="$(curl -sS --max-time 2 -o /dev/null -w "%{http_code}" "http://127.0.0.1:8010/health" || echo "000")"
http_3000="$(curl -sS --max-time 2 -o /dev/null -w "%{http_code}" "http://127.0.0.1:3000/" || echo "000")"

title="$(curl -sS --max-time 2 "http://127.0.0.1:3000/" 2>/dev/null | tr -d '\r\n' | sed -n 's/.*<title>(.*)<\/title>.*/\1/p' | head -n 1)"
if [ -z "${title:-}" ]; then title=""; fi

pw="$(python3 -c "
import importlib.util
spec = importlib.util.find_spec('playwright')
if not spec:
    print('playwright=MISSING version=NA')
else:
    try:
        import playwright
        v = getattr(playwright, '__version__', 'UNKNOWN')
    except Exception:
        v = 'UNKNOWN'
    print(f'playwright=OK version={v}')
" 2>/dev/null || echo "playwright=UNKNOWN version=NA")"

seal="$(python3 -c "
import os, subprocess, sys
p = os.path.join(os.getcwd(), 'ssot_verify.sh')
if not os.path.exists(p):
    print('ssot_verify.sh=MISSING exit=127')
    sys.exit(0)
try:
    r = subprocess.run(['bash', p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
    print(f'ssot_verify.sh=RAN exit={r.returncode}')
except subprocess.TimeoutExpired:
    print('ssot_verify.sh=TIMEOUT exit=124')
except Exception:
    print('ssot_verify.sh=ERROR exit=1')
" 2>/dev/null || echo "ssot_verify.sh=UNKNOWN exit=NA")"

echo "E1_REF: time=${ts} branch=${branch} sha=${sha}"
echo "E2_INFRA: ${port_status}"
echo "E3_HTTP: 8010/health=${http_8010} 3000/=${http_3000}"
echo "E4_VIEW: title=\"${title}\""
echo "E5_ENV: ${pw}"
echo "E6_SEAL: ${seal}"

exit 0
