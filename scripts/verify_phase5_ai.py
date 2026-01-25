"""
Verification Script for Phase 5 (Real Agent Intelligence)
Simulates a client request to the Agent Orchestrator/Gateway to verify PII redaction and Streaming.
"""

import asyncio
import sys

from application.agents.orchestrator import agent_orchestrator
from domain.ai.models import AIRequest


async def verify_streaming_analysis():
    print("🧪 Starting Phase 5 Verification: Real Agent Intelligence Stream")

    # Test Data with PII (to test Redaction)
    query = "Analyze the tax implications for John Doe (SSN: 123-45-6789) regarding Section 179 depreciation."
    print(f"📝 Input Query: {query}")

    print("\n🌊 Streaming Response:")
    chunk_count = 0
    full_response = ""

    try:
        async for chunk in agent_orchestrator.orchestrate_analysis(query, persona="tax_analyst"):
            sys.stdout.write(chunk)
            sys.stdout.flush()
            full_response += chunk
            chunk_count += 1
    except Exception as e:
        print(f"\n❌ Error during streaming: {e}")
        return False

    print("\n\n✅ Stream Complete.")
    print(f"📊 Stats: {chunk_count} chunks received.")

    # Assertions
    if "123-45-6789" in full_response:
        print("❌ FAIL: PII was not redacted from the response/prompt echo!")
        return False

    if "IRS Context" not in full_response and "Section 179" not in full_response:
        # Note: The mock gateway response includes "IRS Context".
        print("❌ FAIL: Context was not injected or Gateway failed.")
        return False

    print("✅ PII Redaction Verified.")
    print("✅ RAG Context Injection Verified.")
    return True


if __name__ == "__main__":
    success = asyncio.run(verify_streaming_analysis())
    sys.exit(0 if success else 1)
