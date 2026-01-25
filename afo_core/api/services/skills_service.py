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

# New Modular implementation
from api.skills import SkillsService as NewSkillsService

# Backward Compatibility Setup
# We inherit from BaseService to maintain type hierarchy if checked elsewhere,
# but internally delegate to the new implementation.


class SkillsService(BaseService):
    """
    Skill Registry 비즈니스 로직 서비스 (眞善美孝)
    Facade Wrapper for Phase 73 Modularization
    """

    def __init__(self) -> None:
        super().__init__()
        self._impl = NewSkillsService()

    async def register_skill(self, request: SkillRequest) -> SkillResponse:
        return await self._impl.register_skill(request)

    async def get_skill(self, skill_id: str) -> SkillResponse | None:
        return await self._impl.get_skill(skill_id)

    async def list_skills(self, filters: SkillFilterRequest | None = None) -> SkillListResponse:
        return await self._impl.list_skills(filters)

    async def execute_skill(self, request: SkillExecuteRequest) -> SkillExecutionResult:
        return await self._impl.execute_skill(request)

    async def delete_skill(self, skill_id: str) -> bool:
        return await self._impl.delete_skill(skill_id)

    async def get_stats(self) -> SkillStatsResponse:
        return await self._impl.get_stats()

    async def health_check(self) -> dict[str, Any]:
        return await self._impl.health_check()

    @property
    def skill_registry(self) -> Any:
        return self._impl.loader.registry

    def __getattr__(self, name: str) -> Any:
        return getattr(self._impl, name)
