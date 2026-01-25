# Trinity Score: 90.0 (Established by Chancellor)
from typing import Any

from pydantic import BaseModel, Field

from strategists.base import log_action, robust_execute


class TruthModel(BaseModel):
    data: dict[str, Any] = Field(..., description="Data Structure - Required")
    validation_level: int = Field(1, ge=1, le=10, description="Validation Intensity")


def guard(data: dict[str, Any]) -> float:
    """Guan Yu (Truth): Type Integrity Guard

    [Modular Design Benefit]:
    - Type Safety: Enforces contract via Pydantic.
    - Robustness: Graceful degradation to 0.5 on validation error.
    """

    def _logic(d) -> None:
        model = TruthModel(**d)
        return min(1.0, model.validation_level / 10)

    # Fallback to 0.5 (Partial Trust) if validation crashes unexpectly
    result = robust_execute(_logic, data, fallback_value=0.5)
    log_action("Guan Yu 眞", result)
    return result


# V2 Interface Alias
truth_guard = guard
