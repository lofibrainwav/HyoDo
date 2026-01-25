import asyncio
import os
import sys

# Add package root to path

# Ensure absolute path to package root
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

# Mock imports BEFORE importing socrates_node to prevent import errors from other modules
# from unittest.mock import MagicMock
# sys.modules["AFO.chancellor_graph"] = MagicMock()
# sys.modules["AFO.trinity_metric_wrapper"] = MagicMock()
# sys.modules["AFO.api.chancellor_v2.graph.nodes.validation_node"] = MagicMock()

from AFO.api.chancellor_v2.graph.nodes.socrates_node import socrates_node


# Mock GraphState
class MockState:
    def __init__(self, command, plan) -> None:
        self.input = {"command": command}
        self.plan = plan
        self.outputs = {}
        self.errors = []


async def test_socrates():
    print("Testing Socrates Node...")

    # CASE 1: Simple task (Should skip)
    print("\n[Case 1] Simple Task")
    state1 = MockState("hello", ["step1"])
    await socrates_node(state1)
    print(f"Output: {state1.outputs.get('SOCRATES')}")

    # CASE 2: Complex task (Should run)
    print("\n[Case 2] Complex Task")
    state2 = MockState(
        "Deploy the entire kingdom to Mars",
        ["Build Rocket", "Fuel Rocket", "Launch", "Land", "Colonize"],
    )
    # Mocking llm_router would be needed for real output,
    # but initially we just want to see it doesn't crash and attempts execution.
    # Since we can't easily mock async generic modules in this script without dependencies,
    # we expect it to likely fail on llm_router import or execution if environment isn't perfect.
    # However, if it reaches the LLM call, the logic is valid.

    # CASE 3: Socratic Kingdom Audit
    print("\n[Case 3] Socratic Debate: Collaboration Hub Architecture (TICKET-107)")
    state3 = MockState(
        "Build a centralized Collaboration Hub to manage state sessions between multiple agents (Truth, Goodness, Beauty).",
        [
            "Define Session Schema",
            "Implement Redis Locking",
            "Create Event Bus",
            "Integrate with Graph",
        ],
    )

    try:
        # Check if we can run it. If it fails due to creds, we will simulate the output.
        await socrates_node(state3)
        print(f"Output: {state3.outputs.get('SOCRATES')}")
    except Exception as e:
        print(f"Execution Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_socrates())
