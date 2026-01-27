#!/usr/bin/env python3
import asyncio
import os
import sys

# Add workspace root
WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT", "./packages/afo-core")
if WORKSPACE_ROOT not in sys.path:
    sys.path.append(WORKSPACE_ROOT)

from AFO.api.services.suggestion_service import publish_proactive_suggestion


async def test_proactive_suggestion():
    print("🧪 Testing Proactive Suggestion Service...")

    # Mocking Lushun (Beauty/Marketing Scholar)
    success = await publish_proactive_suggestion(
        source="Lushun (Strategic Advisor)",
        message="[Idea of the Day] Implement 'Seals of Authenticity' on all generated PRDs to ensure long-term Eternity (永) tracking.",
        priority="high",
        action_url="file://./prd.json",
        metadata={"category": "Eternity", "pattern": "IdeaBrowser"},
    )

    if success:
        print("✅ Suggestion published to 'chancellor_thought_stream' Redis channel.")
    else:
        print("❌ Failed to publish suggestion.")


if __name__ == "__main__":
    asyncio.run(test_proactive_suggestion())
