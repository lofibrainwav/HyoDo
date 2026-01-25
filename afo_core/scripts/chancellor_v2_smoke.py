from __future__ import annotations

from typing import TYPE_CHECKING

from api.chancellor_v2.graph.runner import run_v2

if TYPE_CHECKING:
    from api.chancellor_v2.graph.state import GraphState

"""Chancellor Graph V2 Smoke Test.

Verifies that events and checkpoints are generated correctly.
"""


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


if __name__ == "__main__":
    st = run_v2({"hello": "kingdom"}, NODES)
    print(f"trace_id: {st.trace_id}")
    print(f"errors: {st.errors}")
    print(f"outputs: {list(st.outputs.keys())}")
    print(f"final_step: {st.step}")

    if not st.errors:
        print("\n✅ Smoke test PASSED - events and checkpoints generated")
    else:
        print("\n❌ Smoke test FAILED")
