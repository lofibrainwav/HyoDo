import asyncio
import os
import sys

# Add package root to sys.path
sys.path.append(os.path.abspath("packages/afo-core"))

from application.trinity.debate_service import trinity_service
from domain.trinity.models import StrategistType


async def verify_trinity_debate():
    print(
        "🏛️ Starting Phase 6 Verification: Trinity Resonance (Real Parallel Debate - Streaming Mode)"
    )

    query = (
        "Should I use Section 179 for my tech startup's new servers, or go with bonus depreciation?"
    )
    print(f"📝 Debate Query: {query}\n")

    print("⏳ Convening the Council of Three (Parallel Analysis)...")

    accumulated_responses = {}

    try:
        async for item in trinity_service.conduct_debate_stream(query):
            persona = item["persona"]
            chunk = item["chunk"]

            if persona not in accumulated_responses:
                accumulated_responses[persona] = ""
            accumulated_responses[persona] += chunk

            # Print a dot for progress to avoid spamming
            print(".", end="", flush=True)

    except Exception as e:
        print(f"\n❌ Error during debate stream: {e}")
        return False

    print("\n\n✅ Debate Stream Complete!")

    # Validation
    required_personas = [
        StrategistType.JANG_YEONG_SIL.value,
        StrategistType.YI_SUN_SIN.value,
        StrategistType.SHIN_SAIMDANG.value,
        "synthesis",
    ]

    for p in required_personas:
        if p not in accumulated_responses:
            print(f"❌ FAIL: Missing content for persona: {p}")
            return False
        content = accumulated_responses[p]
        if not content.strip():
            print(f"❌ FAIL: Empty content for persona: {p}")
            return False

        print(f"\n👤 Persona: {p}")
        print(f"🧠 Content: {content[:100]}... (Total {len(content)} chars)")

    print("\n✅ All strategists participated and synthesis was received.")
    return True


if __name__ == "__main__":
    success = asyncio.run(verify_trinity_debate())
    if not success:
        sys.exit(1)
