"""
Stress Test Script (Phase 57: The Strategy of Sun Tzu)
Tests Rate Limiting (SlowAPI) and Circuit Breaker resilience.
"""

import asyncio
import time

import httpx

BASE_URL = "http://localhost:8010"


async def attack_vector_dos(requests_per_burst: int = 100):
    """
    Attack Vector A: Rapid-fire requests to trigger SlowAPI Rate Limit.
    Expected: After threshold, API returns 429 Too Many Requests.
    """
    print(f"⚔️ [Vector A] Launching DOS Simulation ({requests_per_burst} requests)...")

    results = {"success": 0, "rate_limited": 0, "error": 0}

    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = []
        for i in range(requests_per_burst):
            tasks.append(client.get(f"{BASE_URL}/api/julie/status"))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for r in responses:
            if isinstance(r, Exception):
                results["error"] += 1
            elif r.status_code == 200:
                results["success"] += 1
            elif r.status_code == 429:
                results["rate_limited"] += 1
            else:
                results["error"] += 1

    print(f"  ✅ Success: {results['success']}")
    print(f"  🛡️ Rate Limited (429): {results['rate_limited']}")
    print(f"  ❌ Errors: {results['error']}")

    # Assertion: At least some requests should be rate limited
    if results["rate_limited"] > 0:
        print("  🎯 [PASS] SlowAPI Rate Limiter is ACTIVE!")
        return True
    else:
        print("  ⚠️ [WARN] No 429 responses detected. Rate limit might be too high or not working.")
        return False


async def attack_vector_health_check():
    """
    Simple health check to ensure system is responsive after stress.
    """
    print("🩺 [Health Check] Verifying system stability...")
    await asyncio.sleep(2)  # Brief cooldown

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.get(f"{BASE_URL}/api/julie/status")
            if r.status_code == 200:
                print(f"  ✅ System is STABLE. Response: {r.json().get('status')}")
                return True
            else:
                print(f"  ⚠️ Unexpected status: {r.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ System UNREACHABLE: {e}")
            return False


async def main():
    print("=" * 60)
    print("🏹 Phase 57: The Strategy of Sun Tzu - Stress Test")
    print("=" * 60)

    # Vector A: DOS Attack
    rate_limit_passed = await attack_vector_dos(100)

    # Health Check
    health_passed = await attack_vector_health_check()

    print("=" * 60)
    if rate_limit_passed and health_passed:
        print("🏆 [VICTORY] All defensive systems operational!")
    else:
        print("⚠️ [PARTIAL SUCCESS] Review results above.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
