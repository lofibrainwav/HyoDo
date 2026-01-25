from __future__ import annotations

from ..models import (
    AFOSkillCard,
    ExecutionMode,
    PhilosophyScore,
    SkillCategory,
    SkillIOSchema,
    SkillParameter,
)


def get_creative_skills() -> list[AFOSkillCard]:
    """CREATIVE_AI Skills"""
    skills = []

    # Skill 29: GenUI Expander
    skill_029 = AFOSkillCard(
        skill_id="skill_029_gen_ui_expander",
        name="GenUI Expander",
        description="Autonomously generates and refines React UI components.",
        category=SkillCategory.CREATIVE_AI,
        tags=["gen-ui", "react", "frontend", "auto-design"],
        version="1.0.0",
        capabilities=["generate_component", "refine_ui", "preview_render"],
        dependencies=["react-agent"],
        execution_mode=ExecutionMode.ASYNC,
        estimated_duration_ms=15000,
        philosophy_scores=PhilosophyScore(truth=90, goodness=95, beauty=100, serenity=95),
    )
    skills.append(skill_029)

    # Skill 31: AI Code Reviewer
    skill_031 = AFOSkillCard(
        skill_id="skill_031_ai_code_reviewer",
        name="AI Code Reviewer",
        description="AI 기반 코드 품질 분석 및 개선 제안 시스템",
        category=SkillCategory.CREATIVE_AI,
        tags=["ai", "code-review", "quality", "improvement"],
        version="1.0.0",
        capabilities=[
            "static_analysis",
            "code_quality_scoring",
            "improvement_suggestions",
            "best_practices_check",
        ],
        dependencies=["openai_api", "ruff", "mypy"],
        execution_mode=ExecutionMode.ASYNC,
        estimated_duration_ms=5000,
        input_schema=SkillIOSchema(
            parameters=[
                SkillParameter(
                    name="code",
                    type="string",
                    description="리뷰할 코드 내용",
                    required=True,
                ),
                SkillParameter(
                    name="language",
                    type="string",
                    description="프로그래밍 언어",
                    required=False,
                    default="python",
                ),
            ]
        ),
        output_schema=SkillIOSchema(
            parameters=[
                SkillParameter(
                    name="review_score",
                    type="int",
                    description="코드 품질 점수 (0-100)",
                    required=True,
                ),
                SkillParameter(
                    name="suggestions",
                    type="list",
                    description="개선 제안 목록",
                    required=True,
                ),
                SkillParameter(
                    name="issues",
                    type="list",
                    description="발견된 문제점",
                    required=True,
                ),
            ]
        ),
        philosophy_scores=PhilosophyScore(truth=95, goodness=90, beauty=100, serenity=85),
    )
    skills.append(skill_031)

    return skills
