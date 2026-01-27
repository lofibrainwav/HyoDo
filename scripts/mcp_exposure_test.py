import json
import subprocess
import sys


def test_mcp_tools():
    print("🔬 Testing Skill Registry MCP Tools Exposure")
    print("-" * 45)

    server_path = "./packages/trinity-os/trinity_os/servers/afo_skills_registry_mcp.py"

    # Simulate tools/list
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

    try:
        process = subprocess.Popen(
            [sys.executable, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        stdout, stderr = process.communicate(input=json.dumps(request) + "\n", timeout=10)

        if stderr:
            print(f"Stderr: {stderr}")

        response = json.loads(stdout)
        tools = response.get("result", {}).get("tools", [])

        print(f"Total tools exposed: {len(tools)}")

        # Verify specific missing ones are now present
        tool_names = [t["name"] for t in tools]
        target_skills = [
            "skill_007_automated_debugging",
            "skill_029_multi_cloud_backup",
            "skill_000_trinity_score_calculator",
        ]

        for ts in target_skills:
            status = "✅ Found" if ts in tool_names else "❌ NOT FOUND"
            print(f"  - {ts}: {status}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_mcp_tools()
