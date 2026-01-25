from __future__ import annotations

from .definitions import (
    get_analysis_skills,
    get_automation_skills,
    get_context7_intelligence_skills,
    get_creative_skills,
    get_governance_skills,
    get_integration_skills,
    get_monitor_skills,
    get_rag_skills,
    get_security_skills,
)
from .registry import SkillRegistry

# Trinity Score: 95.0 (Established by Chancellor)
"""
AFO Core Skills (domain/skills/core.py)

Registry of built-in skills for the AFO Kingdom.
Modularized (Phase 75) to `definitions/` package.
"""


def register_core_skills() -> SkillRegistry:
    """Register AFO's core built-in skills and load persisted MCP configurations"""
    registry = SkillRegistry()

    # Aggregate all skills from definition modules
    core_skills = []
    core_skills.extend(get_automation_skills())
    core_skills.extend(get_rag_skills())
    core_skills.extend(get_monitor_skills())
    core_skills.extend(get_security_skills())
    core_skills.extend(get_analysis_skills())
    core_skills.extend(get_integration_skills())
    core_skills.extend(get_creative_skills())
    core_skills.extend(get_context7_intelligence_skills())
    core_skills.extend(get_governance_skills())

    for skill in core_skills:
        registry.register(skill)

    # Phase 2: Auto-load persisted MCP configurations
    mcp_loaded = registry.load_mcp_configs()
    if mcp_loaded > 0:
        print(f"✅ Skills Registry SSOT 복구 성공 ({mcp_loaded} MCP configs loaded)")
    else:
        print("✅ Skills Registry SSOT 복구 성공")

    return registry
