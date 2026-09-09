"""Generic, evidence-derived friction events for orchestration observations.

The v0 contract keeps raw observable friction separate from later judgement.
Every derived event therefore starts with ``class: unknown``.  A future
calibration layer may classify avoidable, protective, chosen-growth, or
structural friction with its own provenance; this module does not guess.
"""

from __future__ import annotations

from typing import Any

from hyodo.orchestration_observation import validate_orchestration_observation

FRICTION_EVENT_SCHEMA_VERSION = "hyodo.friction-event/v0"

FRICTION_TYPES = frozenset(
    {
        "human_intervention",
        "agent_retry",
        "clarification_needed",
        "context_loss",
        "approval_wait",
        "blocked_action",
        "rollback",
        "duplicate_work",
        "unobserved_claim",
        "policy_conflict",
        "rework",
        "verification_failure",
    }
)
FRICTION_CLASSES = frozenset(
    {"avoidable", "protective", "chosen_growth", "structural", "unknown"}
)

_COUNT_RULES = (
    ("human_interventions", "human_intervention"),
    ("clarification_count", "clarification_needed"),
    ("context_loss_count", "context_loss"),
    ("duplicate_work_count", "duplicate_work"),
    ("unobserved_claim_count", "unobserved_claim"),
    ("policy_conflict_count", "policy_conflict"),
    ("rework_count", "rework"),
    ("verification_failure_count", "verification_failure"),
)


def _friction_event(
    observation: dict[str, Any],
    *,
    friction_type: str,
    rule_id: str,
    count: int | None = None,
    duration_ms: int | None = None,
) -> dict[str, Any]:
    magnitude: dict[str, int] = {}
    if count is not None:
        magnitude["count"] = count
    if duration_ms is not None:
        magnitude["duration_ms"] = duration_ms

    return {
        "schema": FRICTION_EVENT_SCHEMA_VERSION,
        "friction_event_id": f"{observation['observation_id']}:{friction_type}",
        "run_id": observation["run_id"],
        "ts": observation["ts"],
        "source_observation_id": observation["observation_id"],
        "source_event_ids": [observation["event_id"]],
        "node_id": observation["node_id"],
        "friction": {
            "type": friction_type,
            "class": "unknown",
        },
        "magnitude": magnitude,
        "evidence_refs": list(observation["evidence_refs"]),
        "provenance": {
            "derived_by": "hyodo",
            "rule_id": rule_id,
        },
        "authority": {
            "grants_execution": False,
            "overrides_policy": False,
            "overrides_evidence_gate": False,
        },
    }


def derive_friction_events(raw: Any) -> tuple[list[dict[str, Any]], list[str]]:
    """Derive zero or more generic FrictionEvent v0 records from one observation.

    Invalid observations produce no events and return validation reasons.  The
    derivation is deterministic and uses only explicit counters/state supplied by
    the external orchestrator sidecar; it does not infer intent from prompt text.
    """

    ok, reasons, observation = validate_orchestration_observation(raw)
    if not ok or observation is None:
        return [], reasons

    events: list[dict[str, Any]] = []

    retry_count = observation["attempt"] - 1
    if retry_count > 0:
        events.append(
            _friction_event(
                observation,
                friction_type="agent_retry",
                rule_id="attempt_gt_one",
                count=retry_count,
            )
        )

    approval_wait_ms = observation["approval_wait_ms"]
    if approval_wait_ms > 0:
        events.append(
            _friction_event(
                observation,
                friction_type="approval_wait",
                rule_id="approval_wait_ms_gt_zero",
                duration_ms=approval_wait_ms,
            )
        )

    if observation["state"] == "blocked":
        events.append(
            _friction_event(
                observation,
                friction_type="blocked_action",
                rule_id="state_blocked",
                count=1,
            )
        )
    elif observation["state"] == "rolled_back":
        events.append(
            _friction_event(
                observation,
                friction_type="rollback",
                rule_id="state_rolled_back",
                count=1,
            )
        )

    for field, friction_type in _COUNT_RULES:
        count = observation[field]
        if count > 0:
            events.append(
                _friction_event(
                    observation,
                    friction_type=friction_type,
                    rule_id=f"{field}_gt_zero",
                    count=count,
                )
            )

    events.sort(key=lambda event: event["friction"]["type"])
    return events, []


__all__ = [
    "FRICTION_CLASSES",
    "FRICTION_EVENT_SCHEMA_VERSION",
    "FRICTION_TYPES",
    "derive_friction_events",
]
