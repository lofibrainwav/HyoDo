from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

"""Chancellor Graph V2 Checkpoint and Event Store.

Atomic file-based storage for checkpoints and events.
"""


def _atomic_write(path: Path, data: str) -> None:
    """Write data atomically using tmp → replace pattern."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(path)


def save_checkpoint(trace_id: str, step: str, payload: dict[str, Any]) -> Path:
    """Save checkpoint for a graph step.

    Args:
        trace_id: Unique trace identifier
        step: Step name (e.g., "PARSE", "VERIFY")
        payload: State payload to save

    Returns:
        Path to saved checkpoint file
    """
    path = Path("artifacts/chancellor_checkpoints") / trace_id / f"{step}.json"
    _atomic_write(path, json.dumps(payload, ensure_ascii=False, indent=2))
    return path


def append_event(trace_id: str, event: dict[str, Any]) -> Path:
    """Append event to trace event log.

    Args:
        trace_id: Unique trace identifier
        event: Event payload with ts, step, event, ok, detail

    Returns:
        Path to event log file
    """
    path = Path("artifacts/chancellor_events") / f"{trace_id}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return path


def load_checkpoint(trace_id: str, step: str) -> dict[str, Any] | None:
    """Load checkpoint for a specific step.

    Args:
        trace_id: Unique trace identifier
        step: Step name

    Returns:
        Checkpoint payload or None if not found
    """
    path = Path("artifacts/chancellor_checkpoints") / trace_id / f"{step}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_checkpoints(trace_id: str) -> list[str]:
    """List all checkpoint steps for a trace.

    Args:
        trace_id: Unique trace identifier

    Returns:
        List of step names with saved checkpoints
    """
    path = Path("artifacts/chancellor_checkpoints") / trace_id
    if not path.exists():
        return []
    return [f.stem for f in path.glob("*.json")]
