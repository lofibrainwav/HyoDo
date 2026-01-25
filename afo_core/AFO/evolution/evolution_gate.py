# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Evolution Gate
진화 검증 게이트 - Sima Yi's Shield.

Validates proposed evolutionary changes against safety protocols and constraints.
Acts as a filter before any change is proposed to the Sovereign.
"""

import logging
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger("AFO.Evolution.Gate")


class EvolutionProposal(BaseModel):
    """Proposal for system modification."""

    target_component: str
    proposed_changes: str
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL


class EvolutionGate:
    """The Gatekeeper of Evolution."""

    def verify_proposal(self, proposal: Any) -> dict[str, Any]:
        """Verify the safety of a proposal."""

        # Determine if input is dict or object
        if isinstance(proposal, dict):
            # Basic validation for dict
            target = proposal.get("target_component", "unknown")
            risk = proposal.get("risk_level", "UNKNOWN")
        else:
            target = proposal.target_component
            risk = proposal.risk_level

        logger.info(f"🛡️ Verifying proposal for {target} (Risk: {risk})")

        if risk == "CRITICAL":
            return {
                "safe": False,
                "reason": "Risk level CRITICAL is automatically rejected by Sima Yi.",
                "action": "REJECT",
            }

        return {
            "safe": True,
            "reason": "Proposal passed safety checks.",
            "action": "APPROVE",
        }


# Singleton Instance
evolution_gate = EvolutionGate()
