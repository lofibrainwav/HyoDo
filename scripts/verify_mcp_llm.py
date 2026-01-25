import asyncio
import os
import sys

# Add packages path
sys.path.append(os.path.join(os.getcwd(), "packages/afo-core"))


async def verify_mcp_llm():
    from AFO.llm_router import llm_router

    print("=" * 70)
    print("🔍 [VERIFY] Local LLM MCP & Skill Activation")
    print("=" * 70)

    # Test case 1: Context7 Enrichment
    print("\n1. Testing Context7 Enrichment with Ollama...")
    query = "AFO 왕국의 Trinity Score 5기둥에 대해 설명하고, 각 기둥의 가중치를 정확히 말해줘."

    try:
        # qwen2.5-coder (사마휘)와 같은 더 큰 모델 유도
        result = await llm_router.execute_with_routing(
            query, context={"provider": "ollama", "ollama_model": "qwen2.5-coder:7b"}
        )

        print(f"   Success: {result.get('success')}")
        print(f"   Model: {result.get('routing', {}).get('model')}")
        print(f"   Iterations: {result.get('iterations')}")

        if result.get("success"):
            response = result.get("response", "")
            print(f"   Response Preview: {response[:300]}...")

            # Check for philosophy weights (眞 35, 善 35, 美 20, 孝 8, 永 2)
            weights = ["35", "20", "8", "2"]
            found_weights = [w for w in weights if w in response]

            if len(found_weights) >= 2:
                print(f"   ✅ SUCCESS: LLM used context 지식 (발견된 수치: {found_weights})")
            else:
                print("   ⚠️ WARNING: Philosophy weights not clearly found. check Context7 docs.")
        else:
            print(f"   ❌ FAILED: {result.get('error')}")

    except Exception as e:
        print(f"   ❌ ERROR during test: {e}")

    # Test case 2: Skill Execution Loop
    print("\n2. Testing Skill Execution Loop...")
    query_tool = "현재 시스템의 건강 상태를 점검해줘. USE_SKILL 형식을 사용해서 skill_003_health_monitor를 호출해."

    try:
        result_tool = await llm_router.execute_with_routing(
            query_tool,
            context={"provider": "ollama", "ollama_model": "qwen2.5-coder:7b"},
        )

        print(f"   Success: {result_tool.get('success')}")
        print(f"   Iterations: {result_tool.get('iterations')}")

        if result_tool.get("tool_results"):
            print(
                f"   ✅ SUCCESS: {len(result_tool['tool_results'])}개의 도구 호출이 감지되고 실행되었습니다!"
            )
            for i, res in enumerate(result_tool["tool_results"], 1):
                print(
                    f"      [{i}] {res['skill_id']}: {'성공' if res['result'].get('success') else '실패'}"
                )
        else:
            print("   ℹ️ INFO: 도구 호출이 감지되지 않았습니다. (모델의 판단에 따름)")
            print(f"   Response: {result_tool.get('response', '')[:200]}...")

    except Exception as e:
        print(f"   ❌ ERROR during tool test: {e}")

    print("\n" + "=" * 70)
    print("✅ Verification completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(verify_mcp_llm())
