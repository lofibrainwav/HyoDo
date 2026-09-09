"""Tests for generic FrictionEvent v0 derivation."""

from __future__ import annotations

from hyodo.friction_event import (
    FRICTION_EVENT_SCHEMA_VERSION,
    derive_friction_events,
)
from hyodo.orchestration_observation import ORCHESTRATION_OBSERVATION_SCHEMA_VERSION


def _observation(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "schema": ORCHESTRATION_OBSERVATION_SCHEMA_VERSION,
        "observation_id": "obs-worker-b",
        "run_id": "run-1",
        "event_id": "evt-worker-b",
        "ts": "2026-09-09T12:00:00Z",
        "node_id": "worker-b",
        "execution": "parallel",
        "depends_on": ["evt-plan"],
        "join_policy": None,
        "state": "completed",
        "attempt": 1,
        "approval_wait_ms": 0,
        "human_interventions": 0,
        "clarification_count": 0,
        "context_loss_count": 0,
        "duplicate_work_count": 0,
        "unobserved_claim_count": 0,
        "policy_conflict_count": 0,
        "rework_count": 0,
        "verification_failure_count": 0,
        "evidence_refs": ["gate:test@abcdef0"],
    }
    row.update(overrides)
    return row


def test_clean_observation_derives_no_friction() -> None:
    events, reasons = derive_friction_events(_observation())

    assert reasons == []
    assert events == []


def test_explicit_signals_derive_decomposable_events() -> None:
    events, reasons = derive_friction_events(
        _observation(
            attempt=3,
            approval_wait_ms=2500,
            human_interventions=2,
            context_loss_count=1,
            duplicate_work_count=4,
        )
    )

    assert reasons == []
    by_type = {event["friction"]["type"]: event for event in events}
    assert set(by_type) == {
        "agent_retry",
        "approval_wait",
        "context_loss",
        "duplicate_work",
        "human_intervention",
    }
    assert by_type["agent_retry"]["magnitude"] == {"count": 2}
    assert by_type["approval_wait"]["magnitude"] == {"duration_ms": 2500}
    assert by_type["duplicate_work"]["magnitude"] == {"count": 4}


def test_blocked_and_rollback_are_state_derived() -> None:
    blocked, blocked_reasons = derive_friction_events(_observation(state="blocked"))
    rolled_back, rollback_reasons = derive_friction_events(_observation(state="rolled_back"))

    assert blocked_reasons == []
    assert rollback_reasons == []
    assert [event["friction"]["type"] for event in blocked] == ["blocked_action"]
    assert [event["friction"]["type"] for event in rolled_back] == ["rollback"]


def test_v0_does_not_guess_good_or_bad_friction() -> None:
    events, reasons = derive_friction_events(
        _observation(policy_conflict_count=1, human_interventions=1)
    )

    assert reasons == []
    assert events
    for event in events:
        assert event["schema"] == FRICTION_EVENT_SCHEMA_VERSION
        assert event["friction"]["class"] == "unknown"
        assert event["provenance"]["derived_by"] == "hyodo"
        assert event["authority"] == {
            "grants_execution": False,
            "overrides_policy": False,
            "overrides_evidence_gate": False,
        }


def test_invalid_observation_fails_closed_without_events() -> None:
    events, reasons = derive_friction_events(_observation(attempt=0))

    assert events == []
    assert "invalid_field:attempt" in reasons
