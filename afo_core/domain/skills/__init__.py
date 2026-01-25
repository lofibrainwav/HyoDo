# Trinity Score: 95.0 (Established by Chancellor)
"""
AFO Domain Skills Package (domain/skills/__init__.py)

Strangler Fig Facade for the Skill Registry system.
"""

from .core import register_core_skills
from .models import (
    AFOSkillCard,
    ExecutionMode,
    MCPConfig,
    PhilosophyScore,
    SkillCategory,
    SkillExecutionRequest,
    SkillExecutionResult,
    SkillIOSchema,
    SkillParameter,
    SkillStatus,
)
from .registry import SkillFilterParams, SkillRegistry

__all__ = [
    "AFOSkillCard",
    "ExecutionMode",
    "MCPConfig",
    "PhilosophyScore",
    "SkillCategory",
    "SkillExecutionRequest",
    "SkillExecutionResult",
    "SkillIOSchema",
    "SkillParameter",
    "SkillStatus",
    "SkillFilterParams",
    "SkillRegistry",
    "register_core_skills",
]
