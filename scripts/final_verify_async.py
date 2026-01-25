import asyncio

import aiohttp


async def main():
    async with aiohttp.ClientSession() as session:
        print("Connecting to stream...")
        async with session.get("http://127.0.0.1:3000/api/debugging/stream") as resp:
            print(f"Status: {resp.status}")

            # Start emitter task
            async def emit():
                await asyncio.sleep(2)
                print("Emitting event...")
                async with session.post(
                    "http://127.0.0.1:8010/api/debugging/emit",
                    json={"message": "FOUND_SENTINEL"},
                ) as emit_resp:
                    print(f"Emit status: {emit_resp.status}")

            asyncio.create_task(emit())

            print("Listening for sentinel...")
            async for line in resp.content:
                if line:
                    decoded = line.decode()
                    print(f"DATA: {decoded.strip()}")
                    if "FOUND_SENTINEL" in decoded:
                        print("✅ SENTINEL RECEIVED!")
                        return


try:
    asyncio.run(asyncio.wait_for(main(), timeout=10))
except asyncio.TimeoutError:
    print("❌ TIMEOUT: Sentinel not received")
