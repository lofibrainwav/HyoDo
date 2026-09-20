"""Codex native command-hook payload adapter."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hyodo.connect import MappedHookEvent
from hyodo.events import (
    AGENT_EVENT_SCHEMA_VERSION,
    content_digest,
    count_run_events,
    validate_event,
)
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

# Codex 0.155.1 exposes this schema in its native hook implementation.  It has
# no prompt-specific native id, so ``turn_id`` is the only host-provided
# per-submission correlation key available to this adapter.
CODEX_PROMPT_EVENT = "UserPromptSubmit"
CODEX_PROMPT_REQUIRED_FIELDS = (
    "cwd",
    "model",
    "permission_mode",
    "prompt",
    "session_id",
    "turn_id",
)


def _recorded_prompt_id(root: Path, session_id: str, turn_id: str) -> str | None:
    """Return an existing matching prompt id; never synthesize one from a hook."""
    ledger = root / ".hyodo" / "agent-events.jsonl"
    try:
        lines = ledger.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return None
    expected = f"codex:{CODEX_PROMPT_EVENT}:{session_id}:{turn_id}"
    found = False
    for line in lines:
        if not line.strip():
            continue
        try:
            candidate = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            return None
        if not isinstance(candidate, dict):
            return None
        if candidate.get("event_id") != expected:
            continue
        if candidate.get("run_id") != session_id:
            return None
        if candidate.get("kind") != "prompt" or candidate.get("actor") != "human":
            return None
        valid, _, _ = validate_event(candidate)
        if not valid or found:
            return None
        found = True
    return expected if found else None


def map_codex_prompt_payload(
    payload: Any, default_root: Path
) -> tuple[MappedHookEvent | None, str | None]:
    """Map a verified Codex ``UserPromptSubmit`` payload into a prompt event.

    The native prompt body is reduced to a digest. The optional transcript
    path is also reduced to a source tag digest, never an event reference.
    No path or identity is inferred.
    """
    if not isinstance(payload, dict):
        return None, "not_an_object"
    if payload.get("hook_event_name") != CODEX_PROMPT_EVENT:
        return None, "unsupported_hook_event_name"
    for field in CODEX_PROMPT_REQUIRED_FIELDS:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            return None, f"missing_field:{field}"
    prompt = payload["prompt"]
    session_id = payload["session_id"].strip()
    turn_id = payload["turn_id"].strip()
    cwd = payload["cwd"].strip()
    root = Path(cwd) if cwd else default_root
    step_index = count_run_events(root, session_id)
    tags = ["host:codex", f"host_event:{CODEX_PROMPT_EVENT}"]
    if step_index is None:
        step_index = 0
        tags.append("step_index:unobserved")

    raw: dict[str, Any] = {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": f"codex:{CODEX_PROMPT_EVENT}:{session_id}:{turn_id}",
        "run_id": session_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": "prompt",
        "step_index": step_index,
        "actor": "human",
        "io": {"input_digest": content_digest(prompt)},
        "meta": {"model": payload["model"].strip(), "tags": tags},
    }
    transcript_path = payload.get("transcript_path")
    if isinstance(transcript_path, str) and transcript_path.strip():
        raw["meta"]["tags"].extend(
            [
                "source:codex-transcript",
                f"source-path-digest:{content_digest(transcript_path.strip())}",
            ]
        )
    return MappedHookEvent(raw=raw, root=root), None


def map_codex_hook_payload(
    payload: Any, default_root: Path
) -> tuple[MappedHookEvent | None, str | None]:
    """Map Codex Pre/PostToolUse payloads without claiming hosted-tool coverage."""
    if isinstance(payload, dict):
        event_name = payload.get("hook_event_name")
        if event_name == CODEX_PROMPT_EVENT:
            return map_codex_prompt_payload(payload, default_root)
        if event_name in {"PermissionRequest", "SubagentStart", "SubagentStop"}:
            return None, f"unsupported_event:v1_schema:{event_name}"
    mapped = map_tool_payload(
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
    if mapped[0] is not None and isinstance(payload, dict):
        event_name = payload.get("hook_event_name")
        turn_id = payload.get("turn_id")
        session_id = payload.get("session_id")
        if event_name == "PreToolUse" and isinstance(turn_id, str) and isinstance(session_id, str):
            parent = _recorded_prompt_id(mapped[0].root, session_id.strip(), turn_id.strip())
            if parent is not None:
                mapped[0].raw["parent_event_id"] = parent
    return mapped


__all__ = ["map_codex_hook_payload", "map_codex_prompt_payload"]
