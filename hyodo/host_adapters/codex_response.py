"""Codex-native permission response adapter."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from hyodo.policy import PolicyDecision

CODEX_PERMISSION_EVENTS = frozenset({"PreToolUse", "PermissionRequest"})


def map_codex_permission_response(
    decision: PolicyDecision,
    *,
    event_name: str,
    updated_input: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Map a HyoDo decision to Codex's native hook response envelope.

    Codex does not support ``ask`` for ``PreToolUse``. HyoDo therefore maps
    ``ASK`` and ``UNOBSERVED`` to a fail-closed deny instead of allowing the
    tool call or pretending that a human prompt was observed.
    """
    if event_name not in CODEX_PERMISSION_EVENTS:
        raise ValueError(f"unsupported_codex_permission_event:{event_name}")
    if updated_input is not None and event_name != "PreToolUse":
        raise ValueError("updated_input_only_supported_for:PreToolUse")

    permission = "allow" if decision.decision == "ALLOW" else "deny"
    reason = decision.reason or "insufficient evidence"
    if event_name == "PermissionRequest":
        body: dict[str, Any] = {"behavior": permission}
        if permission == "deny":
            body["message"] = f"HyoDo blocked this action: {reason}"
        return {
            "hookSpecificOutput": {
                "hookEventName": event_name,
                "decision": body,
            }
        }

    output: dict[str, Any] = {
        "hookEventName": event_name,
        "permissionDecision": permission,
    }
    if permission == "deny":
        output["permissionDecisionReason"] = f"HyoDo blocked this action: {reason}"
    if updated_input is not None:
        output["updatedInput"] = dict(updated_input)
    return {"hookSpecificOutput": output}


__all__ = ["CODEX_PERMISSION_EVENTS", "map_codex_permission_response"]
