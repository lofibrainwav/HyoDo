"""Strategist Registry - 서브에이전트 등록 및 관리.

동적으로 Strategist를 등록하고 조회할 수 있는 레지스트리입니다.

AFO 철학:
- 孝 (Serenity): 동적 확장 가능한 구조
- 永 (Eternity): 등록된 Strategist 목록 추적
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Type, TypeVar

if TYPE_CHECKING:
    from ..sub_agents.base_strategist import BaseStrategist

S = TypeVar("S", bound="BaseStrategist")
logger = logging.getLogger(__name__)


class StrategistRegistry:
    """Strategist 서브에이전트 레지스트리.

    등록된 Strategist를 pillar 이름으로 조회할 수 있습니다.

    Usage:
        registry = StrategistRegistry()
        registry.register("truth", JangYeongSilAgent())
        strategist = registry.get("truth")
    """

    def __init__(self) -> None:
        """레지스트리 초기화."""
        self._strategists: dict[str, BaseStrategist] = {}

    def register(self, pillar: str, strategist: BaseStrategist) -> None:
        """Strategist 등록.

        Args:
            pillar: 기둥 이름 (truth, goodness, beauty)
            strategist: BaseStrategist 구현체
        """
        pillar_lower = pillar.lower()
        self._strategists[pillar_lower] = strategist
        logger.debug(f"Registered strategist for {pillar_lower}: {strategist.__class__.__name__}")

    def unregister(self, pillar: str) -> bool:
        """Strategist 등록 해제.

        Args:
            pillar: 기둥 이름

        Returns:
            해제 성공 여부
        """
        pillar_lower = pillar.lower()
        if pillar_lower in self._strategists:
            del self._strategists[pillar_lower]
            logger.debug(f"Unregistered strategist for {pillar_lower}")
            return True
        return False

    def get(self, pillar: str) -> BaseStrategist | None:
        """Strategist 조회.

        Args:
            pillar: 기둥 이름

        Returns:
            등록된 Strategist 또는 None
        """
        return self._strategists.get(pillar.lower())

    def get_as(self, pillar: str, strategist_type: type[S]) -> S | None:
        """Strategist를 특정 타입으로 조회.

        Args:
            pillar: 기둥 이름
            strategist_type: 기대하는 Strategist 클래스 타입

        Returns:
            타입이 매칭되는 Strategist 또는 None
        """
        instance = self.get(pillar)
        if isinstance(instance, strategist_type):
            return instance
        return None

    def get_all(self) -> dict[str, BaseStrategist]:
        """모든 등록된 Strategist 조회.

        Returns:
            pillar -> Strategist 매핑
        """
        return self._strategists.copy()

    def get_pillars(self) -> list[str]:
        """등록된 기둥 목록 조회.

        Returns:
            등록된 pillar 이름 목록
        """
        return list(self._strategists.keys())

    def has(self, pillar: str) -> bool:
        """Strategist 등록 여부 확인.

        Args:
            pillar: 기둥 이름

        Returns:
            등록 여부
        """
        return pillar.lower() in self._strategists

    def clear(self) -> None:
        """모든 Strategist 등록 해제."""
        self._strategists.clear()
        logger.debug("Cleared all strategists from registry")

    def __len__(self) -> int:
        """등록된 Strategist 수."""
        return len(self._strategists)

    def __contains__(self, pillar: str) -> bool:
        """in 연산자 지원."""
        return self.has(pillar)
