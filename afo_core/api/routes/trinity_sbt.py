# Trinity Score: 90.0 (Established by Chancellor)
"""Trinity SBT (Soulbound Token) Router for AFO Kingdom
Trinity SBT 민트 API.

Manages Trinity Score-based Soulbound Token minting for immutable
achievement records. SBTs are non-transferable achievement badges.
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("AFO.TrinitySBT")
router = APIRouter(prefix="/trinity/sbt", tags=["Trinity SBT"])


# --- Pydantic Models ---


class SBTMetadata(BaseModel):
    """Soulbound Token metadata."""

    token_id: str = Field(default_factory=lambda: str(uuid4()))
    holder: str
    achievement: str
    trinity_score: float
    pillar_scores: dict[str, float]
    evidence_bundle_id: str | None = None
    minted_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    framework: str = "AFO Kingdom"


class MintRequest(BaseModel):
    """Request to mint a new SBT."""

    holder: str
    achievement: str
    trinity_score: float = Field(ge=0.0, le=100.0)
    pillar_scores: dict[str, float] = Field(default_factory=dict)
    evidence_bundle_id: str | None = None


class MintResponse(BaseModel):
    """Response from SBT minting."""

    success: bool
    token_id: str
    message: str
    metadata: SBTMetadata


class SBTCollection(BaseModel):
    """Collection of SBTs for a holder."""

    holder: str
    tokens: list[SBTMetadata]
    total_achievements: int
    average_trinity_score: float


# --- In-Memory Storage (MVP) ---
_sbt_registry: dict[str, SBTMetadata] = {}
_holder_tokens: dict[str, list[str]] = {}  # holder -> [token_ids]


# --- Metrics (Optional) ---
try:
    from AFO.domain.metrics.prometheus import trinity_sbt_minted

    _METRICS_AVAILABLE = True
except (ImportError, ValueError):
    # ImportError if module not found, ValueError if duplicate timeseries
    _METRICS_AVAILABLE = False
    trinity_sbt_minted = None


# --- Endpoints ---


@router.post("/mint", response_model=MintResponse)
async def mint_sbt(request: MintRequest) -> MintResponse:
    """Mint a new Soulbound Token for an achievement."""
    # Validate minimum Trinity Score for minting
    if request.trinity_score < 70.0:
        raise HTTPException(
            status_code=400,
            detail=f"Trinity Score {request.trinity_score} below minimum threshold (70.0) for SBT minting",
        )

    # Create SBT metadata
    sbt = SBTMetadata(
        holder=request.holder,
        achievement=request.achievement,
        trinity_score=request.trinity_score,
        pillar_scores=request.pillar_scores,
        evidence_bundle_id=request.evidence_bundle_id,
    )

    # Store in registry
    _sbt_registry[sbt.token_id] = sbt

    # Track by holder
    if request.holder not in _holder_tokens:
        _holder_tokens[request.holder] = []
    _holder_tokens[request.holder].append(sbt.token_id)

    # Update metrics if available
    if _METRICS_AVAILABLE:
        trinity_sbt_minted.labels(framework="AFO Kingdom").inc()

    logger.info(f"🏆 SBT Minted: {sbt.token_id} for {request.holder} - {request.achievement}")

    return MintResponse(
        success=True,
        token_id=sbt.token_id,
        message=f"Soulbound Token minted for achievement: {request.achievement}",
        metadata=sbt,
    )


@router.get("/token/{token_id}", response_model=SBTMetadata)
async def get_sbt(token_id: str) -> SBTMetadata:
    """Get SBT metadata by token ID."""
    if token_id not in _sbt_registry:
        raise HTTPException(status_code=404, detail=f"SBT {token_id} not found")
    return _sbt_registry[token_id]


@router.get("/holder/{holder}", response_model=SBTCollection)
async def get_holder_sbts(holder: str) -> SBTCollection:
    """Get all SBTs for a holder."""
    token_ids = _holder_tokens.get(holder, [])
    tokens = [_sbt_registry[tid] for tid in token_ids if tid in _sbt_registry]

    avg_score = sum(t.trinity_score for t in tokens) / len(tokens) if tokens else 0.0

    return SBTCollection(
        holder=holder,
        tokens=tokens,
        total_achievements=len(tokens),
        average_trinity_score=round(avg_score, 2),
    )


@router.get("/stats")
async def get_sbt_stats() -> dict[str, Any]:
    """Get SBT minting statistics."""
    all_tokens = list(_sbt_registry.values())

    return {
        "total_minted": len(all_tokens),
        "unique_holders": len(_holder_tokens),
        "average_trinity_score": (
            round(sum(t.trinity_score for t in all_tokens) / len(all_tokens), 2)
            if all_tokens
            else 0.0
        ),
        "highest_score": max((t.trinity_score for t in all_tokens), default=0.0),
        "achievements_by_month": {},  # Placeholder for future implementation
    }


@router.get("/verify/{token_id}")
async def verify_sbt(token_id: str) -> dict[str, Any]:
    """Verify SBT authenticity and retrieve on-chain proof placeholder."""
    if token_id not in _sbt_registry:
        return {
            "valid": False,
            "message": f"SBT {token_id} not found in registry",
        }

    sbt = _sbt_registry[token_id]
    return {
        "valid": True,
        "token_id": token_id,
        "holder": sbt.holder,
        "achievement": sbt.achievement,
        "trinity_score": sbt.trinity_score,
        "minted_at": sbt.minted_at,
        "framework": sbt.framework,
        "on_chain_proof": None,  # Placeholder for future blockchain integration
    }


@router.get("/health")
async def trinity_sbt_health() -> dict[str, Any]:
    """Check Trinity SBT service health."""
    return {
        "status": "healthy",
        "service": "Trinity SBT",
        "total_minted": len(_sbt_registry),
        "min_trinity_score_required": 70.0,
        "metrics_enabled": _METRICS_AVAILABLE,
    }
