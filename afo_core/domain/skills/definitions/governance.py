from __future__ import annotations

from ..models import (
    AFOSkillCard,
    ExecutionMode,
    PhilosophyScore,
    SkillCategory,
)


def get_governance_skills() -> list[AFOSkillCard]:
    """GOVERNANCE & STRATEGIC_COMMAND Skills"""
    skills = []

    # Skill 41: Royal Library
    skill_041 = AFOSkillCard(
        skill_id="skill_041_royal_library",
        name="Royal Library (41 Principles)",
        description="Collection of 41 strategic principles from Sun Tzu, Three Kingdoms, Machiavelli, and Clausewitz.",
        category=SkillCategory.GOVERNANCE,
        tags=["philosophy", "strategy", "classics", "wisdom"],
        version="1.0.0",
        capabilities=[
            "preflight_check",
            "dry_run_simulation",
            "retry_with_backoff",
            "strict_typing",
            "null_check_validation",
            "root_cause_analysis",
        ],
        execution_mode=ExecutionMode.SYNC,
        philosophy_scores=PhilosophyScore(truth=95, goodness=90, beauty=95, serenity=100),
    )
    skills.append(skill_041)

    return skills
