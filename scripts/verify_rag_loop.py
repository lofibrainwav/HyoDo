import asyncio
import os
import pathlib
import sys

# Add project root to path
sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
)

from AFO.api.routers.rag_query import RAGQueryRequest, query_kingdom_memory


async def verify_rag_loop():
    print("=== 🧠 Phase 12: Eternal Memory Verification ===")

    # Test Query 1
    q1 = "Phase 11의 Custom BERT 정확도는?"
    print(f"\n[Test 1] Assessing: '{q1}'")

    req1 = RAGQueryRequest(question=q1)
    res1 = await query_kingdom_memory(req1)

    print(f"✅ Answer: {res1.get('answer')}")
    print(f"📚 Sources: {res1.get('sources')}")

    # Assertions
    if "98.25%" in res1.get("answer"):
        print("   -> Accuracy verified via RAG.")
    else:
        print("   ❌ Failed to retrieve correct info.")
        sys.exit(1)

    # Test Query 2
    q2 = "What is Phase 10?"
    print(f"\n[Test 2] Assessing: '{q2}'")

    req2 = RAGQueryRequest(question=q2)
    res2 = await query_kingdom_memory(req2)

    print(f"✅ Answer: {res2.get('answer')}")
    print(f"📚 Sources: {res2.get('sources')}")

    if "Matrix Stream" in res2.get("answer"):
        print("   -> Phase 10 context verified.")
    else:
        print("   ❌ Failed to retrieve Phase 10 info.")
        sys.exit(1)

    print("\n🎉 Phase 12 LangChain RAG Loop Verified Successfully.")


if __name__ == "__main__":
    asyncio.run(verify_rag_loop())
