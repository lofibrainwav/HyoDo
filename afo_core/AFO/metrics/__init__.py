"""AFO Metrics Package.

Provides Prometheus metrics collection for:
- Trinity Score tracking
- 11臟六腑 organ health
- API request/response metrics
"""

from .api_metrics import (
    APIMetric,
    APIMetricsCollector,
    record_api_call,
)
from .organ_metrics import (
    OrganHealth,
    OrganMetricsCollector,
    OrganType,
)
from .trinity_metrics import (
    PillarScore,
    TrinityMetricsCollector,
    TrinityScoreResult,
    calculate_trinity_score,
)

__all__ = [
    # Trinity
    "TrinityScoreResult",
    "PillarScore",
    "TrinityMetricsCollector",
    "calculate_trinity_score",
    # Organ
    "OrganType",
    "OrganHealth",
    "OrganMetricsCollector",
    # API
    "APIMetric",
    "APIMetricsCollector",
    "record_api_call",
]
