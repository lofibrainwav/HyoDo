from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

"""Chancellor Graph V2 State Schema.

Minimal state dataclass for graph execution tracking.
"""


@dataclass
class GraphState:
    """State object passed through graph nodes.

    Attributes:
        trace_id: Unique trace identifier for this execution
        request_id: Request identifier from commander
        input: Original input payload
        plan: Execution plan from PARSE node
        outputs: Outputs collected from each node
        errors: Error messages collected during execution
        step: Current step name
        started_at: Unix timestamp when execution started
        updated_at: Unix timestamp of last update
    """

    trace_id: str
    request_id: str
    input: dict[str, Any]
    plan: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    step: str = "CMD"
    started_at: float = 0.0
    updated_at: float = 0.0
