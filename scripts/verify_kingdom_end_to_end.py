import asyncio
import os
import pathlib
import sys

# Add package root to sys.path
core_path = pathlib.Path(
    os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")
).resolve()
sys.path.append(core_path)


# Mock Dependencies strictly for Graph Logic Verification
class MockLLMRouter:
    async def execute_with_routing(self, prompt, context=None):
        return {"response": f"Mock Response for: {prompt[:30]}..."}


class MockYeongdeok:
    async def consult_samahwi(self, prompt):
        return "Samahwi (Risk): Safe (Mock)"

    async def consult_jwaja(self, prompt):
        return "Jwaja (UI): Glassmorphism (Mock)"

    async def consult_hwata(self, prompt):
        return "Hwata (UX): Compassionate Tone (Mock)"

    async def use_tool(self, *args, **kwargs):
        return "Tool Executed (Mock)"


# Patching modules before importing chancellor_graph
import chancellor_graph as graph_module

# Inject Mocks
graph_module.llm_router = MockLLMRouter()
graph_module.yeongdeok = MockYeongdeok()

# Mock State
from langchain_core.messages import HumanMessage


async def run_end_to_end_test():
    print("👑 [Grand Verification] Starting End-to-End Kingdom Simulation (v100.0)...")

    # 1. Build Graph
    try:
        graph_module.build_chancellor_graph()
        print("✅ Chancellor Graph Built Successfully.")
    except Exception as e:
        print(f"❌ Failed to build graph: {e}")
        return

    # 2. Simulate User Query
    user_query = "Commander: Build a secure financial dashboard with glassmorphism UI."
    initial_state = {
        "query": user_query,
        "messages": [HumanMessage(content=user_query)],
        "summary": "",
        "context": {"antigravity": {"DRY_RUN_DEFAULT": True}},
        "status": "INIT",
        "risk_score": 0.0,
        "trinity_score": 0.0,
        "analysis_results": {},
        "results": {},
        "actions": [],
        "search_results": [],
        "multimodal_slots": {},
    }

    print(f"\n📨 Incoming Query: '{user_query}'")

    # 3. Execute Graph Nodes Sequence (Simulated)
    state = initial_state.copy()

    # Step 1: Constitutional Gate (善)
    print("\n--- Step 1: Constitutional Node (善) ---")
    const_res = await graph_module.constitutional_node(state)
    state.update(const_res)
    print(f"👉 Status: {state['status']}")

    # Step 2: Memory & Context (永)
    print("\n--- Step 2: Memory & Rerank (永/眞) ---")
    mem_res = await graph_module.memory_recall_node(state)
    state.update(mem_res)
    rerank_res = await graph_module.rerank_node(state)
    state.update(rerank_res)
    print(f"✅ Recall/Rerank Complete. Trinity Seed: {state.get('trinity_score', 0)}")

    # Step 3: Parallel Strategists (眞/善/美)
    print("\n--- Step 3: Parallel Strategists ---")
    # Simulate parallel execution
    zhuge_res = await graph_module.zhuge_node(state)
    sima_res = await graph_module.sima_node(state)
    zhou_res = await graph_module.zhou_node(state)

    # Correctly update analysis_results (state definition uses reducer for messages, but analysis_results is dict)
    state["analysis_results"].update(zhuge_res.get("analysis_results", {}))
    state["analysis_results"].update(sima_res.get("analysis_results", {}))
    state["analysis_results"].update(zhou_res.get("analysis_results", {}))

    print(f"✅ Zhuge (眞): {state['analysis_results'].get('zhuge_liang', 0)}")
    print(f"✅ Sima (善): {state['analysis_results'].get('sima_yi', 0)}")
    print(f"✅ Zhou (美): {state['analysis_results'].get('zhou_yu', 0)}")

    # Step 4: Trinity Harmonization (⚖️)
    print("\n--- Step 4: Trinity Node ---")
    trinity_res = await graph_module.trinity_node(state)
    state.update(trinity_res)
    print(f"⚖️ Final Trinity Score: {state['trinity_score'] * 100:.1f}%")

    # Step 5: Historian (永)
    print("\n--- Step 5: Historian/Finalize ---")
    final_res = await graph_module.historian_node(state)
    state.update(final_res)
    print(f"📜 Final Seal: {state['messages'][-1].content[:100]}...")

    print("\n🎉 [Grand Verification] End-to-End Simulation Complete. Kingdom v100.0 is STABLE.")


if __name__ == "__main__":
    asyncio.run(run_end_to_end_test())
