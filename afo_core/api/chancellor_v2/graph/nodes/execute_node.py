from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from AFO.api.guards.skills_allowlist_guard import is_skill_allowed
from AFO.api.routers.skills import registry

if TYPE_CHECKING:
    from AFO.api.chancellor_v2.graph.state import GraphState

"""Chancellor Graph V2 - EXECUTE Node.

Connects V2 graph to existing skill execution with Stage 2 guard enforcement.
"""


logger = logging.getLogger(__name__)


async def execute_node(state: GraphState) -> GraphState:
    """Execute planned skills with Stage 2 Allowlist enforcement.

    Reads skill_id from state.plan and executes via existing runtime.
    Writes result to state.outputs["EXECUTE"].

    Security: All skill invocations pass through Stage 2 Allowlist guard.
    """
    skill_id = state.plan.get("skill_id")

    if not skill_id:
        state.outputs["EXECUTE"] = {"status": "skip", "reason": "no skill_id in plan"}
        return state

    # Stage 2 Allowlist Enforcement (SSOT: PH21-S2)
    allowed, reason = is_skill_allowed(skill_id)
    if not allowed:
        state.errors.append(f"EXECUTE blocked: {reason}")
        state.outputs["EXECUTE"] = {"status": "blocked", "reason": reason}
        return state

    # Execute via existing runtime
    try:
        # Import here to avoid circular dependency

        result = await registry.execute_skill(
            skill_id=skill_id,
            parameters=state.plan.get("parameters", {}),
            timeout_seconds=state.plan.get("timeout", 30),
        )

        state.outputs["EXECUTE"] = {
            "status": "success",
            "skill_id": skill_id,
            "result": result,
        }
        logger.info(f"[V2 EXECUTE] Skill {skill_id} executed successfully")

    except Exception as e:
        state.errors.append(f"EXECUTE failed: {type(e).__name__}: {e}")
        state.outputs["EXECUTE"] = {
            "status": "error",
            "skill_id": skill_id,
            "error": str(e),
        }
        logger.exception(f"[V2 EXECUTE] Skill {skill_id} failed")

    return state

    return state
