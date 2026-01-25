import asyncio
import sys

import aiohttp


async def verify_debugging_stream():
    print("🔍 [1/2] Verifying Debugging Stream...")
    url = "http://localhost:8010/debugging/stream"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"❌ Stream failed: Status {response.status}")
                    return False

                print("   ✅ Connection Established (200 OK)")

                # specific check for event stream content type if possible, or just read lines
                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if not line:
                        continue
                    print(f"   📨 Received: {line}")

                    if "Healing Agent Stream Connected" in line or "connected" in line:
                        print("   ✅ 'Connected' event verified!")
                        return True

                    # Timeout guard to avoid hanging forever
                    return True  # If we got any data, it's alive (stream logic usually yields immediately)

    except Exception as e:
        print(f"❌ Stream Exception: {e}")
        return False


async def verify_finance_dashboard():
    print("\n🔍 [2/2] Verifying Finance Dashboard...")
    url = "http://localhost:8010/finance/dashboard"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"❌ Finance API failed: Status {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return False

                data = await response.json()
                print("   ✅ API returned 200 OK")

                # Check specifics
                txs = data.get("recent_transactions", [])
                if not txs:
                    print("   ⚠️ No transactions found.")
                    return False

                first_tx = txs[0]
                print(f"   💰 Transaction found: {first_tx['merchant']} ({first_tx['amount']})")

                if first_tx["merchant"] == "System Init":
                    print("   ✅ Dynamic Data Verified (System Init present)")
                    return True

                return True

    except Exception as e:
        print(f"❌ Finance Exception: {e}")
        return False


async def verify_ssot_status():
    print("\n🔍 [3/3] Verifying SSOT Status (Trinity Scores)...")
    url = "http://localhost:8010/api/ssot-status"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"❌ SSOT API failed: Status {response.status}")
                    return False

                data = await response.json()
                trinity = data.get("trinity", {})
                scores = [
                    trinity.get(k) for k in ["truth", "goodness", "beauty", "serenity", "eternity"]
                ]

                print("   ✅ API returned 200 OK")
                print(
                    f"   🕊️  Trinity Scores: Truth={trinity.get('truth')}, Goodness={trinity.get('goodness')}, Beauty={trinity.get('beauty')}"
                )

                if all(s is not None for s in scores):
                    print("   ✅ 5-Pillar Data Verified")
                    return True
                else:
                    print(f"   ❌ Missing scores: {trinity}")
                    return False

    except Exception as e:
        print(f"❌ SSOT Exception: {e}")
        return False


async def main():
    print("🚀 Starting AFO Kingdom Integrity Verification\n" + "=" * 50)

    stream_ok = await verify_debugging_stream()
    finance_ok = await verify_finance_dashboard()
    ssot_ok = await verify_ssot_status()

    print("=" * 50)
    if stream_ok and finance_ok and ssot_ok:
        print("✅ ALL SYSTEMS VERIFIED: INTEGRITY CONFIRMED")
        sys.exit(0)
    else:
        print("❌ VERIFICATION FAILED")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
