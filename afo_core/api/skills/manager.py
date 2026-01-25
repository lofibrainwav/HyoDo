from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from AFO.afo_skills_registry import (
    AFOSkillCard,
    ExecutionMode,
    SkillCategory,
    SkillFilterParams,
    SkillStatus,
)
from AFO.afo_skills_registry import (
    PhilosophyScore as RegistryPhilosophyScores,
)
from afo_soul_engine.api.models.skills import (
    PhilosophyScores,
    SkillCategoryStats,
    SkillFilterRequest,
    SkillListResponse,
    SkillRequest,
    SkillResponse,
    SkillStatsResponse,
)

if TYPE_CHECKING:
    from AFO.afo_skills_registry import SkillRegistry

logger = logging.getLogger(__name__)


class SkillManager:
    """Skill 등록, 조회, 관리 담당"""

    def __init__(self, registry: SkillRegistry | None) -> None:
        self.registry = registry

    def register_skill(self, request: SkillRequest) -> SkillResponse:
        """스킬 등록"""
        if not self.registry:
            raise ValueError("Skill Registry not available")

        # Enum 변환
        category_enum = SkillCategory(request.category)
        execution_mode_enum = ExecutionMode(request.execution_mode)

        skill_card = AFOSkillCard(
            skill_id=request.skill_id,
            name=request.name,
            description=request.description,
            category=category_enum,
            execution_mode=execution_mode_enum,
            version="1.0.0",
            parameters=request.parameters or {},
            philosophy_scores=RegistryPhilosophyScores(
                truth=85,
                goodness=80,
                beauty=75,
                serenity=90,
            ),
        )

        self.registry.skills[request.skill_id] = skill_card
        logger.info("✅ 스킬 등록됨: %s", request.skill_id)

        return self._to_skill_response(skill_card)

    def get_skill(self, skill_id: str) -> SkillResponse | None:
        """스킬 조회"""
        if not self.registry:
            return None

        skill = self.registry.get(skill_id)
        if not skill:
            return None

        return self._to_skill_response(skill)

    def list_skills(self, filters: SkillFilterRequest | None = None) -> SkillListResponse:
        """스킬 목록 조회"""
        if not self.registry:
            return self._empty_list_response(filters)

        if filters:
            category_enum = SkillCategory(filters.category) if filters.category else None
            status_enum = SkillStatus(filters.status) if filters.status else None
            execution_mode_enum = (
                ExecutionMode(filters.execution_mode) if filters.execution_mode else None
            )

            filter_params = SkillFilterParams(
                category=category_enum,
                status=status_enum,
                tags=filters.tags,
                search=filters.search,
                min_philosophy_avg=(
                    int(filters.min_philosophy_avg) if filters.min_philosophy_avg else None
                ),
                execution_mode=execution_mode_enum,
                offset=filters.offset,
                limit=filters.limit,
            )
            filtered_skills = self.registry.filter(filter_params)
        else:
            filtered_skills = self.registry.list_all()

        skills = [self._to_skill_response(skill) for skill in filtered_skills]

        return SkillListResponse(
            skills=skills,
            total_count=len(self.registry.skills),
            filtered_count=len(skills),
            offset=filters.offset if filters else 0,
            limit=filters.limit if filters else 50,
        )

    def delete_skill(self, skill_id: str) -> bool:
        """스킬 삭제"""
        if not self.registry:
            return False

        if skill_id in self.registry.skills:
            del self.registry.skills[skill_id]
            logger.info("✅ 스킬 삭제됨: %s", skill_id)
            return True
        return False

    def get_stats(self, execution_stats: dict[str, dict[str, Any]]) -> SkillStatsResponse:
        """스킬 통계 조회"""
        if not self.registry:
            return self._empty_stats_response()

        total_skills = len(self.registry.__class__._skills)
        all_skills = list(self.registry.__class__._skills.values())

        # Active Skills Count
        active_skills = sum(
            1
            for s in all_skills
            if (hasattr(s.status, "value") and s.status.value == "active")
            or str(s.status) == "active"
        )

        category_stats_raw = self.registry.get_category_stats()
        categories = []

        for cat_name, count in category_stats_raw.items():
            category_skills = [
                skill for skill in self.registry._skills.values() if skill.category == cat_name
            ]

            avg_philosophy = 0.0
            if category_skills:
                total_philosophy = sum(skill.philosophy_scores.average for skill in category_skills)
                avg_philosophy = total_philosophy / len(category_skills)

            execution_count = execution_stats.get(cat_name, {}).get("execution_count", 0)

            categories.append(
                SkillCategoryStats(
                    category=cat_name,
                    count=count,
                    avg_philosophy=round(avg_philosophy, 2),
                    execution_count=execution_count,
                    description=self._get_category_description(cat_name),
                )
            )

        # Recent executions & avg time
        recent_executions = sum(
            stats.get("execution_count", 0) for stats in execution_stats.values()
        )
        times = [stats.get("avg_execution_time", 0) for stats in execution_stats.values()]
        avg_execution_time = sum(times) / len(times) if times else 0.0

        return SkillStatsResponse(
            total_skills=total_skills,
            active_skills=active_skills,
            categories=categories,
            recent_executions=recent_executions,
            avg_execution_time=avg_execution_time,
            philosophy_distribution=self._calculate_philosophy_distribution(),
        )

    def _to_skill_response(self, skill: Any) -> SkillResponse:
        """AFOSkillCard -> SkillResponse 변환"""
        # Philosophy Score 변환
        truth = getattr(skill.philosophy_scores, "truth", 85.0)
        goodness = getattr(skill.philosophy_scores, "goodness", 80.0)
        beauty = getattr(skill.philosophy_scores, "beauty", 75.0)
        serenity = getattr(skill.philosophy_scores, "serenity", 90.0)

        return SkillResponse(
            skill_id=skill.skill_id,
            name=skill.name,
            description=skill.description,
            category=skill.category,
            execution_mode=skill.execution_mode,
            status=skill.status,
            philosophy=PhilosophyScores(
                truth=truth, goodness=goodness, beauty=beauty, serenity=serenity
            ),
            tags=skill.tags,
            parameters=skill.parameters,
            execution_count=getattr(skill, "execution_count", 0),
            created_at=getattr(skill, "created_at", datetime.now(UTC)),
            updated_at=getattr(skill, "updated_at", datetime.now(UTC)),
        )

    def _calculate_philosophy_distribution(self) -> dict[str, int]:
        distribution = {"90-95": 0, "95-100": 0}
        if not self.registry:
            return distribution

        for skill in self.registry.__class__._skills.values():
            avg_score = skill.philosophy_scores.average
            if 90 <= avg_score < 95:
                distribution["90-95"] += 1
            elif 95 <= avg_score <= 100:
                distribution["95-100"] += 1
        return distribution

    def _get_category_description(self, category: str) -> str:
        descriptions = {
            "workflow_automation": "워크플로우 자동화 (n8n, Zapier 등)",
            "rag_systems": "RAG 시스템 (검색-증강 생성)",
            "browser_automation": "브라우저 자동화 (스크래핑, 테스트)",
            "data_processing": "데이터 처리 및 변환",
            "ai_inference": "AI 추론 및 예측",
            "monitoring": "모니터링 및 알림",
            "utilities": "유틸리티 및 도구",
            "analysis_evaluation": "분석 및 평가 (Speckit 확장)",
            "integration": "외부 서비스 통합 (Speckit 확장)",
            "health_monitoring": "시스템 건강 모니터링 (11-오장육부)",
            "strategic_command": "전략적 명령 처리 (LangGraph)",
            "memory_management": "메모리 시스템 관리",
        }
        return descriptions.get(category, f"{category} 카테고리")

    def _empty_list_response(self, filters: SkillFilterRequest | None) -> SkillListResponse:
        return SkillListResponse(
            skills=[],
            total_count=0,
            filtered_count=0,
            offset=filters.offset if filters else 0,
            limit=filters.limit if filters else 50,
        )

    def _empty_stats_response(self) -> SkillStatsResponse:
        return SkillStatsResponse(
            total_skills=0,
            active_skills=0,
            categories=[],
            recent_executions=0,
            avg_execution_time=0.0,
            philosophy_distribution={},
        )
