import asyncio
import os
import sys

# Create a mock environment
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "packages/afo-core"))

from AFO.domain.metrics.trinity_manager import trinity_manager
from api.routers.trinity import get_trinity_status


async def main():
    print("🚀 Verifying Phase 69: Trinity Score Resonance")

    # 1. Verify TrinityManager Upgrade
    print("\n[1] Check TrinityManager Agent Support")
    if not hasattr(trinity_manager, "agent_deltas"):
        print("❌ Agent Deltas missing!")
        sys.exit(1)

    print("✅ agent_deltas present")

    # 2. Simulate Trigger
    print("\n[2] Simulate Trigger on Jang Yeong-sil")
    trinity_manager.apply_trigger("ELEGANT_RESPONSE", agent_name="jang_yeong_sil")

    metrics = trinity_manager.get_agent_metrics("jang_yeong_sil")
    print(
        f"   Jang Yeong-sil Beauty Delta: {trinity_manager.agent_deltas['jang_yeong_sil']['beauty']}"
    )
    print(f"   Jang Yeong-sil Score: {metrics.trinity_score}")

    if trinity_manager.agent_deltas["jang_yeong_sil"]["beauty"] <= 0:
        print("❌ Trigger failed to update delta")
        sys.exit(1)

    print("✅ Trigger applied successfully")

    # 3. Verify API Response Structure
    print("\n[3] Verify API Response Schema")
    response = await get_trinity_status()

    if "global_metrics" not in response or "agents" not in response:
        print("❌ API response missing keys")
        print(response.keys())
        sys.exit(1)

    if "jang_yeong_sil" not in response["agents"]:
        print("❌ Jang Yeong-sil missing in API response")
        sys.exit(1)

    print("✅ API Schema Verified")
    print("\n🎉 Phase 69 Verification Complete!")


if __name__ == "__main__":
    asyncio.run(main())
