"""
Verification Script for Phase 70: Operational Excellence
Checks:
1. RedisCacheService: Connection and Set/Get operation.
2. IRSClient: SSL Context loading (Simulation check if cert missing).
3. IRSMonitorService: RSS Fetching (Network check).
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../packages/afo-core")))

from AFO.services.irs_client import irs_client
from AFO.services.irs_monitor_service import irs_monitor
from AFO.services.redis_cache_service import redis_cache_service


async def verify_redis():
    print("\n[1] Verifying RedisCacheService...")
    connected = await redis_cache_service.initialize()
    if not connected:
        print(
            "⚠️ Redis not connected (Expected in local env without Redis running). Skipping Key Test."
        )
        return

    success = await redis_cache_service.set("phase70_test", "operational_excellence", ttl=60)
    print(f"Redis Set: {success}")

    val = await redis_cache_service.get("phase70_test")
    print(f"Redis Get: {val}")

    if val == "operational_excellence":
        print("✅ Redis Verification Passed")
    else:
        print("❌ Redis Verification Failed")


async def verify_irs_client():
    print("\n[2] Verifying IRSClient...")
    print(f"Cert Path: {irs_client.cert_path}")
    print(f"Simulation Mode: {irs_client.simulation_mode}")

    if irs_client.simulation_mode:
        print("✅ IRS Client correctly fell back to Simulation Mode (Cert missing)")
    else:
        if irs_client.ssl_context:
            print("✅ IRS Client Loaded SSL Context")
        else:
            print("❌ IRS Client Failed to Load SSL Context in Real Mode")


async def verify_irs_monitor():
    print("\n[3] Verifying IRSMonitorService...")
    # Force real mode for a single fetch test
    irs_monitor.mock_mode = False
    try:
        changes = await irs_monitor._fetch_real_rss_updates()
        print(f"Fetched {len(changes)} RSS items")
        if changes:
            print(f"Sample: {changes[0].metadata.title}")
            print("✅ IRS Monitor RSS Fetch Verified")
        else:
            print("⚠️ Parsed 0 items (Check Network or XML structure)")
    except Exception as e:
        print(f"❌ IRS Monitor Failed: {e}")


async def main():
    print("=== Phase 70 Verification ===")
    await verify_redis()
    await verify_irs_client()
    await verify_irs_monitor()
    print("\n=== Verification Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
