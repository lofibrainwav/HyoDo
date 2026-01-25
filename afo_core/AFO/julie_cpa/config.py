# Trinity Score: 90.0 (Established by Chancellor)
from pydantic_settings import BaseSettings


class JulieConfig(BaseSettings):
    """Julie CPA Configuration."""

    MIN_TX_ID_LENGTH: int = 5
    MIN_DESC_LENGTH: int = 3
    FRICTION_THRESHOLD: float = 0.7  # For critical operations
    MAX_FRICTION_THRESHOLD: float = 0.9  # Max limit before blocking
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 0.5


julie_config = JulieConfig()
