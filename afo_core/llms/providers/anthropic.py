# Trinity Score: 90.0 (Established by Chancellor)
import logging
import os
from typing import Any, cast

from AFO.base import BaseLLMProvider
from AFO.llm_router import LLMConfig

try:
    from AFO.llms.claude_api import claude_api
except ImportError:
    claude_api = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """
    Provider implementation for Anthropic Claude models.
    """

    async def is_available(self) -> bool:
        return claude_api is not None and (os.getenv("ANTHROPIC_API_KEY") is not None)

    async def generate(
        self, query: str, config: LLMConfig, context: dict[str, Any] | None = None
    ) -> str:
        if not claude_api:
            raise ValueError("Claude API Wrapper not available")

        context = context or {}
        model = context.get("model", config.model)

        try:
            # existing wrapper signature: generate_response(prompt, model=..., max_tokens=..., temperature=...)
            response = await cast("Any", claude_api).generate_response(
                prompt=query,
                model=model,
                max_tokens=int(context.get("max_tokens", config.max_tokens)),
                temperature=float(context.get("temperature", config.temperature)),
            )
            return str(response)
        except Exception as e:
            logger.error(f"Anthropic Call Failed: {e}")
            raise

    async def generate_response(self, prompt: str, **kwargs: Any) -> str:
        """
        Public contract implementation (眞: Anthropic)
        """
        if not claude_api:
            raise ValueError("Claude API Wrapper not available")

        res = await cast("Any", claude_api).generate_response(prompt=prompt, **kwargs)
        return str(res)
