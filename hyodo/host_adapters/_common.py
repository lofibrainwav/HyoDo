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
        # One tool call emits two canonical events (tool_call, tool_result) that
        # share the host's tool id. The ledger keys idempotency on event_id, so a
        # bare tool id makes the second half a conflict and drops it in silence.
        # Qualifying by host and event name keeps the tool id as the correlation
        # anchor while giving each canonical event its own identity.
        return f"{host}:{event_name}:{native}"
    # Specialized hooks do not always provide a tool id. A digest is a
    # correlation id, not a claim that the host supplied an id.
    stable = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    digest = content_digest(f"{host}:{event_name}:{stable}")
    return f"{host}:{event_name}:{digest}" if digest else None


def _digestable(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    if isinstance(value, (dict, list, int, float, bool)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return None


def map_tool_payload(
    payload: Any,
    default_root: Path,
    *,
    host: str,
    event_name: str,
    pre_events: frozenset[str],
    post_events: frozenset[str],
    output_keys: tuple[str, ...] = ("output", "result_json"),
    parent_events: dict[str, str] | None = None,
    model_key: str | None = None,
) -> tuple[MappedHookEvent | None, str | None]:
    """Map a host tool hook into HyoDo's validated event shape.

    ``output_keys`` is the host's own vocabulary for a tool result, in
    precedence order. It is a parameter rather than a fixed list because the
    name is a host fact: Codex says ``tool_response`` where Cursor says
    ``output``. Assuming one host's word holds for the others would be a guess
    about hosts nobody measured.

    ``parent_events`` maps a result event name to the call event name it
    answers, for hosts where that pairing is 1:1 and measured. Cursor's
    specialized hooks are not such a pairing, so it passes nothing.

    ``model_key`` names the payload field carrying the model identifier, for
    hosts measured to send one. A host that was never observed sending it
    passes nothing rather than having the field guessed at.
    """
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
    if not isinstance(tool_input, (dict, str)):
        tool_input = {}
    tool_name = _nonempty(payload.get("tool_name")) or event_name
    tool: dict[str, Any] = {"name": tool_name}
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    file_path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    args_value = command if isinstance(command, str) and command else tool_input
    args_text = _digestable(args_value)
    if args_text:
        tool["args_digest"] = content_digest(args_text)
    if isinstance(file_path, str) and file_path:
        tool["paths"] = [file_path]
    # `meta.model` is a v1 slot that read null on every event because nobody
    # filled it. The host names the model that ran; a non-string value is left
    # out rather than coerced into a claim.
    meta: dict[str, Any] = {"tags": tags}
    if model_key:
        model = _nonempty(payload.get(model_key))
        if model:
            meta["model"] = model

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
        "meta": meta,
    }
    duration = payload.get("duration")
    io: dict[str, Any] = {}
    if isinstance(duration, int) and not isinstance(duration, bool) and duration >= 0:
        io["duration_ms"] = duration
    # Only the result half can carry a result. A digest on a `tool_call` would
    # be a claim about something that has not happened yet.
    output = None
    if event_name in post_events:
        for key in output_keys:
            candidate = payload.get(key)
            if candidate is not None:
                output = candidate
                break
    output_text = _digestable(output)
    if output_text:
        io["output_digest"] = content_digest(output_text)
    if io:
        raw["io"] = io

    # The result points back at the call it answers. The parent is derived from
    # the host's own tool id, so no ledger lookup is needed and the mapper stays
    # pure. Without that id the event_id is a payload digest, and a digest of
    # the result cannot produce the digest of the call -- so there is no parent
    # to derive and none is invented. When the call is missing from the ledger,
    # the v1 validator reports `unresolved_ref`; dropping the link instead would
    # make a gap in the host's output look like a complete record.
    if parent_events:
        parent_event_name = parent_events.get(event_name)
        native_tool_id = _nonempty(payload.get("tool_use_id"))
        if parent_event_name and native_tool_id:
            raw["parent_event_id"] = f"{host}:{parent_event_name}:{native_tool_id}"

    return MappedHookEvent(raw=raw, root=root), None
