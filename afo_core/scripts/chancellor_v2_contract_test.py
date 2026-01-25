from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from api.chancellor_v2.graph.runner import run_v2

if TYPE_CHECKING:
    from api.chancellor_v2.graph.state import GraphState

"""Chancellor Graph V2 - Contract Verification Test.

Verifies that MCP Contract is enforced:
1. Sequential Thinking is applied to all steps
2. Context7 is applied to all steps
3. Kingdom DNA is injected at trace start
"""


# Set MCP_REQUIRED=0 for test (allows passthrough mode for CI without MCP server)
os.environ["AFO_MCP_REQUIRED"] = "0"


def ok_node(step: str) -> None:
    """Create a simple pass-through node."""

    def _fn(state: GraphState) -> GraphState:
        state.outputs[step] = "ok"
        return state

    return _fn


def verify_node(state: GraphState) -> GraphState:
    """VERIFY node with pass status."""
    state.outputs["VERIFY"] = {"status": "pass"}
    return state


# Build all nodes
NODES = {
    k: ok_node(k)
    for k in [
        "CMD",
        "PARSE",
        "TRUTH",
        "GOODNESS",
        "BEAUTY",
        "MERGE",
        "EXECUTE",
        "REPORT",
    ]
}
NODES["VERIFY"] = verify_node


def test_contract_enforcement() -> bool:
    """Test that MCP contract is enforced."""
    print("\n" + "=" * 60)
    print("CONTRACT VERIFICATION TEST: Sequential Thinking + Context7")
    print("=" * 60)

    state = run_v2({"test": "contract"}, NODES)

    print(f"trace_id: {state.trace_id}")
    print(f"errors: {state.errors}")

    # Contract verification checks
    checks_passed = 0
    checks_total = 5

    # Check 1: _meta exists and shows enforcement
    meta = state.outputs.get("_meta", {})
    if meta.get("thinking_enforced") and meta.get("context7_enforced"):
        print("✅ CHECK 1: _meta shows contract enforcement")
        checks_passed += 1
    else:
        print(f"❌ CHECK 1: _meta missing or wrong: {meta}")

    # Check 2: Kingdom DNA injected
    context7 = state.outputs.get("context7", {})
    if "KINGDOM_DNA" in context7 and context7["KINGDOM_DNA"].get("injected"):
        print("✅ CHECK 2: Kingdom DNA injected at trace start")
        checks_passed += 1
    else:
        print(f"❌ CHECK 2: Kingdom DNA not found: {context7.keys()}")

    # Check 3: Sequential Thinking applied to all steps
    thinking = state.outputs.get("sequential_thinking", {})
    expected_steps = [
        "CMD",
        "PARSE",
        "TRUTH",
        "GOODNESS",
        "BEAUTY",
        "MERGE",
        "EXECUTE",
        "VERIFY",
        "REPORT",
    ]
    thinking_steps = set(thinking.keys())
    if all(step in thinking_steps for step in expected_steps):
        print(f"✅ CHECK 3: Sequential Thinking applied to all {len(expected_steps)} steps")
        checks_passed += 1
    else:
        missing = set(expected_steps) - thinking_steps
        print(f"❌ CHECK 3: Sequential Thinking missing for: {missing}")

    # Check 4: Context7 applied to all steps (plus KINGDOM_DNA)
    context7_steps = set(context7.keys())
    if all(step in context7_steps for step in expected_steps):
        print(f"✅ CHECK 4: Context7 applied to all {len(expected_steps)} steps")
        checks_passed += 1
    else:
        missing = set(expected_steps) - context7_steps
        print(f"❌ CHECK 4: Context7 missing for: {missing}")

    # Check 5: No errors
    if not state.errors:
        print("✅ CHECK 5: No errors during execution")
        checks_passed += 1
    else:
        print(f"❌ CHECK 5: Errors found: {state.errors}")

    print(f"\n{'=' * 60}")
    print(f"CONTRACT VERIFICATION: {checks_passed}/{checks_total} checks passed")
    print("=" * 60)

    if checks_passed == checks_total:
        print("\n✅ CONTRACT FULLY ENFORCED")
        return True
    else:
        print("\n❌ CONTRACT VIOLATION DETECTED")
        return False


if __name__ == "__main__":
    success = test_contract_enforcement()
    sys.exit(0 if success else 1)
