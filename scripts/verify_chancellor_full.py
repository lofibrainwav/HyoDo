import asyncio
import os
import pathlib
import sys

# 프로젝트 루트 경로 추가
sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
)

# from AFO.chancellor_graph import calculate_complexity, chancellor_graph
from AFO.chancellor_graph import chancellor_graph
from langchain_core.messages import HumanMessage


async def verify_chancellor_full():
    print("=== Chancellor Graph Full Deployment Verification ===")

    # 1. Verify Complexity Logic (SKIPPED - Deprecated)
    print("\n[Test 1] Complexity Calculation Logic (Skipped)")
    high_query = "Please analyze the entire architecture of the system and compare it with 3 other strategies to solve the latency issue."

    # 2. Verify Graph Execution (DRY RUN)
    print("\n[Test 2] Graph Execution Flow (ToT)")

    initial_state = {
        "messages": [HumanMessage(content=high_query)],
        "trinity_score": 95.0,
        "risk_score": 5.0,
        "kingdom_context": {"antigravity": {"DRY_RUN_DEFAULT": True}},
    }

    print(">>> Invoking Chancellor Graph...")
    try:
        # We use ainvoke for async execution with Thread ID for MemorySaver
        config = {"configurable": {"thread_id": "verify_test"}}
        final_state = await chancellor_graph.ainvoke(initial_state, config=config)

        print("\n--- Execution Trace ---")
        history = final_state.get("analysis_results", {})
        steps = final_state.get("steps_taken", 0)
        complexity = final_state.get("complexity", "Unknown")

        print(f"Steps Taken: {steps}")
        print(f"Detected Complexity: {complexity}")
        print(f"Strategists Consulted: {list(history.keys())}")

        # Validation
        if complexity == "High" and "jegalryang" in history and "samaui" in history:
            print("✅ ToT Logic Verified (High Complexity triggered multiple strategists)")
        else:
            print("⚠️  ToT Logic Partial or Failed (Check trace)")

        # Check Final Response
        last_msg = final_state["messages"][-1]
        print(f"Final Speaker: {last_msg.name}")
        # print(f"Final Content: {last_msg.content[:100]}...")

    except Exception as e:
        print(f"❌ Execution Failed: {e}")


if __name__ == "__main__":
    asyncio.run(verify_chancellor_full())
