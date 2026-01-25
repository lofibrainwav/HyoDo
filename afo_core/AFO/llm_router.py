# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO LLM Router Compatibility Layer (AFO/llm_router.py)

This module provides backward compatibility for code that imports from AFO.llm_router.
The actual implementation is in infrastructure/llm/.
"""

from infrastructure.llm import (
    LLMConfig,
    LLMProvider,
    LLMRouter,
    QualityTier,
    RoutingDecision,
)

# Singleton instance for backward compatibility
llm_router = LLMRouter()


async def route_and_execute(
    prompt: str,
    task_type: str | None = None,
    **kwargs: object,
) -> str:
    """Route a prompt to the appropriate LLM and execute."""
    result = await llm_router.route(prompt, task_type=task_type, **kwargs)
    return str(result)


__all__ = [
    "LLMConfig",
    "LLMProvider",
    "LLMRouter",
    "QualityTier",
    "RoutingDecision",
    "llm_router",
    "route_and_execute",
]
