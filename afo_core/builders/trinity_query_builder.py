# Trinity Score: 90.0 (Established by Chancellor)
from typing import Any

from pydantic import BaseModel, Field


class TrinityQuery(BaseModel):
    """Product: Immutable Complex Object
    Represents a full query context for the Chancellor-Strategist flow.
    """

    query: str = Field(..., description="User's raw query")
    context: dict[str, Any] = Field(default_factory=dict, description="Contextual data")
    risk_level: float = Field(0.0, ge=0.0, le=1.0, description="Assessed Risk Level")
    ux_level: int = Field(1, ge=1, le=10, description="Desired UX Complexity")
    dry_run: bool = Field(True, description="Safety Execution Mode")


class TrinityQueryBuilder:
    """Builder Pattern:
    Constructs complex TrinityQuery objects step-by-step.
    Benefits:
    - Fluent Interface (Method Chaining)
    - Enforces optional/default handling explicitly
    - Improves readability of client code
    """

    def __init__(self) -> None:
        # Default State
        self._query = ""
        self._context = {}
        self._risk_level = 0.0
        self._ux_level = 1
        self._dry_run = True

    def set_query(self, query: str) -> "TrinityQueryBuilder":
        self._query = query
        return self

    def with_context(self, context: dict[str, Any]) -> "TrinityQueryBuilder":
        self._context = context
        return self

    def with_risk(self, risk: float) -> "TrinityQueryBuilder":
        if not (0.0 <= risk <= 1.0):
            raise ValueError("Risk must be between 0.0 and 1.0")
        self._risk_level = risk
        return self

    def with_ux(self, level: int) -> "TrinityQueryBuilder":
        if not (1 <= level <= 10):
            raise ValueError("UX level must be between 1 and 10")
        self._ux_level = level
        return self

    def dry_run_mode(self, enabled: bool = True) -> "TrinityQueryBuilder":
        self._dry_run = enabled
        return self

    def build(self) -> TrinityQuery:
        """Constructs and returns the final immutable Product."""
        if not self._query:
            raise ValueError("[Builder] Query cannot be empty")

        return TrinityQuery(
            query=self._query,
            context=self._context,
            risk_level=self._risk_level,
            ux_level=self._ux_level,
            dry_run=self._dry_run,
        )
