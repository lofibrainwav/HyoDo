"""
HybridRAG Pydantic Models

Trinity Score: 90.0 (Established by Chancellor)
"""

from __future__ import annotations

from pydantic import BaseModel


class HybridQueryRequest(BaseModel):
    """眞 (Truth): 하이브리드 RAG 쿼리 요청 모델"""

    query: str
    topK: int = 5
    contextLimit: int = 3500
    temperature: float = 0.3
    responseFormat: str = "markdown"
    additionalInstructions: str = ""
    returnChunks: bool = True
    llm_provider: str = "openai"


class HybridChunk(BaseModel):
    """眞 (Truth): 검색된 청크 모델"""

    id: str
    content: str
    score: float
    source: str | None = None


class HybridQueryResponse(BaseModel):
    """眞 (Truth): 하이브리드 RAG 응답 모델"""

    answer: str | dict
    chunks: list[HybridChunk] = []
    metadata: dict = {}
