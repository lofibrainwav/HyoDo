from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from AFO.afo_skills_registry import register_core_skills

if TYPE_CHECKING:
    from AFO.afo_skills_registry import SkillRegistry

logger = logging.getLogger(__name__)

# Import skill registry components for runtime
try:
    SKILL_REGISTRY_AVAILABLE = True
except ImportError:
    SKILL_REGISTRY_AVAILABLE = False


class SkillLoader:
    """Skill Registry 초기화 및 로딩 담당"""

    def __init__(self) -> None:
        self.skill_registry: SkillRegistry | None = None
        self.initialize_registry()

    def initialize_registry(self) -> None:
        """Skill Registry 초기화"""
        try:
            self.skill_registry = register_core_skills()
            skill_count = (
                len(self.skill_registry._skills) if hasattr(self.skill_registry, "_skills") else 0
            )
            logger.info("✅ Skill Registry 초기화됨: %d개 스킬", skill_count)

            # 카테고리 통계 로깅
            if self.skill_registry and hasattr(self.skill_registry, "get_category_stats"):
                category_stats = self.skill_registry.get_category_stats()
                logger.info("📊 카테고리 통계: %s", category_stats)

        except Exception as e:
            logger.error("❌ Skill Registry 초기화 실패: %s", e)
            self.skill_registry = None

    @property
    def registry(self) -> SkillRegistry | None:
        return self.skill_registry

    @property
    def is_available(self) -> bool:
        return self.skill_registry is not None
