"""Contract tests for local-only Friction Contribution v1."""

from __future__ import annotations

import json
import stat
from pathlib import Path

from hyodo.events import AGENT_EVENTS_RELATIVE_PATH
from hyodo.friction import (
    CONTRIBUTION_FIELDS,
    FRICTION_CONTRIBUTION_SCHEMA_VERSION,
    FRICTION_STATE_RELATIVE_PATH,
    derive_contributions,
    derive_run_contribution,
    load_friction_state,
    preview_payload,
    save_friction_state,
    validate_contribution,
)


def _event(
    event_id: str,
    *,
    run_id: str = "secret-run-id",
    step: int = 0,
    kind: str = "tool_call",
    actor: str = "agent",
    actor_id: str | None = "seat-secret",
    ts: str = "2026-09-08T12:00:00+00:00",
    tags: list[str] | None = None,
    decision: str | None = None,
    evaluated_by: str | None = None,
    method: str | None = None,
    evidence_refs: list[str] | None = None,
    model: str = "gpt-5.6-sol-secret-model-build",
) -> dict[str, object]:
    policy: dict[str, object] = {
        "decision": decision,
        "rule_id": "private-rule-name",
        "reason": "private policy reason",
        "evaluated_by": evaluated_by,
    }
    return {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": event_id,
        "run_id": run_id,
        "ts": ts,
        "kind": kind,
        "step_index": step,
        "actor": actor,
        "actor_id": actor_id,
        "parent_event_id": "private-parent-id",
        "evidence_refs": evidence_refs or [],
        "tool": {
            "name": "private.tool.name",
            "args_digest": "0123456789ab",
            "paths": ["/home/company/secret-project/payment.py"],
            "method": method,
            "urls": [
                {
                    "domain": "private.example.com",
                    "path": "/secret/customer?id=42",
                    "digest": "abcdef012345",
                    "credential_shaped": False,
                }
            ],
        },
        "io": {
            "input_digest": "111111111111",
            "output_digest": "222222222222",
            "bytes_in": 12,
            "bytes_out": 24,
            "input_text": "PROMPT SECRET API_KEY=sk-do-not-export",
            "output_text": "SOURCE CODE SECRET customer@example.com",
        },
        "policy": policy,
        "meta": {"model": model, "tags": tags or []},
    }


def _write_ledger(root: Path, rows: list[object]) -> None:
    path = root / AGENT_EVENTS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) if not isinstance(row, str) else row for row in rows) + "\n")


def test_derived_contribution_is_strict_allowlist_and_contains_no_raw_identifiers_or_bodies():
    rows = [
        _event("private-event-1", tags=["task:code_change", "risk:medium", "retry"]),
        _event(
            "private-event-2",
            step=1,
            kind="tool_result",
            evidence_refs=["gate:test@abcdef0"],
            decision="ALLOW",
            evaluated_by="hyodo.policy/v1",
        ),
    ]

    contribution = derive_run_contribution(rows)

    assert set(contribution) == CONTRIBUTION_FIELDS
    assert contribution["schema"] == FRICTION_CONTRIBUTION_SCHEMA_VERSION
    serialized = json.dumps(contribution, sort_keys=True)
    for forbidden in (
        "secret-run-id",
        "seat-secret",
        "private-event-1",
        "private-event-2",
        "private-parent-id",
        "/home/company/secret-project/payment.py",
        "PROMPT SECRET",
        "API_KEY",
        "SOURCE CODE SECRET",
        "customer@example.com",
        "private.example.com",
        "private.tool.name",
        "private-rule-name",
        "private policy reason",
        "2026-09-08T12:00:00+00:00",
        "gpt-5.6-sol-secret-model-build",
    ):
        assert forbidden not in serialized
    assert contribution["provider_class"] == "openai"
    assert contribution["retry_bucket"] == "1"


def test_caller_claimed_policy_without_evaluator_provenance_cannot_create_pass_outcome():
    contribution = derive_run_contribution(
        [_event("e1", decision="ALLOW", evaluated_by=None, kind="decision")]
    )
    assert contribution["outcome"] == "unknown"


def test_measured_decision_controls_outcome_but_never_exports_authority_fields():
    contribution = derive_run_contribution(
        [_event("e1", decision="DENY", evaluated_by="hyodo.policy/v1", kind="decision")]
    )
    assert contribution["outcome"] == "blocked"
    assert "decision" not in contribution
    assert "authority" not in contribution
    assert "rule_id" not in contribution


def test_fanout_bucketing_interventions_and_approval_wait_are_deterministic():
    rows = [
        _event(
            "e1",
            actor_id="agent-a",
            step=0,
            tags=["task:dependency_update", "risk:low", "retry", "resource_conflict"],
            decision="ASK",
            evaluated_by="hyodo.policy/v1",
        ),
        _event("e2", actor_id="agent-b", step=0, tags=["rework"]),
        _event(
            "e3",
            actor="human",
            actor_id="human-a",
            step=1,
            kind="decision",
            ts="2026-09-08T12:00:20+00:00",
            evidence_refs=["gate:review@abcdef0"],
        ),
        _event(
            "e4",
            actor_id="agent-a",
            step=2,
            kind="error",
            tags=["verification_failure"],
            evidence_refs=["gate:test@abcdef0"],
        ),
    ]

    first = derive_run_contribution(rows)
    second = derive_run_contribution(list(reversed(rows)))

    assert first == second
    assert first["orchestration_pattern"] == "fanout"
    assert first["parallelism_bucket"] == "2"
    assert first["retry_bucket"] == "1"
    assert first["rework_bucket"] == "1"
    assert first["verification_failure_bucket"] == "1"
    assert first["human_intervention_bucket"] == "1"
    assert first["approval_wait_bucket"] == "0-30s"
    assert first["resource_conflict_bucket"] == "1"


def test_legacy_event_without_actor_id_or_evidence_fields_remains_derivable():
    legacy = _event("legacy")
    legacy.pop("actor_id")
    legacy.pop("parent_event_id")
    legacy.pop("evidence_refs")
    contribution = derive_run_contribution([legacy])
    assert contribution["orchestration_pattern"] == "serial"
    assert contribution["evidence_completeness"] == "unobserved"


def test_corrupt_ledger_marks_source_quality_without_copying_bad_line(tmp_path: Path):
    secret_bad_line = "NOT JSON SUPER SECRET CUSTOMER DATA"
    _write_ledger(tmp_path, [_event("e1"), secret_bad_line])

    contributions, observation = derive_contributions(tmp_path)

    assert observation["corrupt_lines"] == 1
    assert contributions[0]["source_quality"] == "corrupt"
    assert secret_bad_line not in json.dumps(contributions)


def test_run_id_is_a_local_filter_only_and_never_exported(tmp_path: Path):
    _write_ledger(
        tmp_path,
        [
            _event("a", run_id="run-A", tags=["task:test"]),
            _event("b", run_id="run-B", tags=["task:docs"]),
        ],
    )
    contributions, observation = derive_contributions(tmp_path, run_id="run-B")
    assert observation["runs_observed"] == 1
    assert contributions[0]["task_class"] == "docs"
    assert "run-B" not in json.dumps(contributions)


def test_validator_rejects_any_extra_identity_field():
    contribution = derive_run_contribution([_event("e1")])
    contribution["run_id"] = "forbidden"
    ok, reasons = validate_contribution(contribution)
    assert not ok
    assert "forbidden_field:run_id" in reasons


def test_local_state_defaults_off_and_network_consent_can_never_be_enabled(tmp_path: Path):
    default = load_friction_state(tmp_path)
    assert default.enabled is False
    assert default.state == "default_off"
    assert default.network_consent is False

    enabled = save_friction_state(tmp_path, True)
    assert enabled.enabled is True
    assert enabled.network_consent is False
    state_path = tmp_path / FRICTION_STATE_RELATIVE_PATH
    assert stat.S_IMODE(state_path.stat().st_mode) == 0o600
    persisted = json.loads(state_path.read_text())
    assert persisted["network_consent"] is False
    assert persisted["consent_scope"] == "local_only_v1"

    disabled = save_friction_state(tmp_path, False)
    assert disabled.enabled is False
    assert load_friction_state(tmp_path).enabled is False


def test_preview_seals_population_support_vs_authority_invariant(tmp_path: Path):
    _write_ledger(tmp_path, [_event("e1")])
    preview = preview_payload(tmp_path)
    assert preview["nothing_transmitted"] is True
    assert preview["network_consent"] is False
    assert preview["network_transport"] == "disabled"
    assert preview["authority"] == {
        "may_influence_acl_support": True,
        "may_grant_execution_authority": False,
        "may_override_local_policy": False,
        "may_override_evidence_gate": False,
    }
    assert "run_ids" in preview["never_export"]
    assert "raw_event_bodies" in preview["never_export"]
