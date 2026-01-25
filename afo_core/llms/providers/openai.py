# Trinity Score: 90.0 (Established by Chancellor)
import logging
import os
from typing import Any, cast

from AFO.base import BaseLLMProvider
from AFO.llm_router import LLMConfig

try:
    from AFO.llms.openai_api import openai_api
except ImportError:
    openai_api = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    Provider implementation for OpenAI and compatible APIs (e.g. DeepSeek via OpenAI compat).
    """

    async def is_available(self) -> bool:
        return openai_api is not None and (
            os.getenv("OPENAI_API_KEY") is not None
            or
            # Check for other compatible keys if strictly needed, but typically openai_api wrapper handles logic
            True
        )

    async def generate(
        self, query: str, config: LLMConfig, context: dict[str, Any] | None = None
    ) -> str:
        if not openai_api:
            raise ValueError("OpenAI API Wrapper not available")

        context = context or {}

        # Determine model
        model = context.get("model", config.model)

        # Prepare params
        kwargs = {
            "temperature": context.get("temperature", config.temperature),
            "max_tokens": int(context.get("max_tokens", config.max_tokens)),
        }

        try:
            # Using the existing wrapper
            response = await cast("Any", openai_api).generate_response(
                prompt=query, model=model, **kwargs
            )

            # Wrapper returns str directly or raises
            return str(response)

        except Exception as e:
            logger.error(f"OpenAI Call Failed: {e}")
            raise

    async def generate_response(self, prompt: str, **kwargs: Any) -> str:
        """
        Public contract implementation (眞: OpenAI)
        """
        if not openai_api:
            raise ValueError("OpenAI API Wrapper not available")

        res = await cast("Any", openai_api).generate_response(prompt=prompt, **kwargs)
        return str(res)
