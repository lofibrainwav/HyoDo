import json
import os
import selectors
import subprocess
import sys
import time

SERVER_MODULE = os.environ.get("MCP_SERVER_MODULE", "AFO.mcp.afo_skills_mcp")
TIMEOUT_S = float(os.environ.get("MCP_SMOKE_TIMEOUT_S", "10"))


def send(w, msg) -> None:
    w.write((json.dumps(msg) + "\n").encode("utf-8"))
    w.flush()


def read_until(sel, want_id, timeout_s) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        events = sel.select(timeout=0.2)
        for key, _ in events:
            line = key.fileobj.readline()
            if not line:
                continue
            try:
                obj = json.loads(line.decode("utf-8", errors="ignore").strip())
            except Exception:
                continue
            if isinstance(obj, dict) and obj.get("id") == want_id:
                return obj
    raise TimeoutError(f"timeout waiting for id={want_id}")


def main() -> None:
    cmd = [sys.executable, "-m", SERVER_MODULE]
    env = os.environ.copy()
    p = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    assert p.stdin and p.stdout and p.stderr

    sel = selectors.DefaultSelector()
    sel.register(p.stdout, selectors.EVENT_READ)

    init_id = 1
    tools_id = 2
    shutdown_id = 3

    send(
        p.stdin,
        {
            "jsonrpc": "2.0",
            "id": init_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "afo-smoke", "version": "2"},
            },
        },
    )
    _ = read_until(sel, init_id, TIMEOUT_S)
    print("OK: initialize")

    send(
        p.stdin,
        {"jsonrpc": "2.0", "id": tools_id, "method": "tools/list", "params": {}},
    )
    tools_resp = read_until(sel, tools_id, TIMEOUT_S)
    tools = (tools_resp.get("result") or {}).get("tools") or []
    print(f"OK: tools/list ({len(tools)})")

    send(
        p.stdin,
        {"jsonrpc": "2.0", "id": shutdown_id, "method": "shutdown", "params": {}},
    )
    try:
        _ = read_until(sel, shutdown_id, TIMEOUT_S)
    except Exception:
        pass

    send(p.stdin, {"jsonrpc": "2.0", "method": "exit", "params": {}})
    try:
        p.stdin.close()
    except Exception:
        pass

    try:
        rc = p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.terminate()
        try:
            rc = p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            p.kill()
            rc = p.wait(timeout=3)

    if rc == 0:
        print("PASS: clean exit (0)")
        return 0

    try:
        err = p.stderr.read().decode("utf-8", errors="ignore")
    except Exception:
        err = ""
    print(f"FAIL: exit ({rc})")
    if err.strip():
        print(err.strip())
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
