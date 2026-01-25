import asyncio
import os
import pathlib
import sys

# Set path to allow imports
sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
)

from AFO.agents.samahwi_core import samahwi


async def main():
    print("🤖 Awakening Samahwi...")

    # Test 1: Basic Thinking
    print("\n[Test 1] Contemplation")
    res1 = await samahwi.run("What is the meaning of life?")
    print(f"Result: {res1}")

    # Test 2: Action (Widget Generation Trigger)
    print("\n[Test 2] Widget Creation Request")
    res2 = await samahwi.run("Create a Trinity Status Widget")
    print(f"Result: {res2}")

    if "Phase 16-2" in res2:
        print("\n✅ Phase 16-1 COMPLETE: Samahwi Core is Awake and Responsive.")
    else:
        print("\n❌ PHASE 16-1 FAILED: Agent logic check failed.")


if __name__ == "__main__":
    asyncio.run(main())
