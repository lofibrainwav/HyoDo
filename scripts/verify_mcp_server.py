"""MCP Server Verification Script

Verifies the AFO Ultimate MCP server via JSON-RPC 2.0 (stdio).

SSOT:
- Prefers `.cursor/mcp.json` server config (afo-ultimate-mcp), so the same interpreter/env
  is used by Cursor + Codex + backend integrations.
"""

import json
import os
import pathlib
import re
import selectors
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


_DEFAULT_PATTERN = re.compile(r"\$\{([A-Z0-9_]+):-([^}]+)\}")


def _expand_default_vars(value: str) -> str:
    value = _DEFAULT_PATTERN.sub(lambda m: os.getenv(m.group(1), m.group(2)), value)
    return os.path.expandvars(value)


def _load_server_command() -> tuple[list[str], dict[str, str]]:
    cfg_path = REPO_ROOT / ".cursor" / "mcp.json"
    if cfg_path.exists():
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        server = data.get("mcpServers", {}).get("afo-ultimate-mcp")
        if isinstance(server, dict) and server.get("command") and server.get("args"):
            cmd = [_expand_default_vars(str(server["command"]))]
            args = [_expand_default_vars(str(a)) for a in (server.get("args") or [])]

            env = os.environ.copy()
            for k, v in (server.get("env") or {}).items():
                env[str(k)] = _expand_default_vars(str(v))

            env.setdefault("WORKSPACE_ROOT", str(REPO_ROOT))
            env.setdefault("PYTHONPYCACHEPREFIX", str(REPO_ROOT / ".pycache_mcp_verify"))

            return [*cmd, *args], env

    # Fallback (legacy): best-effort.
    return [
        sys.executable,
        "packages/trinity-os/trinity_os/servers/afo_ultimate_mcp_server.py",
    ], os.environ.copy()


def verify_mcp() -> None:
    print("🔌 Starting AFO Ultimate MCP Server Verification...")

    cmd, env = _load_server_command()

    # Start the server process
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0,  # Unbuffered
        env=env,
    )

    sel = selectors.DefaultSelector()
    assert process.stdout is not None
    sel.register(process.stdout, selectors.EVENT_READ)

    def read_line(timeout: float = 10.0) -> str:
        events = sel.select(timeout)
        if not events:
            raise TimeoutError("timeout waiting for MCP response")
        assert process.stdout is not None
        return process.stdout.readline()

    try:
        # 1. Initialize
        print("\n🔹 Requesting Initialize...")
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "Verifier", "version": "1.0"},
            },
        }
        process.stdin.write(json.dumps(init_req) + "\n")
        process.stdin.flush()

        response_line = read_line(timeout=30.0)
        if not response_line:
            print("❌ No response from server.")
            return

        print(f"Server Response: {response_line.strip()}")
        resp = json.loads(response_line)
        assert resp["result"]["serverInfo"]["name"] == "AfoUltimate"
        print("✅ Initialize Success")

        # MCP handshake requires notifications/initialized after initialize.
        process.stdin.write(
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
            + "\n"
        )
        process.stdin.flush()

        # 2. List Tools
        print("\n🔹 Requesting tools/list...")
        list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        process.stdin.write(json.dumps(list_req) + "\n")
        process.stdin.flush()

        response_line = read_line(timeout=30.0)
        print(f"Server Response: {response_line.strip()}")
        resp = json.loads(response_line)
        tools = resp["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        print(f"Tools Found: {tool_names}")

        has_playwright = "browser_navigate" in tool_names

        assert "shell_execute" in tool_names
        assert "kingdom_health" in tool_names
        assert "calculate_trinity_score" in tool_names
        assert "verify_fact" in tool_names
        print("✅ Tools List Success")

        # 3. Test Trinity Score
        print("\n🔹 Testing calculate_trinity_score...")
        trinity_req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "calculate_trinity_score",
                "arguments": {
                    "truth_base": 90,
                    "goodness_base": 85,
                    "beauty_base": 80,
                    "friction": 0,
                    "eternity_base": 90,
                },
            },
        }
        process.stdin.write(json.dumps(trinity_req) + "\n")
        process.stdin.flush()

        response_line = read_line(timeout=30.0)
        print(f"Tool Response: {response_line.strip()}")
        resp = json.loads(response_line)
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["trinity_score"] > 80
        print("✅ Trinity Score Calculation Success")

        # 4. Test Fact Verification
        print("\n🔹 Testing verify_fact...")
        fact_req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "verify_fact",
                "arguments": {
                    "claim": "The sky is blue",
                    "context": "General knowledge",
                },
            },
        }
        process.stdin.write(json.dumps(fact_req) + "\n")
        process.stdin.flush()

        response_line = read_line(timeout=30.0)
        print(f"Tool Response: {response_line.strip()}")
        resp = json.loads(response_line)
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["verdict"] == "PLAUSIBLE"
        print("✅ Fact Verification Success")

        # 5. Test Shell Execute
        print("\n🔹 Testing shell_execute...")
        shell_req = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "shell_execute",
                "arguments": {"command": "echo 'Hello AFO'"},
            },
        }
        process.stdin.write(json.dumps(shell_req) + "\n")
        process.stdin.flush()

        response_line = read_line(timeout=30.0)
        print(f"Tool Response: {response_line.strip()}")
        resp = json.loads(response_line)
        content = resp["result"]["content"][0]["text"]
        assert "Hello AFO" in content
        print("✅ Shell Execute Success")

        # 6. Test Write File
        print("\n🔹 Testing write_file...")
        test_file_path = "temp_test_mcp.txt"
        write_req = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "write_file",
                "arguments": {
                    "path": test_file_path,
                    "content": "AFO Verification Content",
                },
            },
        }
        process.stdin.write(json.dumps(write_req) + "\n")
        process.stdin.flush()

        response_line = read_line(timeout=30.0)
        print(f"Tool Response: {response_line.strip()}")
        resp = json.loads(response_line)
        assert not resp["result"]["isError"]
        print("✅ Write File Success")

        # 7. Test Read File
        print("\n🔹 Testing read_file...")
        read_req = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "read_file",
                "arguments": {"path": test_file_path},
            },
        }
        process.stdin.write(json.dumps(read_req) + "\n")
        process.stdin.flush()

        response_line = read_line(timeout=30.0)
        print(f"Tool Response: {response_line.strip()}")
        resp = json.loads(response_line)
        content = resp["result"]["content"][0]["text"]
        assert "AFO Verification Content" in content
        print("✅ Read File Success")

        # Cleanup temp file

        if pathlib.Path(test_file_path).exists():
            pathlib.Path(test_file_path).unlink()

        # 8. Test CuPy Weighted Sum
        print("\n🔹 Testing cupy_weighted_sum...")
        math_req = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "cupy_weighted_sum",
                "arguments": {"data": [1.0, 2.0, 3.0], "weights": [0.5, 0.5, 0.5]},
            },
        }
        process.stdin.write(json.dumps(math_req) + "\n")
        process.stdin.flush()

        response_line = read_line(timeout=30.0)
        print(f"Tool Response: {response_line.strip()}")
        resp = json.loads(response_line)
        # Result should be 1*0.5 + 2*0.5 + 3*0.5 = 0.5 + 1.0 + 1.5 = 3.0
        content = resp["result"]["content"][0]["text"]
        assert float(content) == 3.0
        print("✅ CuPy Weighted Sum Success")

        # 9. Test Sequential Thinking
        print("\n🔹 Testing sequential_thinking...")
        think_req = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {
                "name": "sequential_thinking",
                "arguments": {
                    "thought": "Analysis of Trinity Score architecture shows hybrid engine is optimal.",
                    "thought_number": 1,
                    "total_thoughts": 3,
                    "next_thought_needed": True,
                },
            },
        }
        process.stdin.write(json.dumps(think_req) + "\n")
        process.stdin.flush()

        response_line = read_line(timeout=30.0)
        print(f"Tool Response: {response_line.strip()}")
        resp = json.loads(response_line)
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["status"] == "THINKING"
        print("✅ Sequential Thinking Success")

        # 10. Test Context7 (Retrieve Context)
        print("\n🔹 Testing retrieve_context...")
        ctx_req = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {
                "name": "retrieve_context",
                "arguments": {"query": "AFO Architecture", "domain": "technical"},
            },
        }
        process.stdin.write(json.dumps(ctx_req) + "\n")
        process.stdin.flush()

        response_line = read_line(timeout=30.0)
        print(f"Tool Response: {response_line.strip()}")
        resp = json.loads(response_line)
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["found"] is True
        assert "Chancellor" in content["context"]
        print("✅ Context7 Retrieval Success")

        # 11. Test Context7 (Soul & Body)
        print("\n🔹 Testing retrieve_context (Soul & Body)...")
        soul_req = {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {
                "name": "retrieve_context",
                "arguments": {
                    "query": "Sixxon Body Trinity Soul",
                    "domain": "philosophy",
                },
            },
        }
        process.stdin.write(json.dumps(soul_req) + "\n")
        process.stdin.flush()

        response_line = read_line(timeout=30.0)
        print(f"Tool Response: {response_line.strip()}")
        resp = json.loads(response_line)
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["found"] is True
        assert "Sixxon (The Physical Manifestation)" in content["context"]
        assert "Trinity 5 Pillars (The Soul)" in content["context"]
        print("✅ Context7 Soul & Body Retrieval Success")

        # 12. Test Playwright Bridge (Navigate & Scrape)
        print("\n🔹 Testing Playwright Bridge...")
        if not has_playwright:
            print("ℹ️ Playwright tools not available. Skipping browser_* checks.")
        else:
            try:
                # Navigate
                nav_req = {
                    "jsonrpc": "2.0",
                    "id": 12,
                    "method": "tools/call",
                    "params": {
                        "name": "browser_navigate",
                        "arguments": {"url": "http://example.com"},
                    },
                }
                process.stdin.write(json.dumps(nav_req) + "\n")
                process.stdin.flush()

                response_line = read_line(timeout=60.0)
                print(f"Tool Response (Navigate): {response_line.strip()}")
                resp = json.loads(response_line)
                content = json.loads(resp["result"]["content"][0]["text"])

                if content.get("success"):
                    print("✅ Browser Navigation Success")

                    # Scrape
                    scrape_req = {
                        "jsonrpc": "2.0",
                        "id": 13,
                        "method": "tools/call",
                        "params": {
                            "name": "browser_scrape",
                            "arguments": {"selector": "h1"},
                        },
                    }
                    process.stdin.write(json.dumps(scrape_req) + "\n")
                    process.stdin.flush()

                    response_line = read_line(timeout=60.0)
                    print(f"Tool Response (Scrape): {response_line.strip()}")
                    resp = json.loads(response_line)
                    content = json.loads(resp["result"]["content"][0]["text"])
                    assert "Example Domain" in content["content"]
                    print("✅ Browser Scrape Success")
                else:
                    print(f"⚠️ Browser Navigation Failed: {content.get('error')}")
                    print("Skipping Scrape Test due to Navigation Failure")

            except Exception as e:
                print(f"⚠️ Playwright Test Skipped/Failed: {e}")

    finally:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()

        # Print stderr if any (safe only after termination)
        try:
            if process.stderr is not None:
                stderr_output = process.stderr.read()
                if stderr_output:
                    print(f"STDERR: {stderr_output}")
        except Exception:
            pass

    print("\n🎉 MCP Verification Complete!")


if __name__ == "__main__":
    verify_mcp()
