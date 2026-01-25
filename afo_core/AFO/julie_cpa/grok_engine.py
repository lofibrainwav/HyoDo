"""Grok Engine - Refactored Wrapper.

Original code moved to: AFO/julie_cpa/grok/
"""

from typing import Any

from .grok import GrokConfig, GrokEngine

__all__ = ["GrokEngine", "GrokConfig", "consult_grok"]


async def consult_grok(
    prompt: dict[str, Any] | str,
    _market_context: str = "general",
    trinity_score: float = 0.0,
) -> dict[str, Any]:
    """Shim for consult_grok to fix import errors.

    Legacy function used by AFOConstitution.
    """
    # Simple mock response to allow system to function
    return {
        "analysis": "System is operating under safe parameters (Shim).",
        "action_items": [
            prompt.get("response_to_critique", "") if isinstance(prompt, dict) else str(prompt)
        ],
        "trinity_score": trinity_score,
    }
