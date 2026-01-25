from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from AFO.api.chancellor_v2.graph.state import GraphState

"""REPORT Node - Generate final execution report."""


async def report_node(state: GraphState) -> GraphState:
    """Generate final report for the commander.
    sive report.

        Args:
            state: Current graph state

        Returns:
            Updated graph state with final report
    """
    # Collect all results
    merge_result = state.outputs.get("MERGE", {})
    execute_result = state.outputs.get("EXECUTE", {})
    verify_result = state.outputs.get("VERIFY", {})

    # Generate final report
    report = {
        "trace_id": state.trace_id,
        "request_id": state.request_id,
        "command": state.plan.get("command", ""),
        "skill_id": state.plan.get("skill_id", ""),
        "trinity_score": merge_result.get("trinity_score", 0),
        "execution_status": execute_result.get("status", "unknown"),
        "verification_status": verify_result.get("status", "unknown"),
        "errors": state.errors,
        "error_count": len(state.errors),
        "success": len(state.errors) == 0 and verify_result.get("status") == "pass",
        "duration": state.updated_at - state.started_at if state.updated_at else 0,
        "recommendations": [],
    }

    # Add recommendations based on results
    if report["success"]:
        report["recommendations"].append("✅ Execution completed successfully")
    else:
        report["recommendations"].append("❌ Execution had issues - review errors")

    if merge_result.get("trinity_score", 0) < 90:
        report["recommendations"].append("⚠️ Trinity Score below 90 - consider manual review")

    # Store final report
    if "REPORT" not in state.outputs:
        state.outputs["REPORT"] = {}

    state.outputs["REPORT"] = report

    return state
