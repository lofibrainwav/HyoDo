import logging

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)


async def get_ollama_embedding(text: str) -> list[float]:
    """Ollama API를 사용하여 텍스트 임베딩 생성 (眞 - Truth)"""
    ollama_host = settings.OLLAMA_BASE_URL
    embed_model = settings.EMBED_MODEL

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # /api/embeddings 엔드포인트 사용 (Ollama 표준)
            payload = {"model": embed_model, "prompt": text}
            response = await client.post(f"{ollama_host}/api/embeddings", json=payload)
            response.raise_for_status()
            return response.json()["embedding"]
    except Exception as e:
        logger.error(f"Ollama 임베딩 생성 실패: {e}")
        return []


async def get_embedding(text: str, target_dim: int = 1536) -> list[float]:
    """
    통합 임베딩 탐색 (眞 - Dimension Awareness)
    지정된 차원에 맞는 임베딩 생성 시도
    """
    # 1. OpenAI 시도 (1536D 기본값)
    if target_dim == 1536:
        try:
            from AFO.llms.openai_api import openai_api

            if openai_api.is_available():
                embedding = await openai_api.embed(text)
                if embedding and len(embedding) == 1536:
                    return embedding
        except Exception:
            pass

    # 2. Ollama 시도 (768D 등)
    embedding = await get_ollama_embedding(text)
    if embedding:
        return embedding

    return []
