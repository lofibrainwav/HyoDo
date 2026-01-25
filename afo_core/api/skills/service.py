from __future__ import annotations

from typing import TYPE_CHECKING, Any

from afo_soul_engine.api.core.base_service import BaseService

if TYPE_CHECKING:
    from afo_soul_engine.api.models.skills import (
        SkillExecuteRequest,
        SkillExecutionResult,
        SkillFilterRequest,
        SkillListResponse,
        SkillRequest,
        SkillResponse,
        SkillStatsResponse,
    )

from .executor import SkillExecutor
from .loader import SkillLoader
from .manager import SkillManager


class SkillsService(BaseService):
    """Skill Registry 비즈니스 로직 서비스 (Facade for Modular Components)"""

    def __init__(self) -> None:
        super().__init__()
        self.loader = SkillLoader()
        self.manager = SkillManager(self.loader.registry)
        self.executor = SkillExecutor(self.loader.registry)

    async def register_skill(self, request: SkillRequest) -> SkillResponse:
        """스킬 등록"""
        return self.manager.register_skill(request)

    async def get_skill(self, skill_id: str) -> SkillResponse | None:
        """스킬 조회"""
        return self.manager.get_skill(skill_id)

    async def list_skills(self, filters: SkillFilterRequest | None = None) -> SkillListResponse:
        """스킬 목록 조회"""
        return self.manager.list_skills(filters)

    async def execute_skill(self, request: SkillExecuteRequest) -> SkillExecutionResult:
        """스킬 실행"""
        return await self.executor.execute_skill(request)

    async def delete_skill(self, skill_id: str) -> bool:
        """스킬 삭제"""
        return self.manager.delete_skill(skill_id)

    async def get_stats(self) -> SkillStatsResponse:
        """스킬 통계 조회"""
        return self.manager.get_stats(self.executor.get_execution_stats())

    async def health_check(self) -> dict[str, Any]:
        """서비스 헬스 체크"""
        return {
            "service": "skills",
            "status": "healthy" if self.loader.is_available else "degraded",
            "philosophy": "眞善美孝",
            "registry_available": self.loader.is_available,
            "total_skills": (
                len(self.loader.registry.__class__._skills) if self.loader.registry else 0
            ),
        }
