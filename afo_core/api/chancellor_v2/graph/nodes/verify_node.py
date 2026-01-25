from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from AFO.api.chancellor_v2.graph.state import GraphState

"""Chancellor Graph V2 - VERIFY Node.

Validates execution results and determines PASS/FAIL.
"""


logger = logging.getLogger(__name__)


async def verify_node(state: GraphState) -> GraphState:
    """Verify execution results against expected outcomes.
    1. No errors accumulated during execution
    2. EXECUTE status is "success" or "skip"
    3. All 3 strategists (TRUTH, GOODNESS, BEAUTY) produced output

    Sets state.outputs["VERIFY"]["status"] to "pass" or "fail".
    """
    issues: list[str] = []

    # Check for accumulated errors
    if state.errors:
        issues.append(f"Errors present: {len(state.errors)}")

    # Check EXECUTE status
    execute_result = state.outputs.get("EXECUTE", {})
    execute_status = execute_result.get("status")
    if execute_status not in ("success", "skip"):
        issues.append(f"EXECUTE status: {execute_status}")

    # Check 3 strategists output
    for strategist in ("TRUTH", "GOODNESS", "BEAUTY"):
        if strategist not in state.outputs:
            issues.append(f"Missing {strategist} output")

    # Determine verdict
    if issues:
        state.outputs["VERIFY"] = {
            "status": "fail",
            "issues": issues,
        }
        logger.warning(f"[V2 VERIFY] FAIL: {issues}")
    else:
        state.outputs["VERIFY"] = {
            "status": "pass",
            "checked": ["errors", "execute", "strategists"],
        }
        logger.info("[V2 VERIFY] PASS")

    return state
