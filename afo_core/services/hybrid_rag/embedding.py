"""
HybridRAG Embedding Functions

Trinity Score: 90.0 (Established by Chancellor)
- random_embedding: 폴백용 난수 임베딩
- get_embedding: Ollama embeddinggemma 임베딩 생성
- generate_hyde_query: Ollama HyDE 쿼리 생성

Phase 25: OpenAI 의존성 제거, Ollama 통일 (眞 - 로컬 지능 주권)
"""

from __future__ import annotations

import logging
import random
from typing import Any

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

# Default embedding dimension for embeddinggemma
_DEFAULT_EMBED_DIM = 768


def random_embedding(dim: int = _DEFAULT_EMBED_DIM) -> list[float]:
    """
    眞 (Truth): 난수 기반 임베딩 생성 (폴백용)

    Args:
        dim: 임베딩 차원 (기본 768 for embeddinggemma)

    Returns:
        list[float]: 생성된 난수 리스트
    """
    return [random.gauss(0, 0.1) for _ in range(dim)]


def get_embedding(text: str, client: Any = None) -> list[float]:
    """
    眞 (Truth): Ollama embeddinggemma를 이용한 텍스트 임베딩 추출
    善 (Goodness): 예외 발생 시 난수 임베딩으로 안전하게 폴백

    Args:
        text: 임베딩할 텍스트
        client: 미사용 (API 호환성 유지)

    Returns:
        list[float]: 추출된 임베딩 리스트
    """
    # client 파라미터는 API 호환성을 위해 유지하지만 사용하지 않음
    _ = client

    try:
        import requests

        ollama_host = settings.OLLAMA_BASE_URL
        embed_model = settings.EMBED_MODEL  # embeddinggemma

        # /api/embeddings 엔드포인트 사용 (Ollama 표준)
        response = requests.post(
            f"{ollama_host}/api/embeddings",
            json={"model": embed_model, "prompt": text},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as exc:
        logger.error(
            f"[Hybrid RAG] Ollama 임베딩 생성 실패, 난수로 대체합니다: {exc}",
            exc_info=True,
            extra={"pillar": "善"},
        )
        return random_embedding()


def generate_hyde_query(query: str, client: Any = None) -> str:
    """
    眞 (Truth) & 美 (Beauty): HyDE (Hypothetical Document Embeddings)
    Ollama를 사용하여 질문에 대한 '가상의 이상적인 답변'을 생성.

    Args:
        query: 사용자 질문
        client: 미사용 (API 호환성 유지)

    Returns:
        str: HyDE로 강화된 쿼리 (또는 가상 답변)
    """
    # client 파라미터는 API 호환성을 위해 유지하지만 사용하지 않음
    _ = client

    try:
        import requests

        ollama_host = settings.OLLAMA_BASE_URL
        ollama_model = settings.OLLAMA_MODEL

        payload = {
            "model": ollama_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful expert. Write a theoretical, concise passage that answers the user's question perfectly. Do not explain, just write the answer content.",
                },
                {"role": "user", "content": f"Question: {query}"},
            ],
            "stream": False,
            "options": {"temperature": 0.7},
        }

        response = requests.post(
            f"{ollama_host}/api/chat",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        hypothetical_answer = response.json()["message"]["content"]
        return f"{query}\n{hypothetical_answer}"
    except Exception as e:
        logger.error(
            f"[Hybrid RAG] Ollama HyDE 생성 실패: {e}", exc_info=True, extra={"pillar": "善"}
        )
        return query


async def get_embedding_async(text: str, client: Any = None) -> list[float]:
    """비동기 Ollama 임베딩 생성"""
    # client 파라미터는 API 호환성을 위해 유지하지만 사용하지 않음
    _ = client

    try:
        ollama_host = settings.OLLAMA_BASE_URL
        embed_model = settings.EMBED_MODEL

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                f"{ollama_host}/api/embeddings",
                json={"model": embed_model, "prompt": text},
            )
            response.raise_for_status()
            return response.json()["embedding"]
    except Exception as exc:
        logger.error(
            f"[Hybrid RAG] Ollama 비동기 임베딩 실패: {exc}", exc_info=True, extra={"pillar": "善"}
        )
        return random_embedding()


async def generate_hyde_query_async(query: str, client: Any = None) -> str:
    """비동기 Ollama HyDE 쿼리 생성"""
    # client 파라미터는 API 호환성을 위해 유지하지만 사용하지 않음
    _ = client

    try:
        ollama_host = settings.OLLAMA_BASE_URL
        ollama_model = settings.OLLAMA_MODEL

        payload = {
            "model": ollama_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful expert. Write a theoretical, concise passage that answers the user's question perfectly. Do not explain, just write the answer content.",
                },
                {"role": "user", "content": f"Question: {query}"},
            ],
            "stream": False,
            "options": {"temperature": 0.7},
        }

        async with httpx.AsyncClient(timeout=60.0) as http_client:
            response = await http_client.post(
                f"{ollama_host}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            hypothetical_answer = response.json()["message"]["content"]
            return f"{query}\n{hypothetical_answer}"
    except Exception as e:
        logger.error(
            f"[Hybrid RAG] Ollama 비동기 HyDE 실패: {e}", exc_info=True, extra={"pillar": "善"}
        )
        return query
