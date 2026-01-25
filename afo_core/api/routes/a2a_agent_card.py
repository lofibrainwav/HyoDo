# Trinity Score: 92.0 (2026 A2A Implementation)
"""
A2A Agent Cards Endpoint (Google A2A Protocol 2025)

/.well-known/agent.json 엔드포인트로 Agent Card 제공
MCP + A2A 통합으로 2026 병렬 협업 지원
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["A2A Protocol"])


class AgentSkill(BaseModel):
    """A2A Agent Skill definition"""

    id: str
    name: str
    description: str


class AgentCard(BaseModel):
    """A2A Agent Card (Google A2A Protocol 2025 spec)"""

    name: str = "AFO Kingdom Chancellor Agent"
    description: str = "眞善美孝永 철학 기반 중앙 의사결정 엔진 (AFO Kingdom Soul Engine)"
    version: str = "v2.5"
    capabilities: list[str] = ["task_management", "streaming", "multi_turn"]
    skills: list[AgentSkill] = []
    endpoint: str = "http://localhost:8010/api/a2a"
    authentication: dict[str, Any] = {"type": "api_key", "header": "X-API-Key"}


def _get_dynamic_skills() -> list[AgentSkill]:
    """Dynamically load skills from registry (19 Skills)"""
    # Core skills (always available)
    core_skills = [
        AgentSkill(
            id="chancellor_invoke",
            name="승상 호출",
            description="Trinity Score 기반 라우팅 및 철학 평가",
        ),
        AgentSkill(
            id="trinity_evaluate",
            name="철학 평가",
            description="眞善美孝永 5대 가치 점수 계산",
        ),
        AgentSkill(
            id="health_check",
            name="건강 체크",
            description="시스템 상태 및 오장육부 모니터링",
        ),
        AgentSkill(
            id="multi_agent_orchestration",
            name="병렬 협업",
            description="Claude/Codex/Ollama 멀티 에이전트 조율",
        ),
    ]

    # Try to load from Skills Registry
    try:
        from afo_skills_registry import register_core_skills

        registry = register_core_skills()
        for skill in registry.list_all():
            core_skills.append(
                AgentSkill(id=skill.skill_id, name=skill.name, description=skill.description)
            )
    except ImportError:
        logger.warning("Skills Registry not available, using core skills only")
    except Exception as e:
        logger.warning(f"Failed to load skills from registry: {e}")

    return core_skills


@router.get("/.well-known/agent.json")
async def get_agent_card() -> JSONResponse:
    """
    A2A Agent Card Endpoint

    Returns Agent Card following Google A2A Protocol (2025) spec.
    Enables discovery and interoperability with external agents.
    """
    try:
        dynamic_skills = _get_dynamic_skills()
        card = AgentCard(skills=dynamic_skills)

        logger.info(f"A2A Agent Card Union[served, Skills]: {len(dynamic_skills)}")
        return JSONResponse(content=card.model_dump())

    except Exception as e:
        logger.error(f"A2A Agent Card failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Agent Card unavailable. Kingdom stability maintained (孝 100%).",
        ) from e


@router.get("/api/a2a/status")
async def a2a_status() -> dict[str, Any]:
    """A2A Protocol Status endpoint"""
    return {
        "protocol": "a2a",
        "version": "2025-04",
        "status": "ready",
        "skills_count": len(_get_dynamic_skills()),
        "capabilities": ["task_management", "streaming", "multi_turn"],
    }
