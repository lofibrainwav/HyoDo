import asyncio

import httpx


async def simulate_stream():
    url = "http://127.0.0.1:8010/api/logs/stream"
    print(f"Connecting to {url}...")
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url) as response:
                print(f"Response status: {response.status_code}")
                # Check metrics while stream is open
                metrics_url = "http://127.0.0.1:8010/metrics"
                metrics_resp = await client.get(metrics_url)
                print("--- Metrics Snapshot ---")
                for line in metrics_resp.text.splitlines():
                    if "afo_sse_open_connections" in line:
                        print(line)
                print("------------------------")

                # Consume some events
                count = 0
                async for line in response.aiter_lines():
                    if line:
                        print(f"Received: {line[:50]}...")
                        count += 1
                    if count >= 3:
                        break
        print("Stream closed.")

        # Verify metrics after close
        async with httpx.AsyncClient() as client:
            metrics_resp = await client.get(metrics_url)
            print("--- Final Metrics Snapshot ---")
            for line in metrics_resp.text.splitlines():
                if "afo_sse_open_connections" in line:
                    print(line)
            print("------------------------------")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(simulate_stream())
