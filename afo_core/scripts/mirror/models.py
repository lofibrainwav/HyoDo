# Trinity Score: 90.0 (Established by Chancellor)
"""
Mirror Models - Data models for Chancellor Mirror

Contains:
- TrinityScoreAlert: Alert model for Trinity Score violations
- MirrorConfig: Configuration model for the mirror system
"""

from pydantic import BaseModel, Field


class TrinityScoreAlert(BaseModel):
    """Trinity Score Alert Model"""

    pillar: str
    score: float
    threshold: float
    timestamp: str
    message: str


class MirrorConfig(BaseModel):
    """Configuration for Chancellor Mirror"""

    api_base: str = Field(default="http://localhost:8010")
    alert_threshold: float = Field(default=90.0)
    pillar_thresholds: dict[str, float] = Field(
        default_factory=lambda: {
            "truth": 90.0,
            "goodness": 90.0,
            "beauty": 90.0,
            "serenity": 90.0,
            "eternity": 90.0,
        }
    )
    stream_channel: str = Field(default="afo:verdicts")
    polling_interval_seconds: int = Field(default=600)  # 10 minutes
    error_retry_seconds: int = Field(default=60)  # 1 minute
