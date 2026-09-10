"""Cursor native command-hook payload adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hyodo.connect import MappedHookEvent
from hyodo.host_adapters._common import map_tool_payload

CURSOR_PRE_EVENTS = frozenset({"preToolUse", "beforeShellExecution", "beforeMCPExecution"})
CURSOR_POST_EVENTS = frozenset(
    {"postToolUse", "afterShellExecution", "afterMCPExecution", "afterFileEdit"}
)


def _normalize_specialized_payload(payload: dict[str, Any], event_name: str) -> dict[str, Any]:
    normalized = dict(payload)
    tool_input = payload.get("tool_input")
    if event_name in {"beforeShellExecution", "afterShellExecution"}:
        normalized["tool_input"] = {"command": payload.get("command")}
    elif event_name in {"beforeMCPExecution", "afterMCPExecution"}:
        normalized["tool_input"] = {"arguments": tool_input}
    elif event_name == "afterFileEdit":
        normalized["tool_input"] = {
            "file_path": payload.get("file_path"),
            "edits": payload.get("edits"),
        }
    if event_name == "afterFileEdit" and payload.get("edits") is not None:
        normalized["output"] = payload["edits"]
    return normalized


def map_cursor_hook_payload(
    payload: Any, default_root: Path
) -> tuple[MappedHookEvent | None, str | None]:
    """Map Cursor tool hooks into ``hyodo.agent-event/v1``.

    Cursor lifecycle hooks such as ``subagentStart`` are intentionally not
    coerced into tool events; callers must report them as UNOBSERVED until the
    canonical schema has a lifecycle kind.
    """
    if isinstance(payload, dict):
        event_name = payload.get("hook_event_name")
        if event_name in {"subagentStart", "subagentStop", "sessionStart", "sessionEnd"}:
            return None, "unsupported_lifecycle_event:v1_schema"
        if isinstance(event_name, str):
            payload = _normalize_specialized_payload(payload, event_name)
    return map_tool_payload(
        payload,
        default_root,
        host="cursor",
        event_name=str(payload.get("hook_event_name")) if isinstance(payload, dict) else "",
        pre_events=CURSOR_PRE_EVENTS,
        post_events=CURSOR_POST_EVENTS,
    )


__all__ = ["map_cursor_hook_payload"]
