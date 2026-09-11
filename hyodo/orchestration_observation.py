"""Sidecar DAG observations for HyoDo evidence runs.

HyoDo remains a gate and evidence spine, not an agent runtime.  This module
lets an external orchestrator describe serial/parallel dependencies without
changing ``hyodo.agent-event/v1`` or granting execution authority.
"""

from __future__ import annotations

import json
import os
import stat
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

ORCHESTRATION_OBSERVATION_SCHEMA_VERSION = "hyodo.orchestration-observation/v1"

#: Sidecar observations live beside the agent ledger, never inside it. Keeping
#: the files apart is what makes "the source ledger is never mutated" checkable
#: rather than a promise: an observation cannot be mistaken for an event.
ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH = Path(".hyodo") / "orchestration-observations.jsonl"

EXECUTION_MODES = frozenset({"serial", "parallel"})
JOIN_POLICIES = frozenset({"all", "any"})
NODE_STATES = frozenset({"started", "completed", "blocked", "failed", "rolled_back"})

_COUNT_FIELDS = (
    "human_interventions",
    "clarification_count",
    "context_loss_count",
    "duplicate_work_count",
    "unobserved_claim_count",
    "policy_conflict_count",
    "rework_count",
    "verification_failure_count",
)


def _non_empty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_orchestration_observation(
    raw: Any,
) -> tuple[bool, list[str], dict[str, Any] | None]:
    """Validate and normalize one sidecar orchestration observation."""

    if not isinstance(raw, dict):
        return False, ["not_an_object"], None

    reasons: list[str] = []
    if raw.get("schema") != ORCHESTRATION_OBSERVATION_SCHEMA_VERSION:
        reasons.append("unsupported_schema")

    for field in ("observation_id", "run_id", "event_id", "ts", "node_id"):
        if not _non_empty(raw.get(field)):
            reasons.append(f"invalid_field:{field}")

    execution = raw.get("execution")
    if execution not in EXECUTION_MODES:
        reasons.append("invalid_field:execution")

    state = raw.get("state")
    if state not in NODE_STATES:
        reasons.append("invalid_field:state")

    depends_on_raw = raw.get("depends_on", [])
    depends_on: list[str] = []
    if not isinstance(depends_on_raw, list) or not all(
        _non_empty(value) for value in depends_on_raw
    ):
        reasons.append("invalid_field:depends_on")
    else:
        depends_on = sorted({value.strip() for value in depends_on_raw})
        event_id = raw.get("event_id")
        if isinstance(event_id, str) and event_id.strip() in depends_on:
            reasons.append("invalid_field:depends_on:self")

    join_policy = raw.get("join_policy")
    if join_policy is not None and join_policy not in JOIN_POLICIES:
        reasons.append("invalid_field:join_policy")
    if join_policy is not None and len(depends_on) < 2:
        reasons.append("invalid_field:join_policy:requires_multiple_dependencies")

    attempt = raw.get("attempt", 1)
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        reasons.append("invalid_field:attempt")

    approval_wait_ms = raw.get("approval_wait_ms", 0)
    if not _non_negative_int(approval_wait_ms):
        reasons.append("invalid_field:approval_wait_ms")

    counts: dict[str, int] = {}
    for field in _COUNT_FIELDS:
        value = raw.get(field, 0)
        if not _non_negative_int(value):
            reasons.append(f"invalid_field:{field}")
        else:
            counts[field] = value

    evidence_refs_raw = raw.get("evidence_refs", [])
    evidence_refs: list[str] = []
    if not isinstance(evidence_refs_raw, list) or not all(
        _non_empty(value) for value in evidence_refs_raw
    ):
        reasons.append("invalid_field:evidence_refs")
    else:
        evidence_refs = sorted({value.strip() for value in evidence_refs_raw})

    if reasons:
        return False, reasons, None

    normalized: dict[str, Any] = {
        "schema": ORCHESTRATION_OBSERVATION_SCHEMA_VERSION,
        "observation_id": raw["observation_id"].strip(),
        "run_id": raw["run_id"].strip(),
        "event_id": raw["event_id"].strip(),
        "ts": raw["ts"].strip(),
        "node_id": raw["node_id"].strip(),
        "execution": execution,
        "depends_on": depends_on,
        "join_policy": join_policy,
        "state": state,
        "attempt": attempt,
        "approval_wait_ms": approval_wait_ms,
        "evidence_refs": evidence_refs,
        **counts,
    }
    return True, [], normalized


def join_adapter_events(
    events: Iterable[object], observations: Iterable[object]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Expose sidecar dependencies to Graph v2 helpers without silent drops.

    The source ledger rows are never mutated. ``parent_event_ids`` is a transient
    adapter field understood by the Graph v2 SCC oracle from PR #228; it is not
    written back into ``hyodo.agent-event/v1``. Invalid, duplicate, or unresolved
    observations are returned as explicit issues rather than being mistaken for
    an absent dependency.
    """

    adapted = [dict(event) for event in events if isinstance(event, Mapping)]
    event_ids = {
        event_id.strip()
        for event in adapted
        for event_id in [event.get("event_id")]
        if isinstance(event_id, str) and event_id.strip()
    }

    by_event_id: dict[str, list[str]] = {}
    issues: list[dict[str, Any]] = []
    for raw in observations:
        ok, reasons, normalized = validate_orchestration_observation(raw)
        if not ok or normalized is None:
            observation_id = raw.get("observation_id") if isinstance(raw, dict) else None
            issues.append(
                {
                    "observation_id": observation_id,
                    "reasons": list(reasons),
                }
            )
            continue

        observation_id = normalized["observation_id"]
        event_id = normalized["event_id"]
        if event_id not in event_ids:
            issues.append(
                {
                    "observation_id": observation_id,
                    "reasons": [f"unresolved_event_id:{event_id}"],
                }
            )
            continue
        if event_id in by_event_id:
            issues.append(
                {
                    "observation_id": observation_id,
                    "reasons": [f"duplicate_observation_event_id:{event_id}"],
                }
            )
            continue

        unresolved = [ref for ref in normalized["depends_on"] if ref not in event_ids]
        if unresolved:
            issues.append(
                {
                    "observation_id": observation_id,
                    "reasons": [f"unresolved_dependency:{ref}" for ref in unresolved],
                }
            )
        by_event_id[event_id] = normalized["depends_on"]

    for event in adapted:
        event_id = event.get("event_id")
        if isinstance(event_id, str) and event_id in by_event_id:
            event["parent_event_ids"] = list(by_event_id[event_id])
    return adapted, issues


__all__ = [
    "EXECUTION_MODES",
    "JOIN_POLICIES",
    "NODE_STATES",
    "ORCHESTRATION_OBSERVATION_SCHEMA_VERSION",
    "join_adapter_events",
    "validate_orchestration_observation",
]


def append_orchestration_observation(root: Path, raw: Any) -> bool:
    """Validate and append one sidecar observation. Never raises.

    The normalized form is stored, not the caller's dict, so a field nobody
    validated cannot ride along into the record. An observation that does not
    validate is refused rather than written -- a sidecar that accepts anything
    would make the dependency graph unfalsifiable.

    File mode is pinned to ``0o600`` like the event ledger: an observation
    names run, event and node identifiers, which are salted digests but still
    describe someone's execution.
    """
    ok, _reasons, normalized = validate_orchestration_observation(raw)
    if not ok or normalized is None:
        return False

    path = root / ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(normalized, sort_keys=True, ensure_ascii=False) + "\n")
        if stat.S_IMODE(path.stat().st_mode) != 0o600:
            os.chmod(path, 0o600)
        return True
    except OSError:
        return False


def read_orchestration_observations(root: Path) -> list[dict[str, Any]]:
    """Read back stored observations, skipping lines that do not parse.

    A corrupt line is skipped rather than allowed to empty the whole file:
    an unreadable record must not read as an absent dependency.
    """
    path = root / ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    rows.append(parsed)
    except OSError:
        return rows
    return rows
