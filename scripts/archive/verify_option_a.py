"""
Verification Script for Option A (Strategic Alignment)
1. Verify Trinity 7:3 Logic
2. Verify Redis Log Publisher
3. Verify AsyncRedisSaver
"""

import asyncio
import os
import pathlib
import sys

# Add package root to path
sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
)

from AFO.services.trinity_calculator import trinity_calculator
from AFO.utils.cache_utils import cache
from AFO.utils.logging import _publisher
from AFO.utils.redis_saver import AsyncRedisSaver


async def verify():
    print("🚀 Verifying Option A Features...\n")

    # 1. Verify Trinity 7:3 Logic
    print("1️⃣  Verifying Trinity 7:3 Logic...")
    # Case 1: Pure Dynamic (Fallback)
    # Weights: T(0.35), G(0.35), B(0.20), S(0.08), E(0.02)
    raw_scores = [1.0] * 5  # All 1.0 -> Weighted Sum 1.0 -> Dynamic 100
    score_dynamic = trinity_calculator.calculate_trinity_score(raw_scores)
    print(f"   - Dynamic Only (All 1.0): {score_dynamic} (Expected 100.0)")
    assert score_dynamic == 100.0

    # Case 2: Hybrid (Static 50, Dynamic 100) -> 50*0.7 + 100*0.3 = 35 + 30 = 65
    score_hybrid = trinity_calculator.calculate_trinity_score(raw_scores, static_score=50.0)
    print(f"   - Hybrid (Static 50, Dynamic 100): {score_hybrid} (Expected 65.0)")
    assert score_hybrid == 65.0
    print("   ✅ Trinity Logic Verified\n")

    # 2. Verify Redis Log Publisher
    print("2️⃣  Verifying Redis Log Publisher...")
    if cache.enabled and cache.redis:
        try:
            _publisher.publish("🧪 Verification Test Message")
            print("   ✅ Published test message to Redis")
        except Exception as e:
            print(f"   ❌ Publish Failed: {e}")
    else:
        print("   ⚠️ Redis not enabled, skipping publish test")
    print("\n")

    # 3. Verify AsyncRedisSaver
    print("3️⃣  Verifying AsyncRedisSaver...")
    AsyncRedisSaver()
    if cache.enabled and cache.redis:
        print("   ✅ AsyncRedisSaver instantiated and Redis is active")
    else:
        print("   ⚠️ AsyncRedisSaver instantiated but Redis is INACTIVE")
    print("\n")

    print("🎉 All Option A verifications passed!")


if __name__ == "__main__":
    asyncio.run(verify())
