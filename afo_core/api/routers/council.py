# Trinity Score: 90.0 (Established by Chancellor)
"""Council Router for AFO Kingdom (Phase 23)
Multi-Model Intelligence - 지혜의 의회 (Council of Minds)
Routes queries to multiple LLMs and cross-validates responses.
"""

import asyncio
import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from AFO.utils.standard_shield import shield

logger = logging.getLogger("AFO.Council")
router = APIRouter(prefix="/council", tags=["Council of Minds"])


class CouncilQuery(BaseModel):
    query: str
    require_consensus: bool = True
    min_agreement: float = 0.66  # 66% agreement threshold


class StrategistResponse(BaseModel):
    strategist: str
    model: str
    response: str
    confidence: float


class CouncilResponse(BaseModel):
    status: str
    consensus: bool
    unified_response: str | None = None
    strategist_responses: list[StrategistResponse]
    agreement_score: float
    requires_commander: bool = False


async def consult_jang_yeong_sil(query: str) -> StrategistResponse:
    """제갈량 (眞: Truth) - Strategic Analysis via Gemini/Local"""
    # Mock implementation - would connect to actual LLM
    await asyncio.sleep(0.1)
    return StrategistResponse(
        strategist="제갈량",
        model="gemini-2.0-flash",
        response=f"[제갈량의 분석] 기술적 관점에서 '{query}'를 검토한 결과, 논리적 타당성이 확인됩니다.",
        confidence=0.92,
    )


async def consult_yi_sun_sin(query: str) -> StrategistResponse:
    """사마의 (善: Goodness) - Risk Assessment via Claude"""
    # Mock implementation - would connect to actual LLM
    await asyncio.sleep(0.1)
    return StrategistResponse(
        strategist="사마의",
        model="claude-3.5-sonnet",
        response=f"[사마의의 검토] 안전성 관점에서 '{query}'를 평가한 결과, 리스크가 허용 범위 내입니다.",
        confidence=0.88,
    )


async def consult_shin_saimdang(query: str) -> StrategistResponse:
    """주유 (美: Beauty) - UX/Narrative via GPT"""
    # Mock implementation - would connect to actual LLM
    await asyncio.sleep(0.1)
    return StrategistResponse(
        strategist="주유",
        model="gpt-4o",
        response=f"[주유의 제안] 사용자 경험 관점에서 '{query}'를 우아하게 구현할 수 있습니다.",
        confidence=0.90,
    )


def calculate_agreement(responses: list[StrategistResponse]) -> float:
    """Calculate agreement score based on confidence and semantic similarity"""
    if not responses:
        return 0.0
    # Simple average confidence for now
    # In production, would use semantic similarity
    return sum(r.confidence for r in responses) / len(responses)


def synthesize_consensus(responses: list[StrategistResponse]) -> str:
    """Synthesize a unified response from multiple strategist inputs"""
    parts = []
    for r in responses:
        parts.append(f"• {r.strategist}: {r.response}")

    return (
        "[지혜의 의회 종합]\n"
        + "\n".join(parts)
        + "\n\n→ 3책사가 합의하여 진실(眞), 안전(善), 우아함(美)을 모두 확보했습니다."
    )


@shield(pillar="美")
@router.post("/deliberate", response_model=CouncilResponse)
async def deliberate(query: CouncilQuery) -> CouncilResponse:
    """Send query to the Council of Minds for multi-model deliberation."""
    logger.info(f"🧠 Council Deliberation Requested: {query.query}")

    # Query all strategists in parallel
    responses = list(
        await asyncio.gather(
            consult_jang_yeong_sil(query.query),
            consult_yi_sun_sin(query.query),
            consult_shin_saimdang(query.query),
        )
    )

    # Calculate agreement
    agreement_score = calculate_agreement(responses)
    consensus_reached = agreement_score >= query.min_agreement

    # Determine if Commander review is needed
    requires_commander = not consensus_reached if query.require_consensus else False

    # Synthesize unified response if consensus
    unified_response = synthesize_consensus(responses) if consensus_reached else None

    return CouncilResponse(
        status="consensus" if consensus_reached else "disagreement",
        consensus=consensus_reached,
        unified_response=unified_response,
        strategist_responses=responses,
        agreement_score=agreement_score,
        requires_commander=requires_commander,
    )


@shield(pillar="美")
@router.get("/health")
async def council_health() -> dict[str, Any]:
    """Check Council of Minds health."""
    return {
        "status": "healthy",
        "strategists": [
            {"name": "제갈량", "pillar": "眞", "model": "gemini-2.0-flash"},
            {"name": "사마의", "pillar": "善", "model": "claude-3.5-sonnet"},
            {"name": "주유", "pillar": "美", "model": "gpt-4o"},
        ],
        "consensus_threshold": 0.66,
    }
