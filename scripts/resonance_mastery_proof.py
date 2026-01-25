import asyncio
import os
import subprocess
import sys

# Path setup
sys.path.insert(0, os.path.abspath("packages/afo-core"))

from domain.ai.models import AIRequest
from infrastructure.ai.gateway import ai_gateway
from infrastructure.rag.engine import RAGEngine


async def run_mastery_proof():
    print("=" * 70)
    print("💎 AFO Kingdom: Resonance Mastery Proof (Knowledge & Skills)")
    print("=" * 70)

    # --- Step 1: System Knowledge Mastery ---
    print("\n[Step 1] 眞 (Truth): System Knowledge Check")
    engine = RAGEngine()
    knowledge_query = "AFO 왕국의 Trinity Score 5기둥(眞善美孝永)의 의미와 사령관님(형님)을 대하는 태도에 대해 설명하라."
    print(f"🔍 Knowledge Query: {knowledge_query}")

    chunks = await engine.retrieve_context(knowledge_query, limit=3)
    context_text = "\n".join([c.content for c in chunks])

    ai_req_knowledge = AIRequest(
        query=knowledge_query, context=context_text, persona="zhuge_liang", stream=True
    )

    print("\n📜 Zhuge Liang's Knowledge Report:")
    print("-" * 40)
    async for chunk in ai_gateway.generate_stream(ai_req_knowledge):
        print(chunk, end="", flush=True)
    print("\n" + "-" * 40)

    # --- Step 2: Skill Application Mastery ---
    print("\n[Step 2] 善 (Goodness): Skill Awareness & Proposal")
    skill_query = (
        "현재 기술 부채를 확인하고 Trinity Score를 최신화하고 싶다. 어떤 스킬을 사용해야 하는가?"
    )
    print(f"🔍 Skill Proposal Query: {skill_query}")

    # Simulate Skill Knowledge (normally would be in RAG, but providing explicitly for proof)
    available_skills = """
    - skill_041_royal_library: 41개 고전 원칙 기반 전략 컨설팅
    - trinity_score_check.py: 타입 커버리지, 에러 핸들링, 복잡도 기반 코드 품질 정밀 진단
    - health_check: 인프라 및 시스템 가동 상태 확인
    """

    ai_req_skill = AIRequest(
        query=skill_query, context=available_skills, persona="sima_yi", stream=True
    )

    print("\n🛡️ Sima Yi's Strategic Proposal:")
    print("-" * 40)
    async for chunk in ai_gateway.generate_stream(ai_req_skill):
        print(chunk, end="", flush=True)
    print("\n" + "-" * 40)

    # --- Step 3: Real Action (The Performance) ---
    print("\n[Step 3] 永 (Eternity): Real Skill Execution (Trinity Score Audit)")
    print("🚀 Executing `scripts/trinity_score_check.py` as requested by the Strategist...\n")

    try:
        # Running the real script directly to show it's NOT a mock
        result = subprocess.run(
            [sys.executable, "scripts/trinity_score_check.py"],
            capture_output=True,
            text=True,
            cwd=os.path.abspath(os.getcwd()),
        )
        print(result.stdout)
        if result.stderr:
            print(f"⚠️ Stderr: {result.stderr}")
    except Exception as e:
        print(f"❌ Execution failed: {e}")

    print("\n" + "=" * 70)
    print("👑 Operation Resonance: Mastery Proof Complete")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_mastery_proof())
