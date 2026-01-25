import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path.cwd() / "packages/afo-core"))

from application.trinity.metacognitive_service import metacognitive_service


async def test_audit():
    print("🧠 Starting Isolated Metacognitive Audit Test...")
    target = "Phase 5.5 (Family Integration)"

    count = 0
    try:
        async for reflection in metacognitive_service.audit_system_stream(target):
            persona = reflection.get("persona")
            chunk = reflection.get("chunk")
            print(f"[{persona}] {chunk}", end="", flush=True)
            count += 1
            if count > 100:
                break

        print("\n\n✅ Test Complete. Audit generated.")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_audit())
