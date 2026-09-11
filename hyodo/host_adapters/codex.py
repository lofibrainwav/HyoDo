"""Codex native command-hook payload adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hyodo.connect import MappedHookEvent
from hyodo.host_adapters._common import map_tool_payload

CODEX_PRE_EVENTS = frozenset({"PreToolUse"})
CODEX_POST_EVENTS = frozenset({"PostToolUse"})

#: Codex names the tool result `tool_response`. Measured against codex-cli
#: 0.154.0: a real `PostToolUse` payload carries it as a string, and carries no
#: `output` or `result_json` at all. `output` and `result_json` stay in the
#: list so a payload shaped by some other producer still maps.
CODEX_OUTPUT_KEYS = ("tool_response", "output", "result_json")

#: Codex pairs its tool hooks 1:1, so a `PostToolUse` answers the `PreToolUse`
#: carrying the same `tool_use_id`. Cursor's specialized hooks are not such a
#: pairing, which is why this is declared per host rather than assumed.
CODEX_PARENT_EVENTS = {"PostToolUse": "PreToolUse"}

#: Measured against codex-cli 0.154.0: both tool hooks carry `model` as a
#: string. Cursor was not observed sending one, so it declares nothing.
CODEX_MODEL_KEY = "model"


def map_codex_hook_payload(
    payload: Any, default_root: Path
) -> tuple[MappedHookEvent | None, str | None]:
    """Map Codex Pre/PostToolUse payloads without claiming hosted-tool coverage."""
    if isinstance(payload, dict):
        event_name = payload.get("hook_event_name")
        if event_name in {"PermissionRequest", "SubagentStart", "SubagentStop"}:
            return None, f"unsupported_event:v1_schema:{event_name}"
    return map_tool_payload(
        payload,
        default_root,
        host="codex",
        event_name=str(payload.get("hook_event_name")) if isinstance(payload, dict) else "",
        pre_events=CODEX_PRE_EVENTS,
        post_events=CODEX_POST_EVENTS,
        output_keys=CODEX_OUTPUT_KEYS,
        parent_events=CODEX_PARENT_EVENTS,
        model_key=CODEX_MODEL_KEY,
    )


__all__ = ["map_codex_hook_payload"]
