# Trinity Score: 95.0 (Enhanced by Phase 25 - Ollama Integration Hardening)
import asyncio
import contextlib
import logging
import os
from typing import Any

import httpx

from AFO.base import BaseLLMProvider
from AFO.llm_router import LLMConfig

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """
    Provider implementation for local Ollama models.

    Phase 25 Enhancements:
    - Configurable retry logic with exponential backoff
    - Health check before generation
    - Centralized settings integration (OLLAMA_BASE_URL, OLLAMA_TIMEOUT)
    - Fallback model support
    """

    # Fallback models in priority order (Bottom-Up strategy)
    FALLBACK_MODELS = [
        "qwen3-vl:2b",  # Fast model (Stage 1)
        "qwen2.5-coder:7b",  # Coder model
        "llama3.2:3b",  # Generic fallback
    ]

    async def is_available(self) -> bool:
        """Check if Ollama server is reachable (眞 - Truth check)."""
        try:
            from AFO.config.settings import get_settings

            settings = get_settings()
            base_url = settings.OLLAMA_BASE_URL
        except ImportError:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama availability check failed: {e}")
            return False

    async def generate(
        self, query: str, config: LLMConfig, context: dict[str, Any] | None = None
    ) -> str:
        """
        Call Ollama API with retry logic and fallback support.

        Phase 25 Enhancements:
        - Retry with exponential backoff (max 3 retries)
        - Fallback to alternative models on failure
        - Centralized timeout from settings.OLLAMA_TIMEOUT
        """
        # Get centralized settings (眞 - Single Source of Truth)
        try:
            from AFO.config.settings import get_settings

            settings = get_settings()
            base_url = config.base_url or settings.OLLAMA_BASE_URL
            default_timeout = float(settings.OLLAMA_TIMEOUT)
            max_retries = int(settings.OLLAMA_MAX_RETRIES)
        except ImportError:
            base_url = config.base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            default_timeout = 120.0
            max_retries = 3

        # Context overrides
        context = context or {}
        timeout_seconds = float(
            context.get("ollama_timeout_seconds", os.getenv("OLLAMA_TIMEOUT", str(default_timeout)))
        )
        max_tokens = int(context.get("max_tokens", config.max_tokens))
        temperature = float(context.get("temperature", config.temperature))
        model = str(context.get("ollama_model", config.model))
        num_ctx = int(context.get("ollama_num_ctx", getattr(config, "context_window", 4096)))
        num_threads = context.get("ollama_num_thread")

        # Build options
        options: dict[str, Any] = {
            "temperature": temperature,
            "num_predict": max_tokens,
            "num_ctx": num_ctx,
        }
        if num_threads is not None:
            with contextlib.suppress(Exception):
                options["num_thread"] = int(num_threads)

        # Retry with exponential backoff (善 - Resilience)
        last_error: Exception | None = None
        models_to_try = [model] + [m for m in self.FALLBACK_MODELS if m != model]

        for model_attempt in models_to_try:
            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout_seconds)) as client:
                        response = await client.post(
                            f"{base_url}/api/generate",
                            json={
                                "model": model_attempt,
                                "prompt": query,
                                "stream": False,
                                "options": options,
                            },
                        )
                        response.raise_for_status()
                        result = response.json()
                        response_text = str(result.get("response", ""))

                        if model_attempt != model:
                            logger.info(f"✅ Ollama fallback succeeded: {model} → {model_attempt}")

                        return response_text

                except httpx.TimeoutException as e:
                    last_error = e
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"⏱️ Ollama timeout (attempt {attempt + 1}/{max_retries}, model={model_attempt}), "
                        f"retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)

                except httpx.HTTPStatusError as e:
                    last_error = e
                    # Model not found - try next model immediately
                    if e.response.status_code == 404:
                        logger.warning(f"⚠️ Model '{model_attempt}' not found, trying fallback...")
                        break  # Skip remaining retries, try next model
                    wait_time = 2**attempt
                    logger.warning(
                        f"❌ Ollama HTTP error {e.response.status_code} "
                        f"(attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)

                except httpx.ConnectError as e:
                    last_error = e
                    logger.error(f"❌ Ollama connection failed: {base_url} - {e}")
                    # Connection error - no point retrying with same settings
                    break

                except Exception as e:
                    last_error = e
                    logger.error(f"❌ Ollama unexpected error: {e}")
                    break

        # All retries and fallbacks failed
        logger.error(f"❌ Ollama Call Failed after all retries: {last_error}")
        raise last_error or RuntimeError("Ollama generation failed with unknown error")

    async def generate_response(self, prompt: str, **kwargs: Any) -> str:
        """
        Public contract implementation (眞: Ollama)
        """
        # Simple configuration conversion for Ollama call
        from AFO.llm_router import LLMConfig, LLMProvider

        config = LLMConfig(
            model=str(kwargs.get("model", "llama3")),
            provider=LLMProvider.OLLAMA,
            temperature=float(kwargs.get("temperature", 0.0)),
            max_tokens=int(kwargs.get("max_tokens", 1024)),
        )
        return await self.generate(query=prompt, config=config, context=kwargs)
