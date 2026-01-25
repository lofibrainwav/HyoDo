from __future__ import annotations

from ..models import (
    AFOSkillCard,
    ExecutionMode,
    PhilosophyScore,
    SkillCategory,
    SkillIOSchema,
    SkillParameter,
)


def get_rag_skills() -> list[AFOSkillCard]:
    """RAG, MEMORY_MANAGEMENT & DATA_ENGINEERING Skills"""
    skills = []

    # Skill 2: Ultimate RAG
    skill_002 = AFOSkillCard(
        skill_id="skill_002_ultimate_rag",
        name="Ultimate RAG (Hybrid CRAG + Self-RAG)",
        description="Hybrid Corrective RAG + Self-RAG implementation with Lyapunov-proven convergence",
        category=SkillCategory.RAG_SYSTEMS,
        tags=["rag", "crag", "self-rag", "hybrid", "lyapunov"],
        version="2.0.0",
        capabilities=[
            "corrective_rag",
            "self_rag",
            "lyapunov_convergence",
            "multi_hop_reasoning",
        ],
        dependencies=["openai_api", "langchain"],
        execution_mode=ExecutionMode.STREAMING,
        estimated_duration_ms=3000,
        input_schema=SkillIOSchema(
            parameters=[
                SkillParameter(
                    name="query", type="string", description="User query", required=True
                ),
                SkillParameter(
                    name="top_k",
                    type="int",
                    description="Number of documents to retrieve",
                    required=False,
                    default=5,
                    validation_rules={"min": 1, "max": 20},
                ),
            ]
        ),
        philosophy_scores=PhilosophyScore(truth=98, goodness=95, beauty=90, serenity=92),
        documentation_url="https://github.com/lofibrainwav/AFO/blob/main/afo_soul_engine/hybrid_crag_selfrag.py",
    )
    skills.append(skill_002)

    # Skill 13: Obsidian Librarian
    skill_013 = AFOSkillCard(
        skill_id="skill_013_obsidian_librarian",
        name="AFO Obsidian Librarian",
        description="Manages the Kingdom's Knowledge in Obsidian. Reads/Writes notes, and creates links.",
        category=SkillCategory.MEMORY_MANAGEMENT,
        tags=["obsidian", "knowledge", "library", "markdown", "notes"],
        version="1.0.0",
        capabilities=[
            "read_note",
            "write_note",
            "search_notes",
            "append_daily_log",
            "link_notes",
            "get_backlinks",
        ],
        dependencies=["markdown", "frontmatter"],
        execution_mode=ExecutionMode.SYNC,
        estimated_duration_ms=500,
        philosophy_scores=PhilosophyScore(truth=96, goodness=98, beauty=95, serenity=99),
    )
    skills.append(skill_013)

    # Skill 19: Hybrid GraphRAG
    skill_019 = AFOSkillCard(
        skill_id="skill_019_hybrid_graphrag",
        name="Hybrid GraphRAG",
        description="Combining Vector Search with Knowledge Graphs for deep context understanding.",
        category=SkillCategory.RAG_SYSTEMS,
        tags=["graph-rag", "knowledge-graph", "vector-search", "hybrid"],
        version="1.0.0",
        capabilities=[
            "graph_traversal",
            "entity_extraction",
            "relationship_mapping",
            "hybrid_search",
        ],
        dependencies=["neo4j", "chromadb", "langchain"],
        execution_mode=ExecutionMode.ASYNC,
        estimated_duration_ms=4000,
        philosophy_scores=PhilosophyScore(truth=97, goodness=95, beauty=92, serenity=90),
    )
    skills.append(skill_019)

    # Skill 25: Dataset Optimizer
    skill_025 = AFOSkillCard(
        skill_id="skill_025_dataset_optimizer",
        name="Dataset Optimizer",
        description="Optimizes and prunes RAG datasets for efficiency.",
        category=SkillCategory.DATA_ENGINEERING,
        tags=["dataset", "optimization", "rag", "pruning"],
        version="1.0.0",
        capabilities=["deduplicate", "compress", "prune_outdated"],
        dependencies=["pandas", "numpy"],
        execution_mode=ExecutionMode.BACKGROUND,
        estimated_duration_ms=20000,
        philosophy_scores=PhilosophyScore(truth=100, goodness=90, beauty=95, serenity=90),
    )
    skills.append(skill_025)

    # Skill 26: Vector Gardener
    skill_026 = AFOSkillCard(
        skill_id="skill_026_vector_gardener",
        name="Vector Gardener",
        description="Manages and re-indexes vector database for performance.",
        category=SkillCategory.DATA_ENGINEERING,
        tags=["vector-db", "lancedb", "reindex", "optimization"],
        version="1.0.0",
        capabilities=["reindex", "optimize_segments", "vacuum"],
        dependencies=["lancedb"],
        execution_mode=ExecutionMode.BACKGROUND,
        estimated_duration_ms=10000,
        philosophy_scores=PhilosophyScore(truth=99, goodness=90, beauty=95, serenity=95),
    )
    skills.append(skill_026)

    return skills
