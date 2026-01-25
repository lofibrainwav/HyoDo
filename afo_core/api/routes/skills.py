from __future__ import annotations

import json
import logging
from typing import Annotated, Any, cast

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from AFO.afo_skills_registry import (
    AFOSkillCard,
    SkillExecutionResult,
    SkillFilterParams,
    SkillRegistry,
    register_core_skills,
)
from services.health_service import get_comprehensive_health

# Trinity Score: 95.0 (New Component)
"""
AFO Skills Router (아름다운 코드 적용).

AFO Skill Registry를 외부로 노출하는 API 라우터.
眞善美孝 철학을 준수하며, SkillRegistry Singleton을 통해 데이터를 제공합니다.

Author: AFO Kingdom Development Team
Date: 2025-12-25
Version: 1.0.0
"""


# Configure logging
logger = logging.getLogger(__name__)


# Initialize Router
router = APIRouter(prefix="/api/skills", tags=["Skills"])


# Dependency to get registry (Dependency Injection pattern)
def get_registry() -> SkillRegistry:
    """Get the SkillRegistry instance (Singleton)."""
    registry = SkillRegistry()
    # Ensure core skills are registered (handle case where module-import registered 1 manual skill)
    if registry.count() < 5:
        logger.info("Initializing SkillRegistry with core skills...")
        register_core_skills()
    return registry


@router.post("/execute", response_model=SkillExecutionResult)
async def execute_skill(
    registry: Annotated[SkillRegistry, Depends(get_registry)],
    skill_id: Annotated[str, Body(..., embed=True)],
    parameters: Annotated[dict[str, Any] | None, Body(embed=True)] = None,
    dry_run: Annotated[bool, Body(embed=True)] = False,
) -> SkillExecutionResult:
    """
    Execute a skill.

    Trinity Score: 眞 (Truth) - Real execution interface.

    Raises:
        HTTPException: If skill not found or execution fails.
    """
    skill = registry.get(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")

    logger.info("Executing skill: %s (Dry Run: %s)", skill_id, dry_run)

    # In a real implementation, this would call the SkillExecutor service.
    # For Phase 2, we simulate successful execution/dry-run.

    # Real Execution Logic for Skill 003
    if skill_id == "skill_003_health_monitor":
        try:
            health_data = await get_comprehensive_health()
            json_content = json.dumps(health_data)  # Prepare JSON string for 'content' field
            return SkillExecutionResult(
                skill_id=skill_id,
                status="completed",
                result={
                    "message": "Health Check Complete",
                    "content": [{"type": "text", "text": json_content}],
                    "data": health_data,
                },
                dry_run=dry_run,
            )
        except Exception as e:
            logger.exception("Health check failed")
            raise HTTPException(
                status_code=500,
                detail="Agent Card unavailable. Kingdom stability maintained (孝 100%).",
            ) from e

    return SkillExecutionResult(
        skill_id=skill_id,
        status="completed" if not dry_run else "dry_run_success",
        result={"message": f"Skill {skill.name} executed successfully (Simulation)"},
        dry_run=dry_run,
    )


@router.get("/", response_model=dict[str, Any])
async def list_skills(
    registry: Annotated[SkillRegistry, Depends(get_registry)],
    category: str | None = None,
    search: str | None = None,
    min_philosophy_avg: Annotated[int | None, Query(ge=0, le=100)] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List all available skills with filtering.

    Trinity Score: 眞 (Truth) - Accurate skill listing.

    Raises:
        HTTPException: If listing fails.
    """
    try:
        # Build filter params
        params = SkillFilterParams(
            category=cast("Any", category),
            search=search,
            min_philosophy_avg=min_philosophy_avg,
            limit=limit,
            offset=offset,
        )

        # Query registry
        skills = registry.filter(params)
        total = registry.count()

        return {
            "skills": skills,
            "total": total,
            "count": len(skills),
            "categories": registry.get_categories(),
        }
    except Exception as e:
        logger.exception("Failed to list skills")
        raise HTTPException(status_code=500, detail="Internal Server Error") from e


@router.get("/list", response_model=dict[str, Any])
async def list_skills_alias(
    registry: Annotated[SkillRegistry, Depends(get_registry)],
    category: str | None = None,
    search: str | None = None,
    min_philosophy_avg: Annotated[int | None, Query(ge=0, le=100)] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Alias for /api/skills/ - List all available skills with filtering.

    Trinity Score: 善 (Serenity) - 프론트엔드 호환성 제공.
    """
    return await list_skills(
        registry=registry,
        category=category,
        search=search,
        min_philosophy_avg=min_philosophy_avg,
        limit=limit,
        offset=offset,
    )


@router.get("/stats/categories", response_model=dict[str, int])
async def get_category_stats(
    registry: Annotated[SkillRegistry, Depends(get_registry)],
) -> dict[str, int]:
    """Get statistics by category."""
    return registry.get_category_stats()


@router.get("/health", response_model=dict[str, Any])
async def check_health() -> dict[str, Any]:
    """Check health of the Skills API."""
    return {"status": "healthy", "service": "AFO Skills API"}


@router.get("/{skill_id}", response_model=AFOSkillCard)
async def get_skill(
    registry: Annotated[SkillRegistry, Depends(get_registry)],
    skill_id: str,
) -> AFOSkillCard:
    """
    Get a single skill by ID.

    Raises:
        HTTPException: If skill not found.
    """
    skill = registry.get(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
    return skill
