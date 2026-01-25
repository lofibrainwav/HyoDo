import asyncio
import os
import sys

# Path setup to include packages
sys.path.insert(0, os.path.abspath("packages/afo-core"))

from domain.ai.models import AIRequest
from infrastructure.ai.gateway import ai_gateway


async def test_gateway_real():
    query = "Why is it important to have a technical debt audit in a kingdom system?"
    req = AIRequest(query=query, persona="developer", stream=True)

    print("🚀 Sending request to AI Gateway (Model: DeepSeek-R1?)...")
    print(f"Query: {query}\n")

    print("--- RESPONSE ---")
    async for chunk in ai_gateway.generate_stream(req):
        print(chunk, end="", flush=True)
    print("\n----------------")


if __name__ == "__main__":
    asyncio.run(test_gateway_real())
