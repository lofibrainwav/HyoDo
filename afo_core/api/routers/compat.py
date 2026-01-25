# Trinity Score: 90.0 (Established by Chancellor)
"""
Strangler Fig Compatibility Router
Phase 15: The Grok Singularity

Provides API endpoints for React components to consume HTML dashboard data.
Implements the Strangler Fig pattern for gradual migration from HTML to React.
"""

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from AFO.utils.standard_shield import shield

# Lazy imports to avoid circular dependency with AFO.api.compat


def _get_compat_functions() -> dict[str, Any]:
    """Lazy import to avoid circular imports."""
    from AFO.api.compat import (
        get_personas_list,
        get_philosophy_pillars,
        get_project_stats,
        get_royal_constitution,
        get_service_ports,
        get_system_architecture,
    )

    return {
        "get_personas_list": get_personas_list,
        "get_philosophy_pillars": get_philosophy_pillars,
        "get_project_stats": get_project_stats,
        "get_royal_constitution": get_royal_constitution,
        "get_service_ports": get_service_ports,
        "get_system_architecture": get_system_architecture,
    }


router = APIRouter(prefix="/compat", tags=["compat"])


# Pydantic models for API responses
class PersonaResponse(BaseModel):
    name: str
    code: str
    role: str


class PortResponse(BaseModel):
    service: str
    port: str
    description: str


class RuleResponse(BaseModel):
    id: int
    name: str
    principle: str
    code: str = ""


class BookResponse(BaseModel):
    title: str
    weight: str
    rules: list[RuleResponse]


class PhilosophyResponse(BaseModel):
    pillars: list[dict[str, Any]]
    trinity_formula: str
    auto_run_condition: str


@shield(pillar="善")
@router.get("/personas", response_model=list[PersonaResponse])
async def get_personas():
    """
    Get personas data from HTML dashboard.
    Used by RoyalLibrary React component.
    """
    try:
        funcs = _get_compat_functions()
        data = funcs["get_personas_list"]()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load personas: {e!s}")


@shield(pillar="善")
@router.get("/ports", response_model=list[PortResponse])
async def get_ports():
    """
    Get service ports data from HTML dashboard.
    Used by RoyalLibrary React component.
    """
    try:
        funcs = _get_compat_functions()
        data = funcs["get_service_ports"]()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load ports: {e!s}")


@shield(pillar="善")
@router.get("/royal-rules", response_model=list[BookResponse])
async def get_royal_rules():
    """
    Get Royal Constitution rules from HTML dashboard.
    Used by RoyalLibrary React component.
    """
    try:
        funcs = _get_compat_functions()
        data = funcs["get_royal_constitution"]()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load royal rules: {e!s}")


@shield(pillar="善")
@router.get("/philosophy", response_model=PhilosophyResponse)
async def get_philosophy():
    """
    Get 5 Pillars philosophy data from HTML dashboard.
    Used by Trinity components.
    """
    try:
        funcs = _get_compat_functions()
        data = funcs["get_philosophy_pillars"]()
        return PhilosophyResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load philosophy: {e!s}")


@shield(pillar="善")
@router.get("/architecture")
async def get_architecture():
    """
    Get system architecture data from HTML dashboard.
    Used by architecture visualization components.
    """
    try:
        funcs = _get_compat_functions()
        data = funcs["get_system_architecture"]()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load architecture: {e!s}")


@shield(pillar="善")
@router.get("/stats")
async def get_stats():
    """
    Get project statistics from HTML dashboard.
    Used by dashboard widgets.
    """
    try:
        funcs = _get_compat_functions()
        data = funcs["get_project_stats"]()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load stats: {e!s}")


@shield(pillar="善")
@router.get("/health")
async def compat_health():
    """
    Health check for compat router.
    """
    return {
        "status": "healthy",
        "service": "strangler-fig-compat",
        "pattern": "HTML → React Migration",
        "endpoints": [
            "/api/compat/personas",
            "/api/compat/ports",
            "/api/compat/royal-rules",
            "/api/compat/philosophy",
            "/api/compat/architecture",
            "/api/compat/stats",
        ],
    }
