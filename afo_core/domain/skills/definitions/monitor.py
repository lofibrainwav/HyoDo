from __future__ import annotations

from ..models import (
    AFOSkillCard,
    ExecutionMode,
    PhilosophyScore,
    SkillCategory,
)


def get_monitor_skills() -> list[AFOSkillCard]:
    """HEALTH_MONITORING, DEVOPS & SUSTAINABILITY Skills"""
    skills = []

    # Skill 3: 11-Organ Health Monitor
    skill_003 = AFOSkillCard(
        skill_id="skill_003_health_monitor",
        name="11-Organ Health Monitor",
        description="Monitors 11 critical AFO system organs (五臟六腑) and generates health reports",
        category=SkillCategory.HEALTH_MONITORING,
        tags=["health", "monitoring", "五臟六腑", "diagnostics"],
        version="1.5.0",
        capabilities=[
            "redis_health_check",
            "postgresql_health_check",
            "chromadb_health_check",
            "api_server_health_check",
            "n8n_health_check",
            "comprehensive_report",
        ],
        dependencies=["redis", "postgresql", "docker"],
        execution_mode=ExecutionMode.SYNC,
        estimated_duration_ms=500,
        philosophy_scores=PhilosophyScore(truth=100, goodness=100, beauty=95, serenity=100),
        documentation_url="https://github.com/lofibrainwav/AFO/blob/main/afo_soul_engine/auto_health_monitor.py",
    )
    skills.append(skill_003)

    # Skill 11: Verify Full Stack
    skill_011 = AFOSkillCard(
        skill_id="skill_011_verify_full_stack",
        name="Verify Full Stack Integrity",
        description="Comprehensive system health check for all AFO components (DB, Redis, API, Dashboard)",
        category=SkillCategory.HEALTH_MONITORING,
        tags=["verification", "health", "fullstack", "system"],
        version="1.0.0",
        capabilities=[
            "full_stack_verification",
            "trinity_score_check",
            "component_status_report",
        ],
        dependencies=["redis", "postgresql", "docker"],
        execution_mode=ExecutionMode.ASYNC,
        estimated_duration_ms=2000,
        philosophy_scores=PhilosophyScore(truth=99, goodness=98, beauty=90, serenity=95),
    )
    skills.append(skill_011)

    # Skill 17: Data Pipeline
    skill_017 = AFOSkillCard(
        skill_id="skill_017_data_pipeline",
        name="Real-time Data Pipeline",
        description="Real-time collection of system friction, complexity, and metrics.",
        category=SkillCategory.HEALTH_MONITORING,
        tags=["data-pipeline", "real-time", "friction", "complexity", "metrics"],
        version="1.0.0",
        capabilities=[
            "ingest_logs",
            "calculate_friction",
            "track_complexity",
            "stream_metrics",
        ],
        dependencies=["kafka", "redis", "pandas"],
        execution_mode=ExecutionMode.STREAMING,
        estimated_duration_ms=100,
        philosophy_scores=PhilosophyScore(truth=98, goodness=95, beauty=90, serenity=97),
    )
    skills.append(skill_017)

    # Skill 18: Docker Recovery (Sima Yi)
    skill_018 = AFOSkillCard(
        skill_id="skill_018_docker_recovery",
        name="Docker Auto-Recovery (Sima Yi)",
        description="Autonomous health monitoring and self-healing system.",
        category=SkillCategory.HEALTH_MONITORING,
        tags=["docker", "recovery", "self-healing", "sima-yi", "uptime"],
        version="1.0.0",
        capabilities=[
            "monitor_containers",
            "restart_container",
            "detect_deadlock",
            "analyze_logs",
        ],
        dependencies=["docker", "ai-analysis"],
        execution_mode=ExecutionMode.BACKGROUND,
        estimated_duration_ms=5000,
        philosophy_scores=PhilosophyScore(truth=99, goodness=100, beauty=85, serenity=100),
    )
    skills.append(skill_018)

    # Skill 27: Latency Profiler
    skill_027 = AFOSkillCard(
        skill_id="skill_027_latency_profiler",
        name="Latency Profiler",
        description="Analyzes system latency and identifies bottlenecks.",
        category=SkillCategory.DEVOPS,
        tags=["latency", "profiling", "performance", "bottleneck"],
        version="1.0.0",
        capabilities=["profile_request", "analyze_trace"],
        dependencies=["pyinstrument"],
        execution_mode=ExecutionMode.SYNC,
        estimated_duration_ms=1000,
        philosophy_scores=PhilosophyScore(truth=100, goodness=85, beauty=90, serenity=90),
    )
    skills.append(skill_027)

    # Skill 28: Energy Monitor
    skill_028 = AFOSkillCard(
        skill_id="skill_028_energy_monitor",
        name="Energy Monitor",
        description="Estimates computational carbon footprint and energy usage.",
        category=SkillCategory.SUSTAINABILITY,
        tags=["energy", "carbon", "sustainability", "green-ai"],
        version="1.0.0",
        capabilities=["calc_energy", "report_carbon"],
        dependencies=["codecarbon-lite"],
        execution_mode=ExecutionMode.ASYNC,
        estimated_duration_ms=500,
        philosophy_scores=PhilosophyScore(truth=95, goodness=100, beauty=90, serenity=100),
    )
    skills.append(skill_028)

    return skills
