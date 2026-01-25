import asyncio
import sys

# Set PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent / "packages" / "afo-core"))

from AFO.scholars.yeongdeok import yeongdeok


async def verify_empowerment():
    print("🛠️ Verifying Yeongdeok's Tool Capability...\n")

    # Test 1: Try to use the MCP Tool Bridge
    print("1. Testing MCP Tool Bridge usage:")
    res1 = await yeongdeok.use_tool("skill_012_mcp_tool_bridge", action="list_tools")
    print(f"Result:\n{res1}\n")

    # Test 2: Try to use a non-existent tool (Error Handling)
    print("2. Testing Invalid Tool usage:")
    res2 = await yeongdeok.use_tool("skill_999_fake_tool")
    print(f"Result:\n{res2}\n")


if __name__ == "__main__":
    asyncio.run(verify_empowerment())
