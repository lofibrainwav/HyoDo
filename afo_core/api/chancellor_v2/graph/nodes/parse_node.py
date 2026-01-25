from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from AFO.api.chancellor_v2.graph.state import GraphState

"""PARSE Node - Command parsing and execution planning."""


async def parse_node(state: GraphState) -> GraphState:
    """Parse command into structured plan.
    te execution plan.

        Args:
            state: Current graph state

        Returns:
            Updated graph state with execution plan
    """
    command = state.plan.get("command", "")

    # Basic parsing - extract skill_id and parameters
    # This is a simplified implementation
    if "skill_id" in state.input:
        skill_id = state.input["skill_id"]
        parameters = state.input.get("parameters", {})
    else:
        # Fallback parsing - assume first word is command
        parts = command.split()
        if parts:
            skill_id = f"skill_{parts[0].lower()}"
            parameters = {"args": parts[1:]}
        else:
            state.errors.append("Cannot parse command")
            return state

    # Update plan with parsed information
    state.plan = {
        **state.plan,
        "skill_id": skill_id,
        "parameters": parameters,
        "timeout": 30,  # Default timeout
    }

    return state
