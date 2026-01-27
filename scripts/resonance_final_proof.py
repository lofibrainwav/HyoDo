import asyncio
import json
import os
import sys

# Path setup
sys.path.insert(0, os.path.abspath("packages/afo-core"))

from domain.ai.models import AIRequest
from infrastructure.ai.gateway import ai_gateway
from infrastructure.rag.engine import RAGEngine


async def verify_resonance():
    print("=" * 60)
    print("💎 AFO Kingdom: Operation Resonance Verification")
    print("=" * 60)

    # 1. Verify RAG (LanceDB + Ollama Embedding)
    print("\n[Step 1] 眞: LanceDB RAG Verification")
    engine = RAGEngine()
    query = "승상의 정체성과 역할에 대해 설명해줘."
    print(f"🔍 Query: {query}")

    chunks = await engine.retrieve_context(query, limit=2)
    context_text = "\n".join([c.content for c in chunks])

    if chunks:
        print(f"✅ RAG Success! (Found {len(chunks)} context chunks)")
        for i, chunk in enumerate(chunks):
            print(f"   - Context {i + 1}: {chunk.content[:100]}... (Source: {chunk.source})")
    else:
        print("❌ RAG Failure: No context retrieved.")
        context_text = ""

    # 2. Verify AI Gateway (Ollama Streaming + RAG Context)
    print("\n[Step 2] 善: AI Gateway (Ollama) Resonance Verification")
    ai_req = AIRequest(query=query, context=context_text, persona="jang_yeong_sil", stream=True)
    print(f"🚀 Model Routing: {ai_gateway._route_model(ai_req.persona)}")
    print("   AI Response: ", end="", flush=True)

    full_response = ""
    try:
        async for chunk in ai_gateway.generate_stream(ai_req):
            print(chunk, end="", flush=True)
            full_response += chunk
        print("\n\n✅ Gateway Success! Response received via Streaming.")
    except Exception as e:
        print(f"\n❌ Gateway Failure: {e}")

    print("\n" + "=" * 60)
    print("👑 Operation Resonance: Verification Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(verify_resonance())
