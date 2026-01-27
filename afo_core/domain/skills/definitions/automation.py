from __future__ import annotations

from typing import cast

from ..models import (
    AFOSkillCard,
    ExecutionMode,
    MCPConfig,
    PhilosophyScore,
    SkillCategory,
    SkillIOSchema,
    SkillParameter,
)
from .utils import get_mcp_server_url


def get_automation_skills() -> list[AFOSkillCard]:
    """WORKFLOW_AUTOMATION & STRATEGIC_COMMAND Skills"""
    skills = []

    # Skill 1: YouTube to n8n Spec Generator
    skill_001 = AFOSkillCard(
        skill_id="skill_001_youtube_spec_gen",
        name="YouTube to n8n Spec Generator",
        description="Converts YouTube tutorial transcripts to executable n8n workflow specifications using GPT-4o-mini",
        category=SkillCategory.WORKFLOW_AUTOMATION,
        tags=["youtube", "n8n", "spec-generation", "llm", "workflow"],
        version="1.0.0",
        capabilities=[
            "youtube_transcript_extraction",
            "llm_spec_generation",
            "n8n_workflow_creation",
            "error_handling",
        ],
        dependencies=["openai_api", "transcript_mcp"],
        execution_mode=ExecutionMode.ASYNC,
        endpoint=None,
        estimated_duration_ms=15000,
        input_schema=SkillIOSchema(
            parameters=[
                SkillParameter(
                    name="youtube_url",
                    type="string",
                    description="YouTube video URL",
                    required=True,
                ),
                SkillParameter(
                    name="transcript_base",
                    type="string",
                    description="Transcript MCP server base URL",
                    required=False,
                    default=get_mcp_server_url(),
                ),
            ],
            example={"youtube_url": "https://www.youtube.com/watch?v=abc123"},
        ),
        output_schema=SkillIOSchema(
            parameters=[
                SkillParameter(
                    name="node_spec",
                    type="dict",
                    description="n8n node specification JSON",
                    required=True,
                )
            ]
        ),
        philosophy_scores=PhilosophyScore(truth=95, goodness=90, beauty=92, serenity=88),
        mcp_config=MCPConfig(
            mcp_server_url=cast("str", get_mcp_server_url()),
            capabilities=["transcript_extraction"],
        ),
        documentation_url="https://github.com/lofibrainwav/AFO/blob/main/docs/skills/youtube-spec-gen.md",
    )
    skills.append(skill_001)

    # Skill 7: Automated Debugging
    skill_007 = AFOSkillCard(
        skill_id="skill_007_automated_debugging",
        name="Automated Debugging System",
        description="Complete automated debugging system for error detection, diagnosis, and auto-fix capabilities.",
        category=SkillCategory.WORKFLOW_AUTOMATION,
        tags=["debugging", "auto-fix", "diagnosis", "maintenance"],
        version="1.0.0",
        capabilities=[
            "error_detection",
            "error_classification",
            "auto_diagnosis",
            "solution_suggestion",
            "auto_fix",
            "trinity_score_calculation",
        ],
        dependencies=["ruff", "mypy", "ai-analysis"],
        execution_mode=ExecutionMode.ASYNC,
        estimated_duration_ms=5000,
        philosophy_scores=PhilosophyScore(truth=95, goodness=90, beauty=88, serenity=92),
    )
    skills.append(skill_007)

    # Skill 5: Strategy Engine (LangGraph)
    skill_005 = AFOSkillCard(
        skill_id="skill_005_strategy_engine",
        name="LangGraph Strategy Engine",
        description="4-stage command triage and orchestration using LangGraph with Redis checkpointing",
        category=SkillCategory.STRATEGIC_COMMAND,
        tags=["langgraph", "orchestration", "strategy", "triage"],
        version="2.3.0",
        capabilities=[
            "command_parsing",
            "command_triage",
            "strategy_determination",
            "redis_checkpointing",
            "stateful_conversations",
        ],
        dependencies=["langgraph", "redis"],
        execution_mode=ExecutionMode.ASYNC,
        estimated_duration_ms=1000,
        philosophy_scores=PhilosophyScore(truth=96, goodness=94, beauty=93, serenity=95),
        documentation_url="https://github.com/lofibrainwav/AFO/blob/main/afo_soul_engine/strategy_engine.py",
    )
    skills.append(skill_005)

    # Skill 10: Family Persona Manager
    skill_010 = AFOSkillCard(
        skill_id="skill_010_family_persona",
        name="Family Persona Manager",
        description="Manages the AFO Family personas (Yeongdeok, Yi Sun-sin, Jang Yeong-sil) and their interactions",
        category=SkillCategory.STRATEGIC_COMMAND,
        tags=["family", "persona", "roleplay", "interaction"],
        version="1.0.0",
        capabilities=[
            "persona_loading",
            "dialogue_generation",
            "relationship_management",
            "family_meeting",
        ],
        dependencies=["openai_api"],
        execution_mode=ExecutionMode.SYNC,
        estimated_duration_ms=500,
        philosophy_scores=PhilosophyScore(truth=92, goodness=94, beauty=96, serenity=95),
    )
    skills.append(skill_010)

    # Skill 11 ALT: DevTool Belt
    skill_011_alt = AFOSkillCard(
        skill_id="skill_011_dev_tool_belt",
        name="AFO DevTool Belt",
        description="Essential development tools for agents: Linting, Testing, Git, and Docker management",
        category=SkillCategory.WORKFLOW_AUTOMATION,
        tags=["devtools", "lint", "test", "git", "docker", "maintenance"],
        version="1.0.0",
        capabilities=[
            "run_linter",
            "run_tests",
            "git_commit",
            "docker_restart",
            "system_health_check",
        ],
        dependencies=["ruff", "pytest", "git", "docker"],
        execution_mode=ExecutionMode.SYNC,
        estimated_duration_ms=2000,
        philosophy_scores=PhilosophyScore(truth=98, goodness=95, beauty=90, serenity=97),
    )
    skills.append(skill_011_alt)

    # Skill 15: Suno AI Composer
    skill_015 = AFOSkillCard(
        skill_id="skill_015_suno_composer",
        name="Suno AI Music Composer",
        description="Generates music and lyrics using Suno AI. Handles polling and downloading.",
        category=SkillCategory.WORKFLOW_AUTOMATION,
        tags=["suno", "music", "creative", "ai-art", "audio"],
        version="1.0.0",
        capabilities=[
            "generate_music",
            "generate_lyrics",
            "download_audio",
            "get_credits",
        ],
        dependencies=["suno-api", "requests"],
        execution_mode=ExecutionMode.ASYNC,
        estimated_duration_ms=60000,
        philosophy_scores=PhilosophyScore(truth=85, goodness=90, beauty=100, serenity=95),
    )
    skills.append(skill_015)

    return skills
