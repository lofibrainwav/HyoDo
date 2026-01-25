"""
Friction Metrics Analyzer (SSOT)
Analyzes system logs and build artifacts to calculate "Friction" (Serenity Impediment).
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def get_friction_metrics() -> dict[str, Any]:
    """
    Analyzes log files for recent errors (Friction).
    Returns:
        dict: {
            "error_count_last_100": int,
            "friction_score": float (0.0 - 1.0),
            "log_file_exists": bool
        }
    """
    try:
        from AFO.config.settings import get_settings

        settings = get_settings()
        log_file = Path(settings.BASE_DIR) / "data" / "monitoring" / "afo_evolution.log"
    except ImportError:
        # Fallback if settings not available
        log_file = Path("data/monitoring/afo_evolution.log")

    error_count = 0

    if log_file.exists():
        try:
            # Read last 100 lines
            with open(log_file) as f:
                lines = f.readlines()[-100:]
                for line in lines:
                    if "ERROR" in line or "CRITICAL" in line or "Exception" in line:
                        error_count += 1
        except Exception as e:
            logger.warning(f"Failed to read log file: {e}")

    # Friction Score (0.0 = No Friction, 1.0 = High Friction)
    # Simple heuristic: 1 error = 0.1 friction, cap at 1.0
    friction_score = min(1.0, error_count * 0.1)

    return {
        "error_count_last_100": error_count,
        "friction_score": friction_score,
        "log_file_exists": log_file.exists(),
    }
