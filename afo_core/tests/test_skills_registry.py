# Trinity Score: 90.0 (Established by Chancellor)
from typing import Any
from unittest.mock import patch

import pytest

from AFO.afo_skills_registry import (
    AFOSkillCard,
    PhilosophyScore,
    SkillCategory,
    SkillRegistry,
)


class TestSkillRegistry:
    def setup_method(self) -> None:
        """眞 (Truth): 테스트 전 레지스트리 초기화"""
        SkillRegistry._instance = None
        SkillRegistry._skills = {}

    def test_singleton(self) -> None:
        """眞 (Truth): 싱글톤 패턴 동작 테스트"""
        r1: Any = SkillRegistry()
        r2: Any = SkillRegistry()
        assert r1 is r2

    def test_register_and_get(self) -> None:
        """眞 (Truth): 스킬 등록 및 조회 기능 테스트"""
        registry: Any = SkillRegistry()
        skill: Any = AFOSkillCard(
            skill_id="skill_999_test",
            name="Test Skill",
            description="A test skill description that is long enough",
            category=SkillCategory.INTEGRATION,
            version="1.0.0",
            philosophy_scores=PhilosophyScore(truth=10, goodness=10, beauty=10, serenity=10),
        )
        assert registry.register(skill) is True
        # Register again returns False
        assert registry.register(skill) is False

        fetched = registry.get("skill_999_test")
        assert fetched == skill
        assert fetched.name == "Test Skill"

    def test_filter_category(self) -> None:
        """眞 (Truth): 카테고리 기반 스킬 필터링 테스트"""
        registry: Any = SkillRegistry()
        s1 = AFOSkillCard(
            skill_id="skill_001_s1",
            name="Skill One",
            description="Desc for S1.........",
            category=SkillCategory.INTEGRATION,
            version="1.0.0",
            philosophy_scores=PhilosophyScore(truth=10, goodness=10, beauty=10, serenity=10),
        )
        s2 = AFOSkillCard(
            skill_id="skill_002_s2",
            name="Skill Two",
            description="Desc for S2.........",
            category=SkillCategory.HEALTH_MONITORING,
            version="1.0.0",
            philosophy_scores=PhilosophyScore(truth=10, goodness=10, beauty=10, serenity=10),
        )
        registry.register(s1)
        registry.register(s2)

        from AFO.afo_skills_registry import SkillFilterParams

        results = registry.filter(SkillFilterParams(category=SkillCategory.INTEGRATION))
        assert len(results) == 1
        assert results[0].skill_id == "skill_001_s1"

    def test_filter_search(self) -> None:
        """眞 (Truth): 검색어 기반 스킬 필터링 테스트"""
        registry: Any = SkillRegistry()
        s1 = AFOSkillCard(
            skill_id="skill_001_s1",
            name="Apple Skill",
            description="A red fruit description",
            category=SkillCategory.INTEGRATION,
            version="1.0.0",
            philosophy_scores=PhilosophyScore(truth=10, goodness=10, beauty=10, serenity=10),
        )
        registry.register(s1)

        from AFO.afo_skills_registry import SkillFilterParams

        # Match name
        assert len(registry.filter(SkillFilterParams(search="Apple"))) == 1
        # Match desc
        assert len(registry.filter(SkillFilterParams(search="fruit"))) == 1
        # No match
        assert len(registry.filter(SkillFilterParams(search="banana"))) == 0

    def test_philosophy_score_properties(self) -> None:
        """美 (Beauty): 철학 점수 속성(평균, 요약) 검증"""
        score: PhilosophyScore = PhilosophyScore(truth=100, goodness=50, beauty=50, serenity=0)
        assert score.average == 50.0
        # Check for Chinese characters as per implementation
        assert "眞" in score.summary

    def test_validation_logic(self) -> None:
        """善 (Goodness): 스킬 카드 유효성 검증(Pydantic) 테스트"""
        from pydantic import ValidationError

        # Test invalid semantic version
        with pytest.raises(ValidationError):
            AFOSkillCard(
                skill_id="skill_000_bad",
                name="Bad Skill",
                description="Bad desc.....",
                category=SkillCategory.INTEGRATION,
                version="v1.0",  # Invalid pattern
                philosophy_scores=PhilosophyScore(truth=0, goodness=0, beauty=0, serenity=0),
            )

    def test_stats(self) -> None:
        """永 (Eternity): 카테고리별 통계 기능 테스트"""
        registry: Any = SkillRegistry()
        registry.register(
            AFOSkillCard(
                skill_id="skill_001_stat_test",
                name="Skill Stats",
                description="D1..........",
                category=SkillCategory.INTEGRATION,
                version="1.0.0",
                philosophy_scores=PhilosophyScore(truth=0, goodness=0, beauty=0, serenity=0),
            )
        )
        assert registry.count() == 1
        stats = registry.get_category_stats()
        assert stats[SkillCategory.INTEGRATION.value] == 1

    def test_built_in_registration(self) -> None:
        """眞 (Truth): 내장 코어 스킬 등록 테스트"""
        from AFO.afo_skills_registry import register_core_skills

        # Register core skills (no mock needed after modularization)
        registry: Any = register_core_skills()
        assert registry.count() > 0
        assert registry.get("skill_001_youtube_spec_gen") is not None
