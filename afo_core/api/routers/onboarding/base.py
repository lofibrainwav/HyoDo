"""Onboarding Base Service - 추상 기반 서비스"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseOnboardingService(ABC):
    """온보딩 서비스 추상 기반 클래스 (眞: 명확한 인터페이스)"""

    @abstractmethod
    async def get_status(self) -> dict[str, Any]:
        """온보딩 상태 조회"""
        pass

    @abstractmethod
    async def get_system_architecture(self) -> dict[str, Any]:
        """시스템 아키텍처 조회"""
        pass

    @abstractmethod
    async def get_agent_memory_system(self) -> dict[str, Any]:
        """에이전트 기억 시스템 조회"""
        pass

    @abstractmethod
    async def demo_memory_search(self, query: str) -> dict[str, Any]:
        """메모리 검색 데모"""
        pass


class OnboardingServiceError(Exception):
    """온보딩 서비스 에러"""

    def __init__(self, message: str, details: Any = None) -> None:
        self.message = message
        self.details = details
        super().__init__(self.message)


__all__ = [
    "BaseOnboardingService",
    "OnboardingServiceError",
]
