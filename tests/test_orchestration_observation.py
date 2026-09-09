"""Tests for the sidecar serial/parallel orchestration observation contract."""

from __future__ import annotations

from copy import deepcopy

from hyodo.orchestration_observation import (
    ORCHESTRATION_OBSERVATION_SCHEMA_VERSION,
    join_adapter_events,
    validate_orchestration_observation,
)
from hyodo.tarjan_scc import hyodo_parent_edges


def _observation(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "schema": ORCHESTRATION_OBSERVATION_SCHEMA_VERSION,
        "observation_id": "obs-j",
        "run_id": "run-1",
        "event_id": "J",
        "ts": "2026-09-09T12:00:00Z",
        "node_id": "join",
        "execution": "parallel",
        "depends_on": ["A", "B"],
        "join_policy": "all",
        "state": "completed",
        "attempt": 1,
        "approval_wait_ms": 0,
        "evidence_refs": ["gate:test@abcdef0"],
    }
    row.update(overrides)
    return row


def test_valid_multi_parent_join_is_normalized() -> None:
    ok, reasons, normalized = validate_orchestration_observation(_observation())

    assert ok is True
    assert reasons == []
    assert normalized is not None
    assert normalized["depends_on"] == ["A", "B"]
    assert normalized["join_policy"] == "all"
    assert normalized["human_interventions"] == 0


def test_join_policy_requires_multiple_dependencies() -> None:
    ok, reasons, normalized = validate_orchestration_observation(
        _observation(depends_on=["A"], join_policy="all")
    )

    assert ok is False
    assert "invalid_field:join_policy:requires_multiple_dependencies" in reasons
    assert normalized is None


def test_self_dependency_is_rejected() -> None:
    ok, reasons, normalized = validate_orchestration_observation(
        _observation(depends_on=["A", "J"])
    )

    assert ok is False
    assert "invalid_field:depends_on:self" in reasons
    assert normalized is None


def test_join_adapter_exposes_dependencies_without_mutating_ledger() -> None:
    events = [
        {"event_id": "A", "run_id": "run-1"},
        {"event_id": "B", "run_id": "run-1"},
        {"event_id": "J", "run_id": "run-1"},
    ]
    before = deepcopy(events)

    adapted, issues = join_adapter_events(events, [_observation()])
    nodes, edges = hyodo_parent_edges(adapted)

    assert issues == []
    assert events == before
    assert "parent_event_ids" not in events[2]
    assert adapted[2]["parent_event_ids"] == ["A", "B"]
    assert nodes == ["A", "B", "J"]
    assert edges == [("J", "A"), ("J", "B")]


def test_invalid_sidecar_is_visible_and_not_exposed_to_graph_adapter() -> None:
    events = [{"event_id": "J", "run_id": "run-1"}]
    adapted, issues = join_adapter_events(
        events, [_observation(depends_on=["J", "A"])]
    )

    assert adapted == events
    assert issues == [
        {
            "observation_id": "obs-j",
            "reasons": ["invalid_field:depends_on:self"],
        }
    ]
