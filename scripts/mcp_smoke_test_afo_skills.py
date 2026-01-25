#!/usr/bin/env python3
"""
MCP Smoke Test for AFO Skills Server
Tests basic MCP protocol compliance and tool listing functionality.
Enhanced with better error handling, timeouts, and logging.
"""

import json
import os
import signal
import subprocess
import sys
from pathlib import Path


class TimeoutError(Exception):
    """Custom timeout exception"""


def timeout_handler(signum, frame) -> None:
    """Signal handler for timeout"""
    raise TimeoutError("Test timed out")


def run_mcp_server_test(timeout_seconds: int = 30) -> bool:
    """Test MCP server using subprocess and stdio with enhanced error handling"""
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "packages" / "afo-core")
    env.setdefault("AFO_API_BASE_URL", "http://127.0.0.1:8010")

    # Start MCP server process
    server_cmd = [sys.executable, "-m", "AFO.mcp.afo_skills_mcp"]

    print("🚀 Starting AFO Skills MCP Server...")
    print(f"Command: {' '.join(server_cmd)}")
    print(f"PYTHONPATH: {env['PYTHONPATH']}")
    print(f"AFO_API_BASE_URL: {env['AFO_API_BASE_URL']}")
    print(f"Test timeout: {timeout_seconds} seconds")
    print()

    server_proc: subprocess.Popen | None = None

    try:
        # Set up timeout handler
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)

        # Start server process
        server_proc = subprocess.Popen(
            server_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            bufsize=1,
            start_new_session=True,  # Create new process group for better cleanup
        )

        print("📋 Sending initialize request...")

        # Send initialize request
        init_request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        server_proc.stdin.write(json.dumps(init_request) + "\n")
        server_proc.stdin.flush()

        # Read initialize response with timeout
        init_response_line = server_proc.stdout.readline().strip()
        if init_response_line:
            init_response = json.loads(init_response_line)
            server_name = (
                init_response.get("result", {}).get("serverInfo", {}).get("name", "Unknown")
            )
            server_version = (
                init_response.get("result", {}).get("serverInfo", {}).get("version", "Unknown")
            )
            print(f"✅ Initialize response: {server_name} v{server_version}")
        else:
            print("❌ No initialize response received")
            return False

        print("📋 Sending notifications/initialized...")
        # Send initialized notification (Required by protocol)
        initialized_notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
        server_proc.stdin.write(json.dumps(initialized_notif) + "\n")
        server_proc.stdin.flush()

        print("📋 Sending tools/list request...")

        # Send tools/list request
        list_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        server_proc.stdin.write(json.dumps(list_request) + "\n")
        server_proc.stdin.flush()

        # Read tools/list response with timeout
        list_response_line = server_proc.stdout.readline().strip()
        if list_response_line:
            list_response = json.loads(list_response_line)
            tools = list_response.get("result", {}).get("tools", [])
            tool_names = [tool.get("name", "unknown") for tool in tools]

            print(f"✅ Tools found: {len(tools)}개")
            print(f"   도구 목록: {', '.join(tool_names)}")

            # Verify expected tools
            expected_tools = [
                "skills_list",
                "skills_detail",
                "skills_execute",
                "genui_generate",
                "afo_api_health",
            ]
            missing_tools = [tool for tool in expected_tools if tool not in tool_names]
            extra_tools = [tool for tool in tool_names if tool not in expected_tools]

            if missing_tools:
                print(f"❌ 누락된 도구: {missing_tools}")
                return False
            if extra_tools:
                print(f"⚠️  추가된 도구: {extra_tools}")

            # Check stderr safely (peek if possible, or skip to avoid blocking)
            # stderr_output = server_proc.stderr.read()
            # if stderr_output.strip():
            #     print(f"⚠️  Server stderr output: {stderr_output.strip()}")

            print("✅ 모든 예상 도구가 정상적으로 등록됨")
            return True

        print("❌ No tools/list response received")
        # Check stderr for clues
        stderr_output = server_proc.stderr.read()
        if stderr_output.strip():
            print(f"Server stderr: {stderr_output.strip()}")
        return False

    except TimeoutError:
        print(f"❌ Test timed out after {timeout_seconds} seconds")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        # Restore signal handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

        # Clean up server process
        if server_proc:
            try:
                # Try graceful termination first
                server_proc.terminate()
                try:
                    server_proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    print("⚠️  Server didn't terminate gracefully, force killing...")
                    # Force kill the entire process group
                    os.killpg(os.getpgid(server_proc.pid), signal.SIGKILL)
            except Exception as e:
                print(f"⚠️  Error during cleanup: {e}")


def main() -> None:
    """Main test function"""
    print("🧪 AFO Skills MCP Server Smoke Test")
    print("=" * 50)

    success = run_mcp_server_test()

    print()
    print("=" * 50)
    if success:
        print("🎉 SMOKE TEST PASSED")
        print("✅ AFO Skills MCP Server is ready for Cursor IDE integration")
        return 0
    print("💥 SMOKE TEST FAILED")
    print("❌ AFO Skills MCP Server needs debugging")
    return 1


if __name__ == "__main__":
    sys.exit(main())
