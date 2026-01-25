# Trinity Score: 90.0 (Established by Chancellor)
"""
Health Service TypedDict Definitions
眞 (Truth): Precise type contracts for health monitoring
善 (Goodness): Type safety for reliable health reporting
"""

from typing import TypedDict


class ServiceCheckResult(TypedDict, total=False):
    """Individual service health check result."""

    healthy: bool
    output: str
    error: str | None
    attempt: int


class OrganStatus(TypedDict, total=False):
    """Individual organ health status (오장육부)."""

    status: str  # "healthy" | "unhealthy"
    score: int
    output: str
    latency_ms: int


class SecurityStatus(TypedDict, total=False):
    """Security probe result."""

    status: str
    score: int
    output: str
    latency_ms: int


class ContractV2(TypedDict):
    """V2 API contract metadata."""

    version: str
    organs_keys_expected: int


class FrictionData(TypedDict, total=False):
    """Friction metrics for serenity calculation."""

    score: float
    error_count: int
    friction_score: float
    error_count_last_100: int


class TrinityBreakdown(TypedDict):
    """Trinity Score pillar breakdown."""

    truth: float
    goodness: float
    beauty: float
    filial_serenity: float
    eternity: float


class OrgansV2Response(TypedDict, total=False):
    """V2 organs response with all metrics."""

    organs_v2: dict[str, OrganStatus]
    security: SecurityStatus
    contract_v2: ContractV2
    ts_v2: str
    iccls_gap: float
    sentiment: float
    friction: FrictionData
    breakdown: TrinityBreakdown


class TrinityDict(TypedDict, total=False):
    """Trinity metrics dictionary representation."""

    trinity_score: float
    truth: float
    goodness: float
    beauty: float
    filial_serenity: float
    eternity: float
    balance_status: str
    weights: dict[str, float]


class ComprehensiveHealthResponse(TypedDict, total=False):
    """Complete health check response."""

    # Service metadata
    service: str
    version: str
    build_version: str
    git_sha: str

    # Health status
    status: str  # "healthy" | "warning" | "imbalanced"
    health_percentage: float
    healthy_organs: int
    total_organs: int

    # Trinity Score
    trinity: TrinityDict

    # Decision
    decision: str  # "AUTO_RUN" | "ASK_COMMANDER" | "TRY_AGAIN"
    decision_message: str

    # Issues & Suggestions
    issues: list[str] | None
    suggestions: list[str]

    # Organs data
    organs: dict[str, OrganStatus]

    # V2 response fields (merged)
    organs_v2: dict[str, OrganStatus]
    security: SecurityStatus
    contract_v2: ContractV2
    ts_v2: str
    iccls_gap: float
    sentiment: float
    friction: FrictionData
    breakdown: TrinityBreakdown

    # Method & Timestamp
    method: str
    timestamp: str
