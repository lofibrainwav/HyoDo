# Trinity Score: 90.0 (Established by Chancellor)
from typing import Any

from .base import log_action, robust_execute

try:
    from AFO.config.antigravity import antigravity
except ImportError:
    # Dependency Injection Stub / Fallback Configuration
    class MockAntiGravity:
        DRY_RUN_DEFAULT = True

    antigravity: Any = MockAntiGravity()  # type: ignore[no-redef]


def review(query_data: dict[str, Any]) -> float:
    """
    Yi Sun-sin (Goodness): Risk & Ethics Review

    [Goodness Philosophy]:
    - Safety First: Check Risk Level and Dry Run status.
    - Graceful Degradation: If checking fails, assume high risk (0.0).
    """

    def _logic(data) -> None:
        risk_level = data.get("risk_level", 0.0)
        if risk_level > 0.1:
            print(f"[Yi Sun-sin 善] Risk too high: {risk_level}")
            return 0.0

        dry_run_score = 1.0 if getattr(antigravity, "DRY_RUN_DEFAULT", True) else 0.0
        ethics_score = 1.0 if "ethics_pass" in data else 0.0
        return (dry_run_score + ethics_score) / 2.0

    # Robust Execute: Fallback to 0.0 (Safety Fallback) on error
    result = robust_execute(_logic, query_data, fallback_value=0.0)
    log_action("Yi Sun-sin 善", result)
    return result


# V2 Interface Alias
goodness_review = review
