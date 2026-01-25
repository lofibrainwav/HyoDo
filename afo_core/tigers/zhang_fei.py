# Trinity Score: 90.0 (Established by Chancellor)
from typing import Any

from strategists.base import log_action, robust_execute

try:
    from AFO.config.antigravity import antigravity
except ImportError:

    class MockAntiGravity:
        DRY_RUN_DEFAULT = True

    antigravity: Any = MockAntiGravity()  # type: ignore[no-redef]


def gate(risk_score: float, context: dict | None = None) -> float:
    """
    Zhang Fei (Goodness): Safety Gate

    [Goodness Philosophy]:
    - Strict Gating: Blocks execution if risk > 0.1.
    - Safety Fallback: Returns 0.0 (block) on any internal error.
    """

    if context is None:
        context = {}

    def _logic(val) -> None:
        risk, ctx = val
        if risk > 0.1:
            print(f"[Zhang Fei 善] Safety Gate BLOCK - Risk {risk}")
            return 0.0
        checks = [antigravity.DRY_RUN_DEFAULT, "ethics_pass" in ctx]
        return sum([1.0 if c else 0.0 for c in checks]) / len(checks)

    # Robust Execute: Fallback to 0.0 (Fail Safe)
    result = robust_execute(_logic, (risk_score, context), fallback_value=0.0)
    log_action("Zhang Fei 善", result)
    return result


# V2 Interface Alias
goodness_gate = gate
