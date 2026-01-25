# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Kingdom Rate Limit Policy Configuration (Phase 2.6)

Defines the Redis Down Policy (Hybrid Strategy) to balance security (Fail-Closed)
and availability (Fail-Open) based on the 5 Pillars philosophy.
"""

from typing import Final


class RedisDownPolicy:
    """Policy definitions for handling Redis downtime.

    Strategies:
    - FAIL_OPEN: Allow requests (or use in-memory fallback) when Redis is down.
                 Prioritizes Availability (Service Continuity).
    - FAIL_CLOSED: Block requests when Redis is down.
                   Prioritizes Security (Prevent Abuse).
    - HYBRID: Apply Fail-Closed to sensitive endpoints, Fail-Open to others.
    """

    FAIL_OPEN: Final[str] = "fail_open"
    FAIL_CLOSED: Final[str] = "fail_closed"
    HYBRID: Final[str] = "hybrid"

    # Endpoints that MUST be protected even if DB is down (Security First)
    SENSITIVE_ENDPOINTS: Final[list[str]] = [
        "/api/auth",
        "/api/billing",
        "/api/admin",
        "/api/wallet/billing",  # Usage/Cost info
        "/api/wallet/session",  # Session management
        "/api/wallet/keys",  # API Key management
    ]

    # Default policy setting (Can be overridden by env AFO_REDIS_DOWN_POLICY)
    DEFAULT_POLICY: Final[str] = HYBRID
