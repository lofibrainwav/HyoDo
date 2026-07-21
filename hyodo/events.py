"""Agent event ledger — FDE Evidence Spine (opt-in).

Append-only local JSONL of agent steps (prompt / tool / response / error /
decision). Default storage is **digest-only** so customer data is not retained
unless the caller opts into full bodies.

This module is a **gate and evidence spine**, not an agent runtime. DENY
decisions must be enforced by the caller; HyoDo records and reports them.

Schema: ``hyodo.agent-event/v1``
Ledger: ``.hyodo/agent-events.jsonl`` (separate from gate ``history.jsonl``).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

AGENT_EVENT_SCHEMA_VERSION = "hyodo.agent-event/v1"
AGENT_EVENTS_RELATIVE_PATH = Path(".hyodo") / "agent-events.jsonl"

EVENT_KINDS = frozenset(
    {
        "prompt",
        "tool_call",
        "tool_result",
        "model_response",
        "error",
        "decision",
    }
)
ACTORS = frozenset({"agent", "human", "hyodo"})
POLICY_DECISIONS = frozenset({"ALLOW", "DENY", "ASK"})

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_DIGEST_RE = re.compile(r"^[0-9a-f]{12}$")


def content_digest(text: str | bytes | None) -> str | None:
    """Return first 12 hex chars of SHA-256, or None when *text* is None."""
    if text is None:
        return None
    payload = text.encode("utf-8") if isinstance(text, str) else text
    return hashlib.sha256(payload).hexdigest()[:12]


def _is_non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_event(raw: Any) -> tuple[bool, list[str], dict[str, Any] | None]:
    """Validate and normalize one agent event.

    Returns ``(ok, reasons, normalized_or_none)``. Reasons use stable codes
    (``missing_field``, ``invalid_kind``, …) for machine consumers.
    """
    reasons: list[str] = []
    if not isinstance(raw, dict):
        return False, ["not_an_object"], None

    schema = raw.get("schema_version")
    if schema != AGENT_EVENT_SCHEMA_VERSION:
        reasons.append("unsupported_schema")

    for field in ("event_id", "run_id", "ts", "kind", "actor"):
        if field not in raw:
            reasons.append(f"missing_field:{field}")
        elif not _is_non_empty_str(raw[field]):
            reasons.append(f"invalid_field:{field}")

    if "step_index" not in raw:
        reasons.append("missing_field:step_index")
    elif (
        not isinstance(raw["step_index"], int)
        or isinstance(raw["step_index"], bool)
        or raw["step_index"] < 0
    ):
        reasons.append("invalid_field:step_index")

    kind = raw.get("kind")
    if _is_non_empty_str(kind) and kind not in EVENT_KINDS:
        reasons.append("invalid_kind")

    actor = raw.get("actor")
    if _is_non_empty_str(actor) and actor not in ACTORS:
        reasons.append("invalid_actor")

    for id_field in ("event_id", "run_id"):
        value = raw.get(id_field)
        if _is_non_empty_str(value) and not _UUID_RE.match(value):
            # Soft: accept non-UUID opaque ids (FDE runners often use ulid/nanoid).
            # Only reject empty (already handled). Opaque strings are allowed.
            pass

    tool_raw = raw.get("tool")
    tool_out: dict[str, Any] | None = None
    if tool_raw is not None:
        if not isinstance(tool_raw, dict):
            reasons.append("invalid_field:tool")
        else:
            tool_out = {}
            name = tool_raw.get("name")
            if name is not None:
                if not _is_non_empty_str(name):
                    reasons.append("invalid_field:tool.name")
                else:
                    tool_out["name"] = name
            else:
                tool_out["name"] = None
            args_digest = tool_raw.get("args_digest")
            if args_digest is not None:
                if not (isinstance(args_digest, str) and _DIGEST_RE.match(args_digest)):
                    reasons.append("invalid_field:tool.args_digest")
                else:
                    tool_out["args_digest"] = args_digest
            else:
                tool_out["args_digest"] = None
            paths = tool_raw.get("paths")
            if paths is not None:
                if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
                    reasons.append("invalid_field:tool.paths")
                else:
                    tool_out["paths"] = list(paths)
            else:
                tool_out["paths"] = []

    io_raw = raw.get("io")
    io_out: dict[str, Any] = {
        "input_digest": None,
        "output_digest": None,
        "bytes_in": 0,
        "bytes_out": 0,
    }
    full_bodies: dict[str, str] = {}
    if io_raw is not None:
        if not isinstance(io_raw, dict):
            reasons.append("invalid_field:io")
        else:
            for dig_key in ("input_digest", "output_digest"):
                dig = io_raw.get(dig_key)
                if dig is not None:
                    if not (isinstance(dig, str) and _DIGEST_RE.match(dig)):
                        reasons.append(f"invalid_field:io.{dig_key}")
                    else:
                        io_out[dig_key] = dig
            for byte_key in ("bytes_in", "bytes_out"):
                val = io_raw.get(byte_key, 0)
                if val is None:
                    val = 0
                if not isinstance(val, int) or isinstance(val, bool) or val < 0:
                    reasons.append(f"invalid_field:io.{byte_key}")
                else:
                    io_out[byte_key] = val
            # Full bodies are opt-in: only kept when present and strings.
            for body_key in ("input_text", "output_text"):
                body = io_raw.get(body_key)
                if body is not None:
                    if not isinstance(body, str):
                        reasons.append(f"invalid_field:io.{body_key}")
                    else:
                        full_bodies[body_key] = body
                        # Fill digest from body when digest omitted.
                        dig_key = "input_digest" if body_key == "input_text" else "output_digest"
                        if io_out[dig_key] is None:
                            io_out[dig_key] = content_digest(body)

    policy_raw = raw.get("policy")
    policy_out: dict[str, Any] | None = None
    if policy_raw is not None:
        if not isinstance(policy_raw, dict):
            reasons.append("invalid_field:policy")
        else:
            decision = policy_raw.get("decision")
            if decision is not None and decision not in POLICY_DECISIONS:
                reasons.append("invalid_field:policy.decision")
            rule_id = policy_raw.get("rule_id")
            if rule_id is not None and not isinstance(rule_id, str):
                reasons.append("invalid_field:policy.rule_id")
            reason = policy_raw.get("reason")
            if reason is not None and not isinstance(reason, str):
                reasons.append("invalid_field:policy.reason")
            policy_out = {
                "decision": decision,
                "rule_id": rule_id if isinstance(rule_id, str) else None,
                "reason": reason if isinstance(reason, str) else None,
            }

    meta_raw = raw.get("meta")
    meta_out: dict[str, Any] = {"model": None, "tags": []}
    if meta_raw is not None:
        if not isinstance(meta_raw, dict):
            reasons.append("invalid_field:meta")
        else:
            model = meta_raw.get("model")
            if model is not None and not isinstance(model, str):
                reasons.append("invalid_field:meta.model")
            else:
                meta_out["model"] = model
            tags = meta_raw.get("tags", [])
            if tags is None:
                tags = []
            if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
                reasons.append("invalid_field:meta.tags")
            else:
                meta_out["tags"] = list(tags)

    if reasons:
        return False, reasons, None

    # At this point required fields are valid.
    normalized: dict[str, Any] = {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": str(raw["event_id"]).strip(),
        "run_id": str(raw["run_id"]).strip(),
        "ts": str(raw["ts"]).strip(),
        "kind": str(raw["kind"]).strip(),
        "step_index": int(raw["step_index"]),
        "actor": str(raw["actor"]).strip(),
        "tool": tool_out
        if tool_out is not None
        else {"name": None, "args_digest": None, "paths": []},
        "io": io_out,
        "policy": policy_out
        if policy_out is not None
        else {"decision": None, "rule_id": None, "reason": None},
        "meta": meta_out,
    }
    # Full bodies only when provided (opt-in by presence).
    if full_bodies:
        normalized["io"] = {**io_out, **full_bodies}
    return True, [], normalized


def strip_full_bodies(event: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with ``input_text`` / ``output_text`` removed (digest-only)."""
    out = json.loads(json.dumps(event))
    io = out.get("io")
    if isinstance(io, dict):
        io.pop("input_text", None)
        io.pop("output_text", None)
        # Ensure digests exist if bodies were the only source (already set in validate).
    return out


def append_agent_event(root: Path, event: dict[str, Any]) -> bool:
    """Append one normalized event to the agent ledger. Never raises."""
    path = root / AGENT_EVENTS_RELATIVE_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def read_agent_events(root: Path) -> tuple[list[dict[str, Any]], int]:
    """Read the agent ledger. Returns ``(events, corrupt_line_count)``."""
    path = root / AGENT_EVENTS_RELATIVE_PATH
    if not path.exists():
        return [], 0
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return [], 0
    events: list[dict[str, Any]] = []
    corrupt = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            corrupt += 1
            continue
        if isinstance(parsed, dict):
            events.append(parsed)
        else:
            corrupt += 1
    return events, corrupt


def load_event_from_path(path: Path) -> tuple[Any | None, str | None]:
    """Load JSON object from *path*. Returns ``(data, error_code)``."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None, "unreadable_path"
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None, "invalid_json"
    return data, None


def load_event_from_text(text: str) -> tuple[Any | None, str | None]:
    """Parse JSON object from a string. Returns ``(data, error_code)``."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None, "invalid_json"
    return data, None
