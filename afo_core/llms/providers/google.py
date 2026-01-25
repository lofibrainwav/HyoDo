# Trinity Score: 90.0 (Established by Chancellor)
"""
Google Gemini Provider for AFO Kingdom
"""

import logging
from typing import Any

from AFO.base import BaseLLMProvider
from AFO.llm_router import LLMConfig

try:
    from AFO.llms.gemini_api import gemini_api
except ImportError:
    gemini_api = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class GoogleProvider(BaseLLMProvider):
    """
    Provider implementation for Google Gemini models via REST API wrapper.
    """

    async def is_available(self) -> bool:
        return gemini_api is not None and gemini_api.is_available()

    async def generate(
        self, query: str, config: LLMConfig, context: dict[str, Any] | None = None
    ) -> str:
        """
        Call Gemini API.
        """
        if not self.is_available():
            raise ValueError("Gemini API Wrapper not available")

        context = context or {}
        models_to_try = [
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ]

        if config.model and config.model in models_to_try:
            models_to_try.remove(config.model)
            models_to_try.insert(0, config.model)
        elif config.model:
            models_to_try.insert(0, config.model)

        last_error = None
        if gemini_api:
            for model_name in models_to_try:
                try:
                    result = await gemini_api.generate(
                        query,
                        model=model_name,
                        max_tokens=int(context.get("max_tokens", config.max_tokens)),
                        temperature=float(context.get("temperature", config.temperature)),
                    )
                    return str(result)
                except Exception as e:
                    last_error = e
                    logger.warning(f"Gemini model {model_name} failed: {e}")
                    continue

        if last_error:
            raise last_error
        raise ValueError("All Gemini models failed or no models available")

    async def generate_response(self, prompt: str, **kwargs: Any) -> str:
        """
        Public contract implementation (眞: Google)
        """
        if not gemini_api:
            raise ValueError("Gemini API Wrapper not available")

        res = await gemini_api.generate(prompt, **kwargs)
        return str(res)
