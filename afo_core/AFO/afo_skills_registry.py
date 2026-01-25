# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO Skills Registry Compatibility Layer (AFO/afo_skills_registry.py)

This module provides backward compatibility for code that imports from AFO.afo_skills_registry.
The actual implementation is in domain/skills/.
"""

from domain.skills.core import register_core_skills
from domain.skills.models import (
    AFOSkillCard,
    ExecutionMode,
    PhilosophyScore,
    SkillCategory,
    SkillStatus,
)
from domain.skills.registry import SkillFilterParams, SkillRegistry

# Global singleton instance for backward compatibility
skills_registry = register_core_skills()

__all__ = [
    "AFOSkillCard",
    "ExecutionMode",
    "PhilosophyScore",
    "SkillCategory",
    "SkillFilterParams",
    "SkillRegistry",
    "SkillStatus",
    "register_core_skills",
    "skills_registry",
]
