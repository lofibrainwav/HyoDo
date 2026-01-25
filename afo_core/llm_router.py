# Trinity Score: 90.0 (Established by Chancellor)
"""
LLM Router Root Module (llm_router.py)

This module provides the public interface for the LLM routing system.
The actual implementation is in infrastructure/llm/.
"""

from infrastructure.llm import (
    LLMConfig,
    LLMProvider,
    LLMRouter,
    QualityTier,
    RoutingDecision,
    call_llm,
)

# Singleton instance
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
    "call_llm",
    "llm_router",
    "route_and_execute",
]
