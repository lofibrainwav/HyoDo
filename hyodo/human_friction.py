"""Human-side friction events and a deterministic friction score.

Agent-emitted traces (``hyodo.agent-event/v1``) describe friction the agents
report about themselves. This module counts friction the *human* experiences,
from evidence an independent observer can re-check:

- ``re_explanation``: the human had to explain again something already given.
- ``duplicate_approval``: the human was asked again for an approval that an
  earlier approval already covered.
- ``context_loss``: an agent lost a path, setting, decision or method that the
  canon already recorded.
- ``runtime_abandon``: work sat queued or unanswered past a threshold.

Every event must carry raw pointers (message ids, request ids, timestamps), so
anyone can re-open the evidence. An event without them is rejected, never
counted. The observer that records an event must not be the actor whose work
caused it, compared trimmed and case-insensitive, and must not appear as an
actor anywhere in the same file.

``CLEAN`` needs positive evidence that someone looked: a
``hyodo.human-friction-observation/v1`` envelope naming the observer, the
window, the sources scanned and the event count. An empty file without one is
``UNOBSERVED``, never ``CLEAN``.

HyoDo validates pointers by shape only. Re-opening them and keeping the events
file append-only are the host's job. The score is a review signal only; it
never grants or denies execution authority.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

HUMAN_FRICTION_EVENT_SCHEMA = "hyodo.human-friction-event/v1"
HUMAN_FRICTION_SCORE_SCHEMA = "hyodo.human-friction-score/v1"
HUMAN_FRICTION_OBSERVATION_SCHEMA = "hyodo.human-friction-observation/v1"

# Default weights. A host may pass its own; HyoDo does not own the host's lens.
DEFAULT_WEIGHTS: dict[str, float] = {
    "re_explanation": 2.0,
    "duplicate_approval": 1.5,
    "context_loss": 3.0,
    "runtime_abandon": 2.5,
}

# Required evidence pointers per type. The first key identifies the event.
REQUIRED_EVIDENCE: dict[str, tuple[str, ...]] = {
    "re_explanation": ("message_ref", "repeats_ref"),
    "duplicate_approval": ("request_ref", "prior_request_ref", "covering_approval_ref"),
    "context_loss": ("message_ref", "lost_canon_ref"),
    "runtime_abandon": ("item_ref", "last_change_at", "observed_at", "threshold_seconds"),
}
EVENT_KEYS = frozenset({"schema", "type", "observed_by", "actor", "evidence", "note"})
ENVELOPE_KEYS = frozenset(
    {"schema", "observed_by", "window_start", "window_end", "sources_scanned", "event_count"}
)
MAX_REF_LENGTH = 300


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _is_ref(value: Any) -> bool:
    return isinstance(value, str) and 0 < len(value.strip()) <= MAX_REF_LENGTH


def _identity(value: Any) -> str | None:
    return value.strip().casefold() if _is_ref(value) else None


def validate_envelope(envelope: Any) -> str | None:
    """Return None when the observation envelope is valid, else the reason."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("schema") != HUMAN_FRICTION_OBSERVATION_SCHEMA
    ):
        return "envelope_schema_mismatch"
    if set(envelope) != ENVELOPE_KEYS:
        return "envelope_fields_mismatch"
    if _identity(envelope["observed_by"]) is None:
        return "envelope_observer_missing"
    start, end = _parse_time(envelope["window_start"]), _parse_time(envelope["window_end"])
    if start is None or end is None or end < start:
        return "envelope_window_invalid"
    sources = envelope["sources_scanned"]
    if not isinstance(sources, list) or not sources or not all(_is_ref(src) for src in sources):
        return "envelope_sources_invalid"
    count = envelope["event_count"]
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        return "envelope_count_invalid"
    return None


def validate_event(event: Any) -> tuple[str | None, str | None]:
    """Return (event_key, None) when valid, else (None, reason)."""
    if not isinstance(event, dict):
        return None, "not_object"
    if event.get("schema") != HUMAN_FRICTION_EVENT_SCHEMA:
        return None, "schema_mismatch"
    unknown = set(event) - EVENT_KEYS
    if unknown:
        return None, "unsupported_field"
    kind = event.get("type")
    if kind not in REQUIRED_EVIDENCE:
        return None, "unknown_type"
    observer, actor = event.get("observed_by"), event.get("actor")
    if not isinstance(observer, str) or not isinstance(actor, str):
        return None, "observer_or_actor_missing"
    if not _is_ref(observer) or not _is_ref(actor):
        return None, "observer_or_actor_missing"
    if _identity(observer) == _identity(actor):
        return None, "observer_is_actor"
    if "note" in event and not isinstance(event["note"], str):
        return None, "note_not_text"
    evidence = event.get("evidence")
    if not isinstance(evidence, dict) or set(evidence) != set(REQUIRED_EVIDENCE[kind]):
        return None, "evidence_fields_mismatch"

    if kind == "runtime_abandon":
        if not _is_ref(evidence["item_ref"]):
            return None, "evidence_ref_invalid"
        last_change = _parse_time(evidence["last_change_at"])
        observed = _parse_time(evidence["observed_at"])
        threshold = evidence["threshold_seconds"]
        if last_change is None or observed is None:
            return None, "timestamp_invalid"
        if isinstance(threshold, bool) or not isinstance(threshold, int) or threshold <= 0:
            return None, "threshold_invalid"
        if (observed - last_change).total_seconds() < threshold:
            return None, "below_threshold"
        return f"{kind}:{evidence['item_ref'].strip()}:{evidence['last_change_at']}", None

    refs = [evidence[key] for key in REQUIRED_EVIDENCE[kind]]
    if not all(_is_ref(ref) for ref in refs):
        return None, "evidence_ref_invalid"
    if len({ref.strip() for ref in refs}) != len(refs):
        return None, "evidence_refs_not_distinct"
    return f"{kind}:{refs[0].strip()}", None


def score_events(
    events: list[Any],
    weights: dict[str, float] | None = None,
    envelope: Any = None,
) -> dict[str, Any]:
    """Count valid events once each and compute the weighted friction score.

    ``CLEAN`` needs a valid observation envelope whose ``event_count`` matches
    the events given. A positive score stays ``FRICTION`` even when some events
    are unreadable; ``partial`` then says the count may be low.
    """
    weights = dict(DEFAULT_WEIGHTS if weights is None else weights)
    if set(weights) != set(DEFAULT_WEIGHTS) or not all(
        isinstance(w, (int, float)) and not isinstance(w, bool) and w >= 0 for w in weights.values()
    ):
        raise ValueError("weights must give a non-negative number for each of the four types")

    actors = {_identity(event.get("actor")) for event in events if isinstance(event, dict)} - {None}
    counts = dict.fromkeys(DEFAULT_WEIGHTS, 0)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, event in enumerate(events):
        key, reason = validate_event(event)
        if key is not None and _identity(event["observed_by"]) in actors:
            key, reason = None, "observer_is_actor_elsewhere"
        if key is None:
            rejected.append({"index": index, "reason": reason})
            continue
        if key in seen:
            rejected.append({"index": index, "reason": "duplicate_event"})
            continue
        seen.add(key)
        counts[event["type"]] += 1
        accepted.append({"index": index, "type": event["type"], "evidence": event["evidence"]})

    if envelope is None:
        rejected.append({"envelope": True, "reason": "no_observation_envelope"})
    else:
        envelope_reason = validate_envelope(envelope)
        if envelope_reason is None and _identity(envelope["observed_by"]) in actors:
            envelope_reason = "envelope_observer_is_actor"
        if envelope_reason is None and envelope["event_count"] != len(events):
            envelope_reason = "envelope_count_mismatch"
        if envelope_reason is not None:
            rejected.append({"envelope": True, "reason": envelope_reason})

    score = round(sum(weights[kind] * counts[kind] for kind in counts), 4)
    partial = any(r["reason"] != "duplicate_event" for r in rejected)
    if score > 0:
        state = "FRICTION"
    elif partial:
        state = "UNOBSERVED"  # missing or unreadable evidence never folds into CLEAN
    else:
        state = "CLEAN"
    return {
        "schema": HUMAN_FRICTION_SCORE_SCHEMA,
        "state": state,
        "score": score,
        "partial": partial,
        "counts": counts,
        "weights": weights,
        "accepted": accepted,
        "rejected": rejected,
        "authority": {"grants_execution": False, "review_signal_only": True},
    }


def read_events(path: Path) -> tuple[list[Any], Any, list[dict[str, Any]]]:
    """Read a JSONL file into (events, envelope, unreadable lines).

    A line whose schema is the observation schema is the envelope; a second
    one is unreadable, since two envelopes cannot both describe the file.
    """
    events: list[Any] = []
    envelope: Any = None
    unreadable: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            unreadable.append({"line": line_no, "reason": "invalid_json"})
            continue
        if isinstance(item, dict) and item.get("schema") == HUMAN_FRICTION_OBSERVATION_SCHEMA:
            if envelope is not None:
                unreadable.append({"line": line_no, "reason": "multiple_envelopes"})
                continue
            envelope = item
            continue
        events.append(item)
    return events, envelope, unreadable


def score_file(path: Path, weights: dict[str, float] | None = None) -> dict[str, Any]:
    """Score a JSONL events file; unreadable lines make the result partial."""
    events, envelope, unreadable = read_events(path)
    result = score_events(events, weights, envelope)
    if unreadable:
        result["rejected"].extend(unreadable)
        result["partial"] = True
        if result["state"] == "CLEAN":
            result["state"] = "UNOBSERVED"
    return result
