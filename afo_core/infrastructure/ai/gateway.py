"""
AI Gateway Service
Centralized handling for LLM interactions.
Handles model routing, logging (telemetry), and streaming response generation.
"""

import json
import logging
import time
from datetime import datetime
from typing import AsyncGenerator

import httpx

from config.settings import settings
from domain.ai.models import AIMetadata, AIRequest
from domain.ai.prompts import get_prompt_template

logger = logging.getLogger(__name__)


class AIGateway:
    """
    Gateway for routing requests to the appropriate LLM provider.
    Currently mimics Vercel AI SDK streaming behavior using a mock generator,
    but structured to easily swap in real clients (OpenAI/Anthropic).
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key
        # In a real implementation, clients like AsyncOpenAI would be initialized here.

    def _route_model(self, persona: str) -> str:
        """
        Routes the request to a specific model based on necessity (眞 - Resolution).
        """
        model_map = {
            "auditor": "deepseek-r1:14b",
            "tax_analyst": "deepseek-r1:14b",
            "developer": "qwen2.5-coder:7b",
        }
        return model_map.get(persona, settings.OLLAMA_MODEL)

    async def generate_stream(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """
        Generates a streaming response using real Ollama API. (善 - Reality)
        """
        model = self._route_model(request.persona)
        start_time = time.time()

        # 1. Fetch and Format Prompt Template
        template = get_prompt_template(request.persona)
        context_str = (
            request.context or "No specific context provided. Answer based on general knowledge."
        )

        try:
            formatted_prompt = template.format(context=context_str, query=request.query)
        except Exception as e:
            logger.warning(f"Prompt formatting failed: {e}. Falling back to raw query.")
            formatted_prompt = request.query

        ollama_url = f"{settings.OLLAMA_BASE_URL}/api/generate"

        # 2. Prepare the payload for Ollama
        payload = {
            "model": model,
            "prompt": formatted_prompt,
            "stream": True,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens or -1,
            },
        }

        content_accumulated = []

        try:
            async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
                async with client.stream("POST", ollama_url, json=payload) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        data = json.loads(line)
                        chunk = data.get("response", "")

                        if chunk:
                            content_accumulated.append(chunk)
                            yield chunk

                        if data.get("done"):
                            break

        except Exception as e:
            error_msg = f"\n[AI Gateway Error] {e!s}"
            logger.error(error_msg)
            yield error_msg
            return

        # Log Metadata (Telemetry)
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        _metadata = AIMetadata(
            request_id=f"req_{int(datetime.now().timestamp())}",
            model_used=model,
            tokens_input=len(request.query) // 4,  # Approx
            tokens_output=len("".join(content_accumulated)) // 4,
            latency_ms=latency_ms,
            rag_sources=request.context_filters.get("sources", [])
            if request.context_filters
            else [],
        )

        # In a real system, we'd log this metadata to an observability platform asynchronously
        # print(f"[Telemetry] {metadata.model_dump_json()}")


# Singleton Instance for internal usage if needed
ai_gateway = AIGateway()
