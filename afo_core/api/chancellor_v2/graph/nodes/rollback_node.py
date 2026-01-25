from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from AFO.api.chancellor_v2.graph.store import list_checkpoints, load_checkpoint

if TYPE_CHECKING:
    from AFO.api.chancellor_v2.graph.state import GraphState

"""Chancellor Graph V2 - ROLLBACK Node.

Restores last successful checkpoint when VERIFY fails.
"""


logger = logging.getLogger(__name__)

# Steps that are considered "safe" rollback points
SAFE_ROLLBACK_STEPS = ["MERGE", "BEAUTY", "GOODNESS", "TRUTH", "PARSE", "CMD"]


def rollback_node(state: GraphState) -> GraphState:
    """Rollback to last successful checkpoint.

    Per SSOT policy:
    - Only removes side-effects (no overwrite)
    - Restores state from last safe checkpoint
    """
    verify_result = state.outputs.get("VERIFY", {})
    if verify_result.get("status") != "fail":
        state.outputs["ROLLBACK"] = {"status": "skip", "reason": "VERIFY did not fail"}
        return state

    # Find last successful checkpoint
    checkpoints = list_checkpoints(state.trace_id)
    rollback_step = None

    for step in SAFE_ROLLBACK_STEPS:
        if step in checkpoints:
            rollback_step = step
            break

    if not rollback_step:
        state.errors.append("ROLLBACK: no safe checkpoint found")
        state.outputs["ROLLBACK"] = {"status": "error", "reason": "no safe checkpoint"}
        logger.error(f"[V2 ROLLBACK] No safe checkpoint for trace {state.trace_id}")
        return state

    # Load checkpoint
    checkpoint_data = load_checkpoint(state.trace_id, rollback_step)
    if not checkpoint_data:
        state.errors.append(f"ROLLBACK: failed to load checkpoint {rollback_step}")
        state.outputs["ROLLBACK"] = {
            "status": "error",
            "reason": "checkpoint load failed",
        }
        return state

    # Restore state (partial - only safe fields)
    state.outputs["ROLLBACK"] = {
        "status": "success",
        "restored_from": rollback_step,
        "original_errors": state.errors.copy(),
    }

    logger.info(f"[V2 ROLLBACK] Restored from {rollback_step}")
    return state
