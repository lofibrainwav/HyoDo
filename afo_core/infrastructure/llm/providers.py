from __future__ import annotations

import logging
from typing import Any

import httpx

from AFO.config.settings import get_settings
from AFO.llms.claude_api import claude_api
from AFO.llms.cli_wrapper import CLIWrapper
from AFO.llms.gemini_api import gemini_api
from AFO.llms.openai_api import openai_api
from services.ollama_service import ollama_service

from .models import LLMConfig, LLMProvider, RoutingDecision

# Trinity Score: 92.0 (Established by Chancellor)
"""
AFO LLM Providers (infrastructure/llm/providers.py)

Implementation of provider-specific LLM calling logic.
"""


logger = logging.getLogger(__name__)

# Optional imports for LLM wrappers
try:
    API_WRAPPERS_AVAILABLE = True
except ImportError:
    API_WRAPPERS_AVAILABLE = False
    claude_api = None  # type: ignore
    CLIWrapper = None  # type: ignore
    openai_api = None  # type: ignore
    gemini_api = None  # type: ignore
    ollama_service = None  # type: ignore


async def call_llm(
    decision: RoutingDecision,
    query: str,
    context: dict[str, Any] | None,
    llm_configs: dict[LLMProvider, LLMConfig],
) -> str:
    """Dispatches call to the appropriate LLM provider"""
    provider = decision.selected_provider
    config = llm_configs.get(provider)

    if not config:
        raise ValueError(f"No configuration found for provider: {provider}")

    try:
        if provider == LLMProvider.OLLAMA:
            return await call_ollama(query, config, context)
        elif provider == LLMProvider.GEMINI:
            return await query_google(query, config, context)
        elif provider == LLMProvider.ANTHROPIC:
            return await call_anthropic(query, config, context)
        elif provider == LLMProvider.OPENAI:
            return await call_openai(query, config, context)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    except Exception as e:
        logger.error(f"LLM call failed for {provider}: {e}")
        raise


def _build_ollama_prompt(query: str, context: dict[str, Any] | None) -> str:
    """Builds an enriched prompt for Ollama with MCP context."""
    if not context:
        return query

    ctx = context
    lines = []

    # 1. System Identity (Implicit)
    lines.append(
        "당신은 AFO 왕국의 신임받는 책사입니다. 주어진 컨텍스트를 활용하여 사령관의 질문에 답하세요."
    )

    # 2. Context7 Documents
    if docs := ctx.get("context7_docs"):
        lines.append("\n[참조 문서 (Context7)]")
        for i, doc in enumerate(docs, 1):
            lines.append(f"문서 {i}: {doc}")

    # 3. Available Skills
    if skills := ctx.get("available_skills"):
        lines.append("\n[사용 가능한 스킬 (AFO Skills)]")
        lines.append("필요한 경우 다음 형식을 사용하여 스킬 실행을 요청할 수 있습니다:")
        lines.append("USE_SKILL: skill_id, params: {JSON}")
        for skill in skills:
            lines.append(f"- {skill['id']}: {skill['description']}")

    # 4. Sequential Thinking
    if (st := ctx.get("sequential_thinking")) and st.get("enabled"):
        lines.append("\n[사고 체계 (Sequential Thinking)]")
        lines.append("다음 단계에 따라 논리적으로 추론하세요:")
        for step, desc in st.get("template", {}).items():
            lines.append(f"- {step}: {desc}")

    # 5. User Query
    lines.append(f"\n[사령관의 질문]\n{query}")
    lines.append("\n[답변]")

    return "\n".join(lines)


async def call_ollama(query: str, config: LLMConfig, context: dict[str, Any] | None = None) -> str:
    """Ollama API 호출 (Ollama API Call)"""

    settings = get_settings()
    base_url = config.base_url or settings.OLLAMA_BASE_URL
    timeout = float((context or {}).get("ollama_timeout_seconds", 30))
    model = (context or {}).get("ollama_model", config.model)

    # Robust Switching Protocol (if available)
    try:
        settings = get_settings()
        if (
            settings.OLLAMA_SWITCHING_PROTOCOL_ENABLED
            and ollama_service
            and hasattr(ollama_service, "ensure_model")
        ):
            await ollama_service.ensure_model(model)
    except Exception:  # nosec
        pass

    try:
        enriched_prompt = _build_ollama_prompt(query, context)
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
            payload = {
                "model": model,
                "prompt": enriched_prompt,
                "stream": False,
                "options": {
                    "temperature": (context or {}).get("temperature", config.temperature),
                    "num_predict": (context or {}).get("max_tokens", config.max_tokens),
                    "num_ctx": (context or {}).get("ollama_num_ctx", config.context_window),
                },
            }
            response = await client.post(f"{base_url}/api/generate", json=payload)
            response.raise_for_status()
            return str(response.json().get("response", ""))
    except Exception:
        # Fallback to CLI Wrapper
        if CLIWrapper and CLIWrapper.is_available("ollama"):
            res = await CLIWrapper.execute_ollama(query)
            if res["success"]:
                return str(res["content"])
        raise


async def query_google(query: str, config: LLMConfig, context: dict[str, Any] | None) -> str:
    """Google Gemini API 호출 (Gemini API Call)"""
    if not gemini_api or not gemini_api.is_available():
        raise RuntimeError("Gemini API not available")

    models_to_try = ["gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro"]
    last_error = None
    ctx = context or {}

    for model_name in models_to_try:
        try:
            result = await gemini_api.generate(
                query,
                model=model_name,
                temperature=ctx.get("temperature", 0.7),
                max_tokens=ctx.get("max_tokens", 1000),
            )
            if result.get("success"):
                return str(result.get("content", ""))
            last_error = Exception(result.get("error", "Unknown error"))
        except Exception as e:
            last_error = e

    raise last_error or RuntimeError("All Gemini models failed")


async def call_anthropic(query: str, config: LLMConfig, context: dict[str, Any] | None) -> str:
    """Anthropic Claude API 호출 (Claude API Call)"""
    if claude_api and claude_api.is_available():
        result = await claude_api.generate(query, max_tokens=1024)
        if result.get("success"):
            return str(result.get("content", ""))

    if CLIWrapper and CLIWrapper.is_available("claude"):
        res = await CLIWrapper.execute_claude(query)
        if res["success"]:
            return str(res["content"])

    raise RuntimeError("Anthropic provider unavailable")


async def call_openai(query: str, config: LLMConfig, context: dict[str, Any] | None) -> str:
    """OpenAI API 호출 (OpenAI API Call)"""
    if openai_api and openai_api.is_available():
        result = await openai_api.generate(query, max_tokens=1024)
        if result.get("success"):
            return str(result.get("content", ""))

    if CLIWrapper and CLIWrapper.is_available("codex"):
        res = await CLIWrapper.execute_codex(query)
        if res["success"]:
            return str(res["content"])

    raise RuntimeError("OpenAI provider unavailable")
