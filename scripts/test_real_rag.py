import asyncio
import logging
import os
import sys

# Path setup to include packages
sys.path.insert(0, os.path.abspath("packages/afo-core"))

from infrastructure.rag.engine import RAGEngine


async def test_rag_real():
    logging.basicConfig(level=logging.INFO)
    engine = RAGEngine()

    query = "왕국에서 사령관은 어떻게 불러야 해?"
    print(f"🔍 Searching for: {query}")

    chunks = await engine.retrieve_context(query, limit=2)

    if not chunks:
        print("❌ No context retrieved.")
        return

    print(f"✅ Retrieved {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"\n[{i + 1}] Source: {chunk.source} (Score: {chunk.score:.4f})")
        print(f"Content: {chunk.content[:200]}...")


if __name__ == "__main__":
    asyncio.run(test_rag_real())
