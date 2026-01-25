from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from AFO.api.chancellor_v2.graph.state import GraphState

"""CMD Node - Command reception and initial validation."""


async def cmd_node(state: GraphState) -> GraphState:
    """Read command from input and initialize state.
    lidation.

        Args:
            state: Current graph state

        Returns:
            Updated graph state
    """
    # Basic command validation
    if not state.input or not isinstance(state.input, dict):
        state.errors.append("Invalid command format")
        return state

    command = state.input.get("command", "")
    if not command or not isinstance(command, str):
        state.errors.append("Missing or invalid command")
        return state

    # Store command in plan for later nodes
    state.plan = {
        **state.plan,
        "command": command,
        "received_at": state.started_at,
    }

    return state
