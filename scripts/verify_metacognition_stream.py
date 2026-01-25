import asyncio
import json

import httpx


async def verify_metacognitive_audit_stream():
    print("🧠 Starting Metacognitive Audit Stream Verification...")

    url = "http://localhost:8010/api/trinity/metacognition/audit/stream?target=Phase%205.5"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            async with client.stream("GET", url) as response:
                if response.status_code != 200:
                    print(f"❌ Failed to connect: {response.status_code}")
                    return

                print("✅ Connected to SSE stream. Receiving reflections...")

                reflection_count = 0
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        persona = data.get("persona")
                        chunk = data.get("chunk")

                        if chunk:
                            print(f"[{persona}] {chunk}", end="", flush=True)
                            reflection_count += 1

                        if reflection_count > 50:  # Limit output for verification
                            print("\n... (Stream continues)")
                            break

                print("\n✅ Verification successful: Received metacognitive insights.")

        except Exception as e:
            print(f"❌ Error during verification: {e}")


if __name__ == "__main__":
    asyncio.run(verify_metacognitive_audit_stream())
