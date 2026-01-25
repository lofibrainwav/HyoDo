from __future__ import annotations

from ..models import (
    AFOSkillCard,
    ExecutionMode,
    MCPConfig,
    PhilosophyScore,
    SkillCategory,
)


def get_analysis_skills() -> list[AFOSkillCard]:
    """ANALYSIS_EVALUATION & CODE_ANALYSIS Skills"""
    skills = []

    # Skill 0: Trinity Score Calculator
    skill_000 = AFOSkillCard(
        skill_id="skill_000_trinity_score_calculator",
        name="Trinity Score Calculator (眞善美孝永)",
        description="Calculate the 5-Pillar Trinity Score with weighted philosophy alignment.",
        category=SkillCategory.ANALYSIS_EVALUATION,
        tags=["philosophy", "evaluation", "metrics", "trinity", "score"],
        version="2.0.0",
        capabilities=["calculate_score", "evaluate_balance", "decision_matrix"],
        dependencies=["trinity_os"],
        execution_mode=ExecutionMode.SYNC,
        estimated_duration_ms=100,
        philosophy_scores=PhilosophyScore(truth=100, goodness=100, beauty=100, serenity=100),
        mcp_config=MCPConfig(mcp_version="2024.11.1", capabilities=["tools"]),
    )
    skills.append(skill_000)

    # Skill 4: Ragas Evaluator
    skill_004 = AFOSkillCard(
        skill_id="skill_004_ragas_evaluator",
        name="Ragas RAG Quality Evaluator",
        description="Evaluates RAG quality using 4 metrics: Faithfulness, Relevancy, Precision, Recall",
        category=SkillCategory.ANALYSIS_EVALUATION,
        tags=["ragas", "evaluation", "metrics", "quality"],
        version="1.2.0",
        capabilities=[
            "faithfulness_scoring",
            "answer_relevancy_scoring",
            "context_precision_scoring",
            "context_recall_scoring",
        ],
        dependencies=["ragas", "openai_api"],
        execution_mode=ExecutionMode.ASYNC,
        estimated_duration_ms=5000,
        philosophy_scores=PhilosophyScore(truth=99, goodness=92, beauty=88, serenity=85),
    )
    skills.append(skill_004)

    # Skill 6: ML Metacognition Upgrade
    skill_006 = AFOSkillCard(
        skill_id="skill_006_ml_metacognition",
        name="ML Metacognition Upgrade (Phase 3)",
        description="Self-reflection enhancement with user feedback loop and sympy 2nd derivative optimization",
        category=SkillCategory.ANALYSIS_EVALUATION,
        tags=["metacognition", "optimization", "feedback", "phase3"],
        version="3.0.0",
        capabilities=[
            "feedback_integration",
            "convexity_proof",
            "gap_reduction",
            "10_iteration_loop",
        ],
        dependencies=["sympy", "numpy"],
        execution_mode=ExecutionMode.SYNC,
        estimated_duration_ms=2000,
        philosophy_scores=PhilosophyScore(truth=95, goodness=94, beauty=92, serenity=93),
    )
    skills.append(skill_006)

    # Skill 8: Soul Refine
    skill_008 = AFOSkillCard(
        skill_id="skill_008_soul_refine",
        name="Soul Refine (Vibe Alignment)",
        description="Vibe coding and taste alignment using cosine similarity and philosophy balance",
        category=SkillCategory.ANALYSIS_EVALUATION,
        tags=["vibe", "alignment", "soul", "taste", "philosophy"],
        version="1.0.0",
        capabilities=[
            "cosine_similarity",
            "vibe_alignment",
            "philosophy_refinement",
            "soul_purity_calculation",
        ],
        dependencies=["numpy"],
        execution_mode=ExecutionMode.SYNC,
        estimated_duration_ms=1000,
        philosophy_scores=PhilosophyScore(truth=94, goodness=95, beauty=97, serenity=96),
    )
    skills.append(skill_008)

    # Skill 9: Advanced Cosine Similarity
    skill_009 = AFOSkillCard(
        skill_id="skill_009_advanced_cosine",
        name="Advanced Cosine Similarity (4 Techniques)",
        description="4 advanced cosine similarity techniques: Weighted, Sparse, Embedding, sqrt (stability 10% ↑)",
        category=SkillCategory.ANALYSIS_EVALUATION,
        tags=["cosine", "advanced", "weighted", "sparse", "embedding", "sqrt", "taste"],
        version="1.0.0",
        capabilities=[
            "weighted_cosine",
            "sparse_cosine_scipy",
            "embedding_cosine_bert",
            "sqrt_cosine_stability",
        ],
        dependencies=["scipy", "sentence-transformers"],
        execution_mode=ExecutionMode.SYNC,
        estimated_duration_ms=1200,
        philosophy_scores=PhilosophyScore(truth=97, goodness=96, beauty=93, serenity=95),
    )
    skills.append(skill_009)

    # Skill 21: Code Analysis Agent
    skill_021 = AFOSkillCard(
        skill_id="skill_021_code_analysis",
        name="Code Analysis Agent",
        description="Deep static code analysis and typing verification using Ruff and MyPy.",
        category=SkillCategory.CODE_ANALYSIS,
        tags=["code-analysis", "ruff", "mypy", "static-analysis"],
        version="1.0.0",
        capabilities=["lint_code", "type_check", "quality_report"],
        dependencies=["ruff", "mypy"],
        execution_mode=ExecutionMode.ASYNC,
        estimated_duration_ms=8000,
        philosophy_scores=PhilosophyScore(truth=100, goodness=95, beauty=90, serenity=90),
    )
    skills.append(skill_021)

    return skills
