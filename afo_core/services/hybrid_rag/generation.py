"""
HybridRAG LLM Answer Generation Functions

Trinity Score: 90.0 (Established by Chancellor)
- generate_answer: Ollama 기반 동기 답변 생성
- generate_answer_async: Ollama 기반 비동기 답변 생성
- generate_answer_stream_async: Ollama SSE 스트리밍 답변 생성

Phase 25: OpenAI 의존성 제거, Ollama 통일 (眞 - 로컬 지능 주권)
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from config.settings import settings


def _sse_fmt(event: str, data: Any) -> bytes:
    """SSE 이벤트 포맷팅"""
    return (f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n").encode()


def generate_answer(
    query: str,
    contexts: list[str],
    temperature: float,
    response_format: str,
    additional_instructions: str,
    llm_provider: str = "ollama",
    openai_client: Any = None,
    graph_context: list[dict[str, Any]] | None = None,
) -> str | dict[str, Any]:
    """
    眞 (Truth): Ollama 기반 컨텍스트 LLM 답변 생성 (GraphRAG Enhanced)
    善 (Goodness): API 호출 실패 시 에러 메시지 반환

    Args:
        query: 사용자 질문
        contexts: 선별된 컨텍스트 리스트
        temperature: LLM 온도
        response_format: 응답 형식 (markdown 등)
        additional_instructions: 추가 지침
        llm_provider: LLM 제공자 (미사용, API 호환성)
        openai_client: 미사용 (API 호환성 유지)
        graph_context: 그래프 RAG에서 추출된 컨텍스트 (선택 사항)

    Returns:
        Union[str, dict]: 생성된 답변 또는 에러 정보
    """
    # Unused parameters for API compatibility
    _ = response_format
    _ = llm_provider
    _ = graph_context
    _ = openai_client

    context_block = "\n\n".join([f"Chunk {idx + 1}:\n{ctx}" for idx, ctx in enumerate(contexts)])

    system_prompt = " ".join(
        part
        for part in [
            "You are the AFO Kingdom Hybrid RAG assistant.",
            "Answer using ONLY the provided chunks. If unsure, say you do not know.",
            "Reference the source when possible.",
            additional_instructions,
        ]
        if part
    )

    try:
        import requests

        ollama_host = settings.OLLAMA_BASE_URL
        ollama_model = settings.OLLAMA_MODEL

        payload = {
            "model": ollama_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Context:\n{context_block}\n\nQuestion: {query}",
                },
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }

        response = requests.post(
            f"{ollama_host}/api/chat",
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        return str(response.json()["message"]["content"])
    except Exception as e:
        return f"Error generating answer with Ollama: {e}"


async def generate_answer_async(
    query: str,
    contexts: list[str],
    temperature: float,
    response_format: str,
    additional_instructions: str,
    llm_provider: str = "ollama",
    openai_client: Any = None,
    graph_context: list[dict[str, Any]] | None = None,
) -> str | dict[str, Any]:
    """비동기 Ollama 답변 생성"""
    # Unused parameters for API compatibility
    _ = response_format
    _ = llm_provider
    _ = graph_context
    _ = openai_client

    context_block = "\n\n".join([f"Chunk {idx + 1}:\n{ctx}" for idx, ctx in enumerate(contexts)])

    system_prompt = " ".join(
        part
        for part in [
            "You are the AFO Kingdom Hybrid RAG assistant.",
            "Answer using ONLY the provided chunks. If unsure, say you do not know.",
            "Reference the source when possible.",
            additional_instructions,
        ]
        if part
    )

    try:
        ollama_host = settings.OLLAMA_BASE_URL
        ollama_model = settings.OLLAMA_MODEL

        payload = {
            "model": ollama_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Context:\n{context_block}\n\nQuestion: {query}",
                },
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{ollama_host}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            return str(response.json()["message"]["content"])
    except Exception as e:
        return f"Error generating answer with Ollama: {e}"


async def generate_answer_stream_async(
    query: str,
    contexts: list[str],
    temperature: float,
    response_format: str,
    additional_instructions: str,
    openai_client: Any = None,
) -> Any:  # AsyncIterator[bytes]
    """
    眞 (Truth): Ollama SSE 패턴 비동기 스트리밍 답변 생성
    善 (Goodness): 로컬 지능 주권 (Ollama 전용)

    Phase 25: OpenAI 의존성 제거
    """
    # Unused parameters for API compatibility
    _ = response_format
    _ = openai_client

    context_block = "\n\n".join([f"Chunk {idx + 1}:\n{ctx}" for idx, ctx in enumerate(contexts)])
    system_prompt = " ".join(
        part
        for part in [
            "You are the AFO Kingdom Hybrid RAG assistant.",
            "Answer using ONLY the provided chunks. If unsure, say you do not know.",
            "Reference the source when possible.",
            additional_instructions,
        ]
        if part
    )

    # 1. Start event
    yield _sse_fmt("start", {"engine": "hybrid_rag_stream_ollama"})

    # 2. Ollama Streaming (Local Sovereignty)
    try:
        ollama_url = settings.OLLAMA_BASE_URL
        ollama_model = settings.OLLAMA_MODEL

        payload = {
            "model": ollama_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Context:\n{context_block}\n\nQuestion: {query}",
                },
            ],
            "stream": True,
            "options": {"temperature": temperature},
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", f"{ollama_url}/api/chat", json=payload) as resp:
                if resp.status_code != 200:
                    yield _sse_fmt(
                        "error",
                        {"error": f"Ollama failed with status {resp.status_code}"},
                    )
                    return

                i = 0
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            token = chunk["message"]["content"]
                            yield _sse_fmt("token", {"i": i, "t": token})
                            i += 1
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue

        yield _sse_fmt("done", {"ok": True, "provider": "ollama"})

    except Exception as e:
        yield _sse_fmt("error", {"error": f"All LLM providers failed: {e!s}"})
