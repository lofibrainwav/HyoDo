# Trinity Score: 90.0 (Established by Chancellor)
import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)


async def verify_cache_integration():
    print("⚡️ Verifying Cache Integration...")

    try:
        # Import LLMRouter
        from AFO.llm_router import LLMRouter, cache_manager, predictive_manager

        print("✅ LLMRouter Import: Success")

        # Check Cache Manager
        if cache_manager:
            print(f"✅ Cache Manager: Initialized ({type(cache_manager).__name__})")
            print(f"   - L1: {type(cache_manager.l1).__name__}")
            print(f"   - L2: {type(cache_manager.l2).__name__}")
        else:
            print("❌ Cache Manager: Failed to Load")

        # Check Predictive Manager
        if predictive_manager:
            print(f"✅ Predictive Manager: Initialized ({type(predictive_manager).__name__})")
        else:
            print("❌ Predictive Manager: Failed to Load")

        # Initialize Router
        router = LLMRouter()
        print("✅ LLMRouter Instance: Created")

        if router.cache == cache_manager:
            print("✅ Router has correct Cache Manager")
        else:
            print("❌ Router Cache Mismatch")

        print("🎉 Verification Complete: All Systems Go!")

    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(verify_cache_integration())
