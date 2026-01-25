from __future__ import annotations

import logging
from typing import Any

# New Modular Implementation
from infrastructure.llm.router import SSOTCompliantLLMRouter as NewRouter

logger = logging.getLogger(__name__)


class SSOTCompliantLLMRouter:
    """
    SSOT 준수 LLM 라우터 (Facade for Phase 74 Modularization)
    infrastructure/llm/ssot_compliant_router.py
    """

    def __init__(self) -> None:
        self._impl = NewRouter()

    def classify_task(self, query: str) -> str:
        return self._impl.classify_task(query)

    def get_scholar_for_task(self, task_type: str) -> str:
        return self._impl.get_scholar_for_task(task_type)

    async def call_scholar_via_wallet(
        self, scholar_key: str, query: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return await self._impl.call_scholar_via_wallet(scholar_key, query, context)

    def get_routing_stats(self) -> dict[str, Any]:
        return self._impl.get_routing_stats()

    @property
    def llm_configs(self) -> dict:
        """Legacy compatibility: Return empty configs or map from scholars"""
        return {}

    async def check_connections(self) -> dict[str, Any]:
        """Legacy compatibility: Health check"""
        return {"status": "healthy", "mode": "ssot_delegation"}

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the implementation"""
        return getattr(self._impl, name)


# 글로벌 인스턴스 (유지)
ssot_router = SSOTCompliantLLMRouter()


async def call_scholar(
    query: str, scholar_key: str | None = None, context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    SSOT 준수 학자 호출 헬퍼 함수

    Args:
        query: 사용자 쿼리
        scholar_key: 특정 학자 지정 (없으면 자동 선택)
        context: 추가 컨텍스트

    Returns:
        학자 응답 및 Trinity Score
    """
    if not scholar_key:
        task_type = ssot_router.classify_task(query)
        scholar_key = ssot_router.get_scholar_for_task(task_type)

    return await ssot_router.call_scholar_via_wallet(scholar_key, query, context or {})
