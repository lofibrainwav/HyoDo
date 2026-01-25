"""
Julie CPA Agent Implementations

Three-tier agent architecture for tax analysis, compliance, and auditing
integrated with Chancellor Graph and Trinity Score evaluation.
"""

from typing import Any

from .associate import JulieAssociateAgent
from .auditor import JulieAuditorAgent
from .manager import JulieManagerAgent

__all__ = [
    "JulieAssociateAgent",
    "JulieManagerAgent",
    "JulieAuditorAgent",
    "process_julie_cpa_workflow",
]


# Convenience function for external use
async def process_julie_cpa_workflow(
    client_data: dict[str, Any],
    tax_documents: list[dict[str, Any]],
    analysis_type: str,
) -> dict[str, Any]:
    """Complete Julie CPA workflow from start to finish"""

    # Initialize agents
    associate = JulieAssociateAgent()
    manager = JulieManagerAgent()
    auditor = JulieAuditorAgent()

    # Step 1: Associate analysis
    associate_result = await associate.analyze_tax_scenario(
        client_data, tax_documents, analysis_type
    )

    # Step 2: Manager review
    manager_result = await manager.review_associate_draft(
        associate_result["draft_analysis"],
        associate_result["evidence_links"],
        {"objective": "tax_optimization"},  # Simplified client objectives
    )

    # Step 3: Auditor finalization (if Trinity Score allows)
    if manager_result["gate_decision"] == "AUTO_RUN":
        auditor_result = await auditor.perform_final_audit(
            associate_result["draft_analysis"],
            manager_result,
            {"evidence_bundle": associate_result["evidence_links"]},  # Simplified evidence bundle
        )
    else:
        auditor_result = {
            "status": "REQUIRES_MANUAL_REVIEW",
            "reason": "Trinity Score below threshold",
        }

    return {
        "workflow_status": "completed",
        "associate_phase": associate_result,
        "manager_phase": manager_result,
        "auditor_phase": auditor_result,
        "overall_trinity_score": manager_result["trinity_score"],
        "final_status": auditor_result.get("certification_status", "PENDING"),
    }
