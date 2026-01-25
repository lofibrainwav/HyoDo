import json
import pathlib
import signal
import subprocess
import sys
import time

p = pathlib.Path(".cursor/mcp.json")
data = json.loads(p.read_text(encoding="utf-8"))
servers = data.get("mcpServers") or data.get("servers") or {}

results = {}
ok = True

for name, cfg in servers.items():
    cmd = cfg.get("command")
    args = cfg.get("args") or []
    if not cmd:
        results[name] = {"ok": False, "reason": "no command"}
        ok = False
        continue

    try:
        proc = subprocess.Popen(
            [cmd, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        time.sleep(1.2)
        rc = proc.poll()
        if rc is None:
            proc.send_signal(signal.SIGTERM)
            results[name] = {"ok": True, "reason": "started"}
        else:
            out = (proc.stdout.read() if proc.stdout else "")[:400]
            err = (proc.stderr.read() if proc.stderr else "")[:400]
            results[name] = {
                "ok": False,
                "reason": f"exited rc={rc}",
                "stdout": out,
                "stderr": err,
            }
            ok = False
    except Exception as e:
        results[name] = {"ok": False, "reason": f"spawn error: {e}"}
        ok = False

print(json.dumps(results, ensure_ascii=False, indent=2))
sys.exit(0 if ok else 2)
