import asyncio
import json
import os
import sys

# Add package root to sys.path
sys.path.append(os.path.abspath("packages/afo-core"))

from application.trinity.debate_service import trinity_service


async def verify_streaming_debate():
    print("🏛️ Starting Phase 7 Verification: Streaming Trinity Resonance")

    query = "Is it better to lease or buy equipment for a new tech hub?"
    print(f"📝 Streaming Query: {query}\n")

    print("⏳ Convening the Council (Streaming Parallel Analysis)...")

    counts = {"zhuge_liang": 0, "sima_yi": 0, "zhou_yu": 0, "synthesis": 0}

    try:
        async for chunk_data in trinity_service.conduct_debate_stream(query):
            persona = chunk_data["persona"]
            _chunk = chunk_data["chunk"]
            counts[persona] += 1

            # Print a dot for each chunk to show "activity"
            print(f"{persona[0].upper()}", end="", flush=True)

    except Exception as e:
        print(f"\n❌ Error during streaming: {e}")
        return False

    print("\n\n✅ Stream Complete!")
    print(f"📊 Chunk Counts: {counts}")

    # Assertions
    success = True
    for strategist in ["zhuge_liang", "sima_yi", "zhou_yu"]:
        if counts[strategist] == 0:
            print(f"❌ FAIL: {strategist} did not stream any chunks!")
            success = False

    if counts["synthesis"] == 0:
        print("❌ FAIL: No synthesis chunk received!")
        success = False

    if success:
        print("\n✅ All strategists streamed chunks in parallel and synthesis was delivered.")
    return success


if __name__ == "__main__":
    success = asyncio.run(verify_streaming_debate())
    if not success:
        sys.exit(1)
