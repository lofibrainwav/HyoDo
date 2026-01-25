from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from .models import AFOSkillCard, ExecutionMode, MCPConfig, SkillCategory, SkillStatus

# Trinity Score: 95.0 (Established by Chancellor)
"""
AFO Skill Registry (domain/skills/registry.py)

Centralized management and filtering of AFO skills.
Phase 2: Added persistence mechanism for MCP configurations.
"""

logger = logging.getLogger(__name__)


# = ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# Filter Models
# = ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class SkillFilterParams(BaseModel):
    """
    Query parameters for filtering skills

    Uses FastAPI 0.115+ Pydantic Query Parameter Models
    """

    category: SkillCategory | None = Field(default=None, description="Filter by category")
    status: SkillStatus | None = Field(default=None, description="Filter by status")
    tags: list[str] | None = Field(default=None, description="Filter by tags (OR logic)")
    search: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Search in name/description",
    )
    min_philosophy_avg: int | None = Field(
        default=None, ge=0, le=100, description="Minimum average philosophy score"
    )
    execution_mode: ExecutionMode | None = Field(
        default=None, description="Filter by execution mode"
    )
    limit: int = Field(default=100, ge=1, le=500, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


# = ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# Skill Registry (Singleton)
# = ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class SkillRegistry:
    """
    Central skill registry for AFO system

    Pattern: Singleton with in-memory storage + optional persistence
    """

    _instance = None
    _skills: ClassVar[dict[str, AFOSkillCard]] = {}

    def __new__(cls) -> Any:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, skill: AFOSkillCard) -> bool:
        """Register a skill"""
        try:
            if skill.skill_id in self._skills:
                # Update existing skill
                self._skills[skill.skill_id] = skill
                return False  # Not a new registration
            else:
                self._skills[skill.skill_id] = skill
                return True  # New registration
        except Exception:
            return False

    def get(self, skill_id: str) -> AFOSkillCard | None:
        """Get skill by ID"""
        try:
            return self._skills.get(skill_id)
        except Exception:
            return None

    def list_all(self) -> list[AFOSkillCard]:
        """List all skills"""
        try:
            return list(self._skills.values())
        except Exception:
            return []

    def filter(self, params: SkillFilterParams) -> list[AFOSkillCard]:
        """Filter skills by parameters"""
        try:
            results = self.list_all()

            # Category filter
            if params.category:
                results = [s for s in results if s.category == params.category]

            # Status filter
            if params.status:
                results = [s for s in results if s.status == params.status]

            # Tags filter (OR logic)
            if params.tags:
                tag_set = {tag.lower() for tag in params.tags}
                results = [s for s in results if any(tag in tag_set for tag in s.tags)]

            # Search filter
            if params.search:
                search_lower = params.search.lower()
                results = [
                    s
                    for s in results
                    if search_lower in s.name.lower() or search_lower in s.description.lower()
                ]

            # Philosophy score filter
            if params.min_philosophy_avg:
                results = [
                    s for s in results if s.philosophy_scores.average >= params.min_philosophy_avg
                ]

            # Execution mode filter
            if params.execution_mode:
                results = [s for s in results if s.execution_mode == params.execution_mode]

            # Pagination
            start = params.offset
            end = params.offset + params.limit
            return results[start:end]
        except Exception as e:
            print(f"⚠️ Skill filtering failed: {e}")
            return []

    def get_categories(self) -> list[str]:
        """Get all unique categories"""
        try:
            return [cat.value for cat in SkillCategory]
        except Exception:
            return []

    def get_category_stats(self) -> dict[str, int]:
        """Get category statistics (category -> count)"""
        try:
            stats: dict[str, int] = {}
            for skill in self._skills.values():
                category = skill.category.value
                if category not in stats:
                    stats[category] = 0
                stats[category] += 1
            return stats
        except Exception:
            return {}

    def count(self) -> int:
        """Total skill count"""
        return len(self._skills)

    def clear(self) -> None:
        """Clear all skills (for testing)"""
        self._skills.clear()

    @property
    def skills(self) -> dict[str, AFOSkillCard]:
        """Expose registry storage for backwards compatibility"""
        return self._skills

    # =========================================================================
    # Persistence Methods (Phase 2: MCP Configuration Persistence)
    # =========================================================================

    def save_mcp_configs(self, filepath: str | Path | None = None) -> bool:
        """
        Save MCP configurations to JSON file for persistence.

        Args:
            filepath: Target file path. Defaults to docs/skills_registry_mcp_tools.json

        Returns:
            True if save successful, False otherwise
        """
        if filepath is None:
            # Default path relative to project root (AFO_Kingdom/docs/)
            # Path: domain/skills/registry.py -> packages/afo-core/ -> packages/ -> AFO_Kingdom/
            filepath = (
                Path(__file__).parent.parent.parent.parent.parent
                / "docs"
                / "skills_registry_mcp_tools.json"
            )

        filepath = Path(filepath)

        try:
            mcp_data = []
            for skill_id, skill in self._skills.items():
                if skill.mcp_config is not None:
                    mcp_entry = {
                        "skill_id": skill_id,
                        "name": skill.name,
                        "category": skill.category.value,
                        "mcp_config": skill.mcp_config.model_dump(mode="json"),
                        "philosophy_avg": skill.philosophy_scores.average,
                        "status": skill.status.value,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                    mcp_data.append(mcp_entry)

            # Sort by philosophy score (highest first)
            mcp_data.sort(key=lambda x: x["philosophy_avg"], reverse=True)

            # Ensure directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(mcp_data, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Saved {len(mcp_data)} MCP configurations to {filepath}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to save MCP configs: {e}")
            return False

    def load_mcp_configs(self, filepath: str | Path | None = None) -> int:
        """
        Load MCP configurations from JSON file and apply to registered skills.

        Args:
            filepath: Source file path. Defaults to docs/skills_registry_mcp_tools.json

        Returns:
            Number of MCP configs successfully applied
        """
        if filepath is None:
            # Default path relative to project root (AFO_Kingdom/docs/)
            filepath = (
                Path(__file__).parent.parent.parent.parent.parent
                / "docs"
                / "skills_registry_mcp_tools.json"
            )

        filepath = Path(filepath)

        if not filepath.exists():
            logger.warning(f"⚠️ MCP config file not found: {filepath}")
            return 0

        try:
            with open(filepath, encoding="utf-8") as f:
                mcp_data = json.load(f)

            applied_count = 0
            for entry in mcp_data:
                skill_id = entry.get("skill_id")
                mcp_config_data = entry.get("mcp_config")

                if skill_id and mcp_config_data and skill_id in self._skills:
                    skill = self._skills[skill_id]
                    # Create MCPConfig from loaded data
                    skill.mcp_config = MCPConfig(**mcp_config_data)
                    applied_count += 1
                    logger.debug(f"  Applied MCP config to: {skill_id}")

            logger.info(
                f"✅ Loaded {applied_count}/{len(mcp_data)} MCP configurations from {filepath}"
            )
            return applied_count

        except Exception as e:
            logger.error(f"❌ Failed to load MCP configs: {e}")
            return 0

    def enable_mcp_for_skill(
        self,
        skill_id: str,
        capabilities: list[str] | None = None,
        mcp_server_url: str | None = None,
        auto_save: bool = True,
    ) -> bool:
        """
        Enable MCP for a specific skill and optionally persist.

        Args:
            skill_id: The skill to enable MCP for
            capabilities: MCP capabilities (defaults to ['tools'])
            mcp_server_url: Optional MCP server URL
            auto_save: Whether to auto-save to file after enabling

        Returns:
            True if successful, False otherwise
        """
        skill = self._skills.get(skill_id)
        if not skill:
            logger.warning(f"⚠️ Skill not found: {skill_id}")
            return False

        try:
            skill.mcp_config = MCPConfig(
                capabilities=capabilities or ["tools"],
                mcp_server_url=mcp_server_url,
                mcp_version="2025.1",
                authentication_required=False,
            )

            if auto_save:
                self.save_mcp_configs()

            logger.info(f"✅ MCP enabled for skill: {skill_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to enable MCP for {skill_id}: {e}")
            return False

    def get_mcp_enabled_skills(self) -> list[AFOSkillCard]:
        """Get all skills with MCP enabled."""
        return [s for s in self._skills.values() if s.mcp_config is not None]

    def get_mcp_stats(self) -> dict[str, Any]:
        """Get MCP enablement statistics."""
        total = len(self._skills)
        mcp_enabled = len(self.get_mcp_enabled_skills())

        return {
            "total_skills": total,
            "mcp_enabled": mcp_enabled,
            "mcp_percentage": round((mcp_enabled / total * 100) if total > 0 else 0, 1),
            "by_category": self._get_mcp_stats_by_category(),
        }

    def _get_mcp_stats_by_category(self) -> dict[str, dict[str, int]]:
        """Get MCP stats grouped by category."""
        stats: dict[str, dict[str, int]] = {}

        for skill in self._skills.values():
            cat = skill.category.value
            if cat not in stats:
                stats[cat] = {"total": 0, "mcp_enabled": 0}

            stats[cat]["total"] += 1
            if skill.mcp_config is not None:
                stats[cat]["mcp_enabled"] += 1

        return stats
