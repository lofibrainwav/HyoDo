# Trinity Score: 90.0 (Established by Chancellor)
"""Trinity Policy Router for AFO Kingdom
Trinity 정책 관리 API.

Manages Trinity Score calculation policies, thresholds, and governance rules.
Implements the 眞善美孝永 5-pillar philosophy configuration.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("AFO.TrinityPolicy")
router = APIRouter(prefix="/api/trinity/policy", tags=["Trinity Policy"])


# --- Pydantic Models ---


class PillarConfig(BaseModel):
    """Configuration for a single pillar."""

    id: str
    name: str
    chinese: str
    weight: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(default=70.0, ge=0.0, le=100.0)
    description: str


class TrinityPolicyConfig(BaseModel):
    """Complete Trinity policy configuration."""

    version: str = "2025.1"
    pillars: list[PillarConfig]
    auto_run_threshold: float = 90.0
    risk_threshold: float = 10.0
    formula: str = "Trinity Score = 0.35×眞 + 0.35×善 + 0.20×美 + 0.08×孝 + 0.02×永"
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class UpdatePillarRequest(BaseModel):
    """Request to update a pillar's configuration."""

    pillar_id: str
    weight: float | None = None
    threshold: float | None = None


class PolicyEvaluationRequest(BaseModel):
    """Request to evaluate an action against policies."""

    action_type: str
    risk_score: float
    pillar_scores: dict[str, float]


class PolicyEvaluationResult(BaseModel):
    """Result of policy evaluation."""

    allowed: bool
    trinity_score: float
    auto_run_eligible: bool
    violations: list[str]
    recommendations: list[str]


# --- Default Policy Configuration ---
_current_policy = TrinityPolicyConfig(
    pillars=[
        PillarConfig(
            id="truth",
            name="Truth",
            chinese="眞",
            weight=0.35,
            threshold=70.0,
            description="기술적 확실성 - 제갈량",
        ),
        PillarConfig(
            id="goodness",
            name="Goodness",
            chinese="善",
            weight=0.35,
            threshold=70.0,
            description="윤리·안정성 - 사마의",
        ),
        PillarConfig(
            id="beauty",
            name="Beauty",
            chinese="美",
            weight=0.20,
            threshold=60.0,
            description="단순함·우아함 - 주유",
        ),
        PillarConfig(
            id="serenity",
            name="Serenity",
            chinese="孝",
            weight=0.08,
            threshold=50.0,
            description="평온·연속성 - 승상",
        ),
        PillarConfig(
            id="eternity",
            name="Eternity",
            chinese="永",
            weight=0.02,
            threshold=50.0,
            description="영속성·레거시 - 승상",
        ),
    ],
)


# --- Helper Functions ---


def calculate_trinity_score(pillar_scores: dict[str, float]) -> float:
    """Calculate Trinity Score from pillar scores."""
    total = 0.0
    for pillar in _current_policy.pillars:
        score = pillar_scores.get(pillar.id, 0.0)
        total += score * pillar.weight
    return round(total, 2)


# --- Endpoints ---


@router.get("/config", response_model=TrinityPolicyConfig)
async def get_policy_config() -> TrinityPolicyConfig:
    """Get current Trinity policy configuration."""
    return _current_policy


@router.get("/pillars")
async def get_pillars() -> dict[str, Any]:
    """Get all pillar configurations."""
    return {
        "pillars": [p.model_dump() for p in _current_policy.pillars],
        "total_weight": sum(p.weight for p in _current_policy.pillars),
    }


@router.patch("/pillar", response_model=PillarConfig)
async def update_pillar(request: UpdatePillarRequest) -> PillarConfig:
    """Update a pillar's configuration."""
    pillar = next((p for p in _current_policy.pillars if p.id == request.pillar_id), None)
    if not pillar:
        raise HTTPException(status_code=404, detail=f"Pillar {request.pillar_id} not found")

    if request.weight is not None:
        pillar.weight = request.weight
    if request.threshold is not None:
        pillar.threshold = request.threshold

    _current_policy.updated_at = datetime.now(UTC).isoformat()
    logger.info(f"📊 Updated pillar {request.pillar_id}")
    return pillar


@router.post("/evaluate", response_model=PolicyEvaluationResult)
async def evaluate_policy(request: PolicyEvaluationRequest) -> PolicyEvaluationResult:
    """Evaluate an action against current policies."""
    trinity_score = calculate_trinity_score(request.pillar_scores)

    violations = []
    recommendations = []

    # Check pillar thresholds
    for pillar in _current_policy.pillars:
        score = request.pillar_scores.get(pillar.id, 0.0)
        if score < pillar.threshold:
            violations.append(
                f"{pillar.chinese} ({pillar.id}): {score:.1f} < {pillar.threshold:.1f}"
            )

    # Check auto-run eligibility
    auto_run_eligible = (
        trinity_score >= _current_policy.auto_run_threshold
        and request.risk_score <= _current_policy.risk_threshold
        and len(violations) == 0
    )

    # Generate recommendations
    if request.risk_score > _current_policy.risk_threshold:
        recommendations.append(
            f"Risk score {request.risk_score} exceeds threshold. Consider DRY RUN first."
        )
    if trinity_score < _current_policy.auto_run_threshold:
        recommendations.append(
            f"Trinity score {trinity_score} below auto-run threshold. Manual approval required."
        )

    return PolicyEvaluationResult(
        allowed=len(violations) == 0,
        trinity_score=trinity_score,
        auto_run_eligible=auto_run_eligible,
        violations=violations,
        recommendations=recommendations,
    )


@router.get("/health")
async def trinity_policy_health() -> dict[str, Any]:
    """Check Trinity Policy service health."""
    return {
        "status": "healthy",
        "service": "Trinity Policy",
        "policy_version": _current_policy.version,
        "auto_run_threshold": _current_policy.auto_run_threshold,
        "pillars_count": len(_current_policy.pillars),
    }
