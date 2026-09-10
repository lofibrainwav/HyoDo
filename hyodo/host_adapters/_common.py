"""Shared, privacy-minimized helpers for native host hook adapters."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hyodo.connect import MappedHookEvent
from hyodo.events import AGENT_EVENT_SCHEMA_VERSION, content_digest, count_run_events


def _nonempty(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _event_id(payload: dict[str, Any], host: str, event_name: str) -> str | None:
    native = _nonempty(payload.get("tool_use_id"))
    if native:
        return native
    # Specialized hooks do not always provide a tool id. A digest is a
    # correlation id, not a claim that the host supplied an id.
    stable = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    digest = content_digest(f"{host}:{event_name}:{stable}")
    return f"{host}:{event_name}:{digest}" if digest else None


def map_tool_payload(
    payload: Any,
    default_root: Path,
    *,
    host: str,
    event_name: str,
    pre_events: frozenset[str],
    post_events: frozenset[str],
) -> tuple[MappedHookEvent | None, str | None]:
    """Map a host tool hook into HyoDo's validated event shape."""
    if not isinstance(payload, dict):
        return None, "not_an_object"
    session_id = _nonempty(payload.get("session_id")) or _nonempty(payload.get("conversation_id"))
    if not session_id:
        return None, "missing_field:session_id"
    if event_name not in pre_events | post_events:
        return None, "unsupported_hook_event_name"
    event_id = _event_id(payload, host, event_name)
    if not event_id:
        return None, "missing_field:tool_use_id"
    root_value = _nonempty(payload.get("cwd"))
    root = Path(root_value) if root_value else default_root
    step_index = count_run_events(root, session_id)
    tags: list[str] = [f"host:{host}", f"host_event:{event_name}"]
    if step_index is None:
        step_index = 0
        tags.append("step_index:unobserved")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}
    tool_name = _nonempty(payload.get("tool_name")) or event_name
    tool: dict[str, Any] = {"name": tool_name}
    command = tool_input.get("command")
    if isinstance(command, str) and command:
        tool["args_digest"] = content_digest(command)
    file_path = tool_input.get("file_path")
    if isinstance(file_path, str) and file_path:
        tool["paths"] = [file_path]
    raw: dict[str, Any] = {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": event_id,
        "run_id": session_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": "tool_call" if event_name in pre_events else "tool_result",
        "step_index": step_index,
        "actor": "agent",
        "actor_id": _nonempty(payload.get("agent_id")) or session_id,
        "tool": tool,
        "meta": {"tags": tags},
    }
    duration = payload.get("duration")
    if isinstance(duration, int) and not isinstance(duration, bool) and duration >= 0:
        raw["io"] = {"duration_ms": duration}
    return MappedHookEvent(raw=raw, root=root), None
