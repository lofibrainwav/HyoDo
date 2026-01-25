from __future__ import annotations

from ..models import (
    AFOSkillCard,
    ExecutionMode,
    PhilosophyScore,
    SkillCategory,
)


def get_security_skills() -> list[AFOSkillCard]:
    """SECURITY & GOVERNANCE Skills"""
    skills = []

    # Skill 20: Auto Security Agent
    skill_020 = AFOSkillCard(
        skill_id="skill_020_auto_security",
        name="Auto Security Agent",
        description="Automated security patching and vulnerability scanning using Bandit.",
        category=SkillCategory.SECURITY,
        tags=["security", "bandit", "auto-patch", "vulnerability"],
        version="1.0.0",
        capabilities=["security_scan", "auto_patch", "vulnerability_report"],
        dependencies=["bandit", "safety"],
        execution_mode=ExecutionMode.ASYNC,
        estimated_duration_ms=10000,
        philosophy_scores=PhilosophyScore(truth=99, goodness=100, beauty=85, serenity=95),
    )
    skills.append(skill_020)

    # Skill 22: Dependency Audit
    skill_022 = AFOSkillCard(
        skill_id="skill_022_dependency_audit",
        name="Dependency Audit",
        description="Scans Python and Node.js dependencies for vulnerabilities.",
        category=SkillCategory.SECURITY,
        tags=["dependency", "audit", "cve", "npm", "pip"],
        version="1.0.0",
        capabilities=["scan_dependencies", "check_cve"],
        dependencies=["pip-audit", "npm-audit"],
        execution_mode=ExecutionMode.BACKGROUND,
        estimated_duration_ms=12000,
        philosophy_scores=PhilosophyScore(truth=98, goodness=100, beauty=80, serenity=95),
    )
    skills.append(skill_022)

    # Skill 23: Secret Guardian
    skill_023 = AFOSkillCard(
        skill_id="skill_023_secret_guardian",
        name="Secret Guardian",
        description="Detects hardcoded secrets, keys, and tokens in the codebase.",
        category=SkillCategory.SECURITY,
        tags=["secrets", "leak-detection", "security", "keys"],
        version="1.0.0",
        capabilities=["scan_secrets", "verify_git_history"],
        dependencies=["trufflehog-lite"],
        execution_mode=ExecutionMode.ASYNC,
        estimated_duration_ms=5000,
        philosophy_scores=PhilosophyScore(truth=99, goodness=100, beauty=85, serenity=98),
    )
    skills.append(skill_023)

    # Skill 24: Container Sentry
    skill_024 = AFOSkillCard(
        skill_id="skill_024_container_sentry",
        name="Container Sentry",
        description="Security scanning for Docker containers and images.",
        category=SkillCategory.SECURITY,
        tags=["docker", "container", "security", "image-scan"],
        version="1.0.0",
        capabilities=["scan_image", "check_config"],
        dependencies=["trivy-lite"],
        execution_mode=ExecutionMode.BACKGROUND,
        estimated_duration_ms=15000,
        philosophy_scores=PhilosophyScore(truth=97, goodness=100, beauty=80, serenity=95),
    )
    skills.append(skill_024)

    # Skill 30: Chancellor Monitor
    skill_030 = AFOSkillCard(
        skill_id="skill_030_chancellor_monitor",
        name="Chancellor Monitor",
        description="Ensures all actions comply with AFO Constitution.",
        category=SkillCategory.GOVERNANCE,
        tags=["governance", "compliance", "constitution", "monitor"],
        version="1.0.0",
        capabilities=["audit_action", "verify_compliance", "log_verdict"],
        dependencies=["chancellor-core"],
        execution_mode=ExecutionMode.SYNC,
        estimated_duration_ms=200,
        philosophy_scores=PhilosophyScore(truth=100, goodness=100, beauty=95, serenity=100),
    )
    skills.append(skill_030)

    return skills
