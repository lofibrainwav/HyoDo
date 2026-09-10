"""Cursor-native permission response adapter."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from hyodo.policy import PolicyDecision

CURSOR_PERMISSION_EVENTS = frozenset({"preToolUse", "beforeShellExecution", "beforeMCPExecution"})


def map_cursor_permission_response(
    decision: PolicyDecision,
    *,
    event_name: str,
    updated_input: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Map a HyoDo decision to Cursor's pre-action hook response envelope."""
    if event_name not in CURSOR_PERMISSION_EVENTS:
        raise ValueError(f"unsupported_cursor_permission_event:{event_name}")
    if updated_input is not None and event_name != "preToolUse":
        raise ValueError("updated_input_only_supported_for:preToolUse")

    permission = {
        "ALLOW": "allow",
        "DENY": "deny",
        "ASK": "ask",
        "UNOBSERVED": "deny",
    }.get(decision.decision, "deny")
    response: dict[str, Any] = {"permission": permission}
    reason = decision.reason or "insufficient evidence"
    if permission == "deny":
        response["user_message"] = f"HyoDo blocked this action: {reason}"
        response["agent_message"] = (
            f"HyoDo could not establish permission for this action. Decision: {decision.decision}."
        )
    elif permission == "ask":
        response["user_message"] = "HyoDo requires human approval before this action."
        response["agent_message"] = reason
    if updated_input is not None:
        response["updated_input"] = dict(updated_input)
    return response


__all__ = ["CURSOR_PERMISSION_EVENTS", "map_cursor_permission_response"]
