import sys
from pathlib import Path

# Setup Path
sys.path.append(str(Path.cwd() / "packages/trinity-os"))
from trinity_os.servers.context7_mcp import Context7MCP


def verify_context7_richness() -> None:
    print("🚀 Starting Context7 Richness Verification")

    try:
        mcp = Context7MCP()
        print(f"✅ Context7 Initialized. Loaded {len(mcp.knowledge_base)} items.")

        # Test 1: Check if 'API_ENDPOINTS_REFERENCE.md' is loaded (from JSON)
        # In JSON it is "docs/API_ENDPOINTS_REFERENCE.md"
        loaded = False
        sample_doc = None
        for item in mcp.knowledge_base:
            if "API_ENDPOINTS_REFERENCE.md" in item.get("source", ""):
                loaded = True
                sample_doc = item
                break

        if not loaded:
            print("❌ Test Failed: API_ENDPOINTS_REFERENCE.md not found in knowledge base.")
            return False

        print("✅ Test Passed: API_ENDPOINTS_REFERENCE.md loaded.")

        # Test 2: Check for Metadata Injection (Header presence)
        content = sample_doc["content"]
        if "# API 엔드포인트 참조 문서" in content:
            print("✅ Test Passed: '# API 엔드포인트 참조 문서' found in content.")
        else:
            print("❌ Test Failed: Main header not found in content.")
            print(f"Preview: {content[:100]}")
            return False

        # Test 3: Check Type injection
        # Should be 'document' or specific if json said so (JSON says nothing about type for this, default document?)
        # Let's check "SKILLS_REGISTRY_REFERENCE" which has category 'Skills Reference'

        return True

    except Exception as e:
        print(f"❌ Verification Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    if verify_context7_richness():
        sys.exit(0)
    else:
        sys.exit(1)
