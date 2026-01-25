#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${AFO_BASE_URL:-http://127.0.0.1:8010}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

PY_JSON="python3.12"
command -v "$PY_JSON" >/dev/null 2>&1 || PY_JSON="python3"

PY_MCP="${REPO_ROOT}/packages/afo-core/.venv/bin/python"
if [ ! -x "$PY_MCP" ]; then
  PY_MCP="$PY_JSON"
fi

echo "[0/5] Prime MCP (npx servers)"
PYTHONPATH="${REPO_ROOT}/packages/afo-core" "$PY_MCP" - <<'PY'
from services.mcp_stdio_client import list_tools

for name in ["memory", "filesystem", "sequential-thinking", "context7"]:
    try:
        tools = list_tools(name)
        print(f"{name}: OK ({len(tools)} tools)")
    except Exception as e:
        print(f"{name}: ERROR ({type(e).__name__}) {e}")
PY

echo

echo "[1/5] Health (nocache)"
curl -sS -m 15 "${BASE_URL}/api/health/comprehensive?nocache=$(date +%s)" | "$PY_JSON" -m json.tool | sed -n '1,120p'

echo

echo "[2/5] Integrity"
curl -sS -m 15 -H 'Content-Type: application/json' -d '{}' "${BASE_URL}/api/integrity/check" | "$PY_JSON" -m json.tool | sed -n '1,160p'

echo

echo "[3/5] Codex MCP servers"
codex mcp list | sed -n '1,60p'

echo

echo "[4/5] Cursor MCP config (repo)"
if [ -f .cursor/mcp.json ]; then
  "$PY_JSON" - <<'PY'
import json
from pathlib import Path
p=Path('.cursor/mcp.json')
data=json.loads(p.read_text())
servers=data.get('mcpServers',{})
afo=[k for k in servers if k.startswith('afo-') or k.startswith('trinity-')]
print('afo_servers',afo)
for name in afo:
    s=servers[name]
    print(name,'command=',s.get('command'))
PY
else
  echo "missing .cursor/mcp.json"
fi

echo

echo "[5/5] MCP tool sanity (sequential_thinking + retrieve_context)"
"$PY_JSON" - <<'PY'
import json
import os
import re
import subprocess
from pathlib import Path

DEFAULT_PATTERN = re.compile(r"\$\{([A-Z0-9_]+):-([^}]+)\}")


def expand(v: str) -> str:
    v = DEFAULT_PATTERN.sub(lambda m: os.getenv(m.group(1), m.group(2)), v)
    return os.path.expandvars(v)


cfg_path = Path(".cursor/mcp.json")
if not cfg_path.exists():
    raise SystemExit("missing .cursor/mcp.json")

cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
server = cfg.get("mcpServers", {}).get("afo-ultimate-mcp")
if not server:
    raise SystemExit("missing afo-ultimate-mcp in .cursor/mcp.json")

cmd = expand(server.get("command", ""))
args = [expand(a) for a in (server.get("args") or [])]

env = os.environ.copy()
for k, v in (server.get("env") or {}).items():
    env[str(k)] = expand(str(v))

p = subprocess.Popen(
    [cmd, *args],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env=env,
)
assert p.stdin and p.stdout

try:
    init = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "checklist", "version": "0"},
        },
    }
    p.stdin.write(json.dumps(init) + "\n")
    p.stdin.flush()
    p.stdout.readline()

    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "sequential_thinking",
            "arguments": {
                "thought": "Unify AFO + TRINITY-OS + SixXon via SSOT configs.",
                "thought_number": 1,
                "total_thoughts": 3,
                "next_thought_needed": True,
            },
        },
    }
    p.stdin.write(json.dumps(req) + "\n")
    p.stdin.flush()
    resp = json.loads(p.stdout.readline())
    seq_txt = resp.get("result", {}).get("content", [{}])[0].get("text", "")
    print("sequential_thinking:", seq_txt[:200])

    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "retrieve_context",
            "arguments": {"query": "AFO Architecture", "domain": "technical"},
        },
    }
    p.stdin.write(json.dumps(req) + "\n")
    p.stdin.flush()
    resp = json.loads(p.stdout.readline())
    ctx_txt = resp.get("result", {}).get("content", [{}])[0].get("text", "")
    print("retrieve_context:", ctx_txt[:220])
finally:
    p.terminate()
    try:
        p.wait(timeout=2)
    except Exception:
        p.kill()
PY
