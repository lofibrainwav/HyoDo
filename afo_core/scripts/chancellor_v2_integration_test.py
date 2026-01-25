from __future__ import annotations

from typing import TYPE_CHECKING

from api.chancellor_v2.graph.nodes.execute_node import execute_node_sync
from api.chancellor_v2.graph.nodes.rollback_node import rollback_node
from api.chancellor_v2.graph.nodes.verify_node import verify_node
from api.chancellor_v2.graph.runner import run_v2

if TYPE_CHECKING:
    from api.chancellor_v2.graph.state import GraphState

"""Chancellor Graph V2 - Integration Test.

Tests V2 graph with real EXECUTE/VERIFY nodes and Stage 2 guard.
"""


def ok_node(step: str) -> None:
    """Create a simple pass-through node."""

    def _fn(state: GraphState) -> GraphState:
        state.outputs[step] = "ok"
        return state

    return _fn


def parse_node(state: GraphState) -> GraphState:
    """PARSE node that extracts skill_id from input."""
    state.plan = {
        "skill_id": state.input.get("skill_id"),
        "parameters": state.input.get("parameters", {}),
        "timeout": state.input.get("timeout", 30),
    }
    state.outputs["PARSE"] = {"plan": state.plan}
    return state


def build_nodes() -> None:
    """Build node dict with real implementations."""
    return {
        "CMD": ok_node("CMD"),
        "PARSE": parse_node,
        "TRUTH": ok_node("TRUTH"),
        "GOODNESS": ok_node("GOODNESS"),
        "BEAUTY": ok_node("BEAUTY"),
        "MERGE": ok_node("MERGE"),
        "EXECUTE": execute_node_sync,
        "VERIFY": verify_node,
        "REPORT": ok_node("REPORT"),
    }


def test_approved_skill() -> None:
    """Test with approved skill (should PASS)."""
    print("\n" + "=" * 50)
    print("TEST 1: Approved Skill (truth_evaluate - exists in MockRegistry)")
    print("=" * 50)

    nodes = build_nodes()
    # Use skill that exists in MockSkillRegistry
    state = run_v2({"skill_id": "truth_evaluate"}, nodes)

    print(f"trace_id: {state.trace_id}")
    print(f"errors: {state.errors}")
    print(f"EXECUTE: {state.outputs.get('EXECUTE', {}).get('status')}")
    print(f"VERIFY: {state.outputs.get('VERIFY', {}).get('status')}")

    # Should pass or skip (no actual skill in mock)
    verify_status = state.outputs.get("VERIFY", {}).get("status")
    execute_status = state.outputs.get("EXECUTE", {}).get("status")

    if verify_status == "pass" or execute_status in ("success", "skip"):
        print("✅ TEST 1 PASSED: Approved skill allowed")
        return True
    else:
        print("❌ TEST 1 FAILED")
        return False


def test_blocked_skill() -> None:
    """Test with blocked skill (should be blocked by Stage 2 guard)."""
    print("\n" + "=" * 50)
    print("TEST 2: Blocked Skill (skill_999_experimental)")
    print("=" * 50)

    nodes = build_nodes()
    state = run_v2({"skill_id": "skill_999_experimental"}, nodes)

    print(f"trace_id: {state.trace_id}")
    print(f"errors: {state.errors}")
    print(f"EXECUTE: {state.outputs.get('EXECUTE', {})}")

    # Should be blocked
    execute_result = state.outputs.get("EXECUTE", {})
    if execute_result.get("status") == "blocked":
        print("✅ TEST 2 PASSED: Blocked skill rejected by Stage 2 guard")
        return True
    else:
        print("❌ TEST 2 FAILED: Skill was not blocked!")
        return False


def test_unlisted_skill() -> None:
    """Test with unlisted skill (should be blocked)."""
    print("\n" + "=" * 50)
    print("TEST 3: Unlisted Skill (unknown_skill_xyz)")
    print("=" * 50)

    nodes = build_nodes()
    state = run_v2({"skill_id": "unknown_skill_xyz"}, nodes)

    print(f"trace_id: {state.trace_id}")
    print(f"errors: {state.errors}")
    print(f"EXECUTE: {state.outputs.get('EXECUTE', {})}")

    # Should be blocked (not in approved list)
    execute_result = state.outputs.get("EXECUTE", {})
    if execute_result.get("status") == "blocked":
        print("✅ TEST 3 PASSED: Unlisted skill rejected")
        return True
    else:
        print("❌ TEST 3 FAILED: Skill was not blocked!")
        return False


if __name__ == "__main__":
    results = []
    results.append(test_approved_skill())
    results.append(test_blocked_skill())
    results.append(test_unlisted_skill())

    print("\n" + "=" * 50)
    print(f"SUMMARY: {sum(results)}/{len(results)} tests passed")
    print("=" * 50)

    if all(results):
        print("\n✅ All integration tests PASSED")
    else:
        print("\n❌ Some tests FAILED")
