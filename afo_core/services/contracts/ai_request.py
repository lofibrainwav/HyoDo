from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AIRequest(BaseModel):
    """AI 요청 모델 - 파이썬 기본값 고정 (MyPy symlink 호환)"""

    prompt: str
    context: dict[str, Any] | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    use_cache: bool = True


class AIResponse(BaseModel):
    """AI 응답 모델"""

    response: str
    usage: dict[str, int] | None = None
    cached: bool = False
    processing_time: float = 0.0
    model: str = ""
