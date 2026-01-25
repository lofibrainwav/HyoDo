# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Kingdom Chancellor Graph Verification Script
Copyright (c) 2025 AFO Kingdom. All rights reserved.
"""

# mypy: ignore-errors
import asyncio
import sys
from pathlib import Path

# Add AFO root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Validating the Graph Structure Logic with Mocked LLM
from unittest.mock import MagicMock

# Mock the LLM classes before importing the graph to intercept instantiation
sys.modules["langchain_openai"] = MagicMock()
sys.modules["langchain_anthropic"] = MagicMock()


from langchain_core.messages import HumanMessage

from AFO import chancellor_graph


# Mock the LLM Router used by the graph nodes
class MockLLMRouter:
    async def execute_with_routing(self, prompt, context=None):
        return {"response": f"Mock Analysis for: {prompt[:20]}..."}


# Patch the router in the imported module
chancellor_graph.llm_router = MockLLMRouter()


async def run_verification():
    print("🧪 Starting Mock Verification of Chancellor Graph V2...")

    # 2. Define Initial State (V2 Schema)
    initial_state = {
        "messages": [HumanMessage(content="Sire, should we invade Wei?")],
        "trinity_score": 0.5,  # V2: float instead of dict
        "risk_score": 0.0,
        "auto_run_eligible": False,
        "kingdom_context": {},
        "persistent_memory": {},
        "current_speaker": "user",
        "next_step": "chancellor",
        "analysis_results": {},
    }

    # 3. Get the Graph
    app = chancellor_graph.chancellor_graph

    # 4. Invoke the Graph
    print("👑 [Chancellor] Invoking Graph with Mock LLMs...")
    config = {"configurable": {"thread_id": "verify_session_v2_mock"}}

    final_state = await app.ainvoke(initial_state, config=config)

    print("\n✅ Verification Complete!")
    print(f"Final Speaker: {final_state.get('current_speaker')}")

    last_msg = final_state["messages"][-1]
    print(f"Final Message: {last_msg.content}")

    if "Mock Analysis" in last_msg.content or "Decree" in last_msg.content:
        print("✅ Graph Logic Verified: Responses are flowing through.")
    else:
        print("⚠️ Graph Logic Warning: Unexpected final message.")


if __name__ == "__main__":
    asyncio.run(run_verification())
