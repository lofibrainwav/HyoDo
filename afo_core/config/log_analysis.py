"""
AFO Kingdom Log Analysis Configuration
Trinity Score: 善 (Goodness) - Centralized Configuration
Author: AFO Kingdom Development Team
"""

from pathlib import Path

from pydantic_settings import BaseSettings


class LogAnalysisSettings(BaseSettings):
    """
    Log Analysis Configuration Settings
    Centralizes all configurable parameters for the Log Analysis Pipeline.
    """

    CHUNK_SIZE: int = 100
    OUTPUT_DIR: Path = Path("analysis_results")
    ENABLE_REPORT: bool = True
    LOG_LEVEL: str = "INFO"

    # Resilience Settings (TICKET-037)
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0

    # Monitoring Settings (TICKET-039)
    ENABLE_MONITORING: bool = True

    # Performance Settings (TICKET-040)
    MEMORY_THRESHOLD_MB: int = 512

    # Environment variable prefix: AFO_LOG_
    class Config:
        env_prefix = "AFO_LOG_"
        case_sensitive = False


log_analysis_settings = LogAnalysisSettings()
