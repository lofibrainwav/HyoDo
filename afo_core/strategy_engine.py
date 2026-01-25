# Trinity Score: 90.0 (Established by Chancellor)
"""Strategy Engine for AFO Kingdom
Provides memory context and workflow management for LLM interactions.
"""

import contextlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MemoryContext:
    """In-memory context manager for conversation history and state.
    Provides short-term memory for LLM interactions.
    """

    history: list[dict[str, str]] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)
    max_turns: int = 20

    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        try:
            self.history.append(
                {
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            # Keep only last N turns
            if len(self.history) > self.max_turns * 2:
                self.history = self.history[-self.max_turns * 2 :]
        except Exception:
            # Silent failure for memory, or fallback logging
            pass

    def get_context(self, last_n: int = 5) -> list[dict[str, str]]:
        """Get recent conversation context."""
        try:
            return self.history[-last_n * 2 :] if self.history else []
        except Exception:
            return []

    def set_state(self, key: str, value: Any) -> None:
        """Set a state variable."""
        with contextlib.suppress(Exception):
            self.state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a state variable."""
        try:
            return self.state.get(key, default)
        except Exception:
            return default

    def clear(self) -> None:
        """Clear all memory."""
        try:
            self.history = []
            self.state = {}
        except Exception:
            pass


@dataclass
class WorkflowStep:
    """A single step in a workflow."""

    name: str
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None


class Workflow:
    """Workflow manager for multi-step LLM operations.
    Supports sequential and parallel execution patterns.
    """

    def __init__(self, name: str = "default") -> None:
        self.name = name
        self.steps: list[WorkflowStep] = []
        self.current_step: int = 0
        self.status: str = "idle"  # idle, running, completed, failed

    def next_step(self) -> WorkflowStep | None:
        """Get the next pending step."""
        try:
            for step in self.steps:
                if step.status == "pending":
                    return step
        except Exception:
            pass
        return None

    def mark_complete(self, step_name: str, result: Any = None) -> None:
        """Mark a step as complete."""
        try:
            for step in self.steps:
                if step.name == step_name:
                    step.status = "completed"
                    step.result = result
                    break
        except Exception:
            pass

    def is_complete(self) -> bool:
        """Check if all steps are complete."""
        try:
            return all(s.status == "completed" for s in self.steps)
        except Exception:
            return False

    def reset(self) -> None:
        """Reset the workflow."""
        try:
            self.steps = []
            self.current_step = 0
            self.status = "idle"
        except Exception:
            pass

    def to_dict(self) -> dict[str, Any]:
        """Serialize workflow to dict."""
        try:
            return {
                "name": self.name,
                "status": self.status,
                "steps": [
                    {"name": s.name, "action": s.action, "status": s.status} for s in self.steps
                ],
            }
        except Exception:
            return {"name": self.name, "status": "error", "steps": []}


# Global instances (exported for import)
memory_context = MemoryContext()
workflow = Workflow("afo_main")


# Convenience functions
def get_workflow() -> Workflow:
    """Get the global workflow."""
    try:
        return workflow
    except Exception:
        return Workflow("fallback")


def create_workflow(name: str) -> Workflow:
    """Create a new workflow."""
    try:
        return Workflow(name)
    except Exception:
        return Workflow("error_fallback")
