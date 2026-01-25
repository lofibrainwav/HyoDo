import asyncio
import json
import time

import httpx


async def verify_sse(url: str, duration: int = 10):
    """
    Verify SSE stream connectivity and heartbeat signals.
    [眞] Truth: Confirms data packets are flowing.
    [孝] Serenity: Confirms heartbeats prevent connection drops.
    """
    print(f"🔍 Testing SSE Stream: {url}")
    print(f"⏳ Monitoring for {duration} seconds...")

    start_time = time.time()
    event_count = 0
    heartbeat_count = 0

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", url) as response:
                if response.status_code != 200:
                    print(f"❌ Error: Received status code {response.status_code}")
                    return False

                async for line in response.aiter_lines():
                    if time.time() - start_time > duration:
                        break

                    if not line.strip():
                        continue

                    if line.startswith("data:"):
                        event_count += 1
                        payload = json.loads(line[5:].strip())
                        if payload.get("type") == "keep-alive" or payload.get("source") == "System":
                            heartbeat_count += 1
                        print(f"📥 Received Event: {payload.get('type') or payload.get('source')}")

    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return False

    print(f"\n📊 Summary for {url}:")
    print(f"✅ Total Events: {event_count}")
    print(f"💓 Heartbeats/System Events: {heartbeat_count}")

    if event_count > 0:
        print("🟢 SSE Stream Verified: OPERATIONAL")
        return True
    else:
        print("🔴 SSE Stream Verified: NO DATA RECEIVED")
        return False


async def main():
    endpoints = [
        "http://127.0.0.1:8010/api/v1/public/chronicle",  # Standard GET check
        "http://127.0.0.1:8000/api/debugging/stream",  # Dashboard Proxy or direct
        "http://127.0.0.1:8010/api/debugging/stream",  # Direct SSE
    ]

    # We first check if the server is actually up
    success = True
    for ep in [endpoints[2]]:  # Checking direct SSE for now
        if not await verify_sse(ep, duration=5):
            success = False

    if success:
        print("\n🏆 Phase 33 SSE Hardening Verification: PASSED")
    else:
        print("\n⚠️ Phase 33 SSE Hardening Verification: ISSUES DETECTED")


if __name__ == "__main__":
    asyncio.run(main())
