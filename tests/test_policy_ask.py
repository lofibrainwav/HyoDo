"""TDD for HyoDo Phase 1-A: ASK, external variables, trust, [web].

Spec: docs/superpowers/specs/2026-09-06-hyodo-agent-os-phase1-design.md,
Package 1-A.
"""

from __future__ import annotations

import uuid

from hyodo.policy_trust import (  # noqa: F401
    POLICY_TRUST_SCHEMA_ID,
    grant_policy_trust,
    load_policy_trust,
)

from hyodo.events import AGENT_EVENT_SCHEMA_VERSION, content_digest, validate_event
from hyodo.policy import (
    POLICY_SCHEMA_ID,
    PolicyConfig,
    PolicyDecision,
    TrustPolicy,  # noqa: F401
    WebPolicy,  # noqa: F401
    evaluate_policy,  # noqa: F401
    load_policy_config,  # noqa: F401
)


def _event(**overrides: object) -> dict:
    base: dict = {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "run_id": "run-ask",
        "ts": "2026-09-06T12:00:00+00:00",
        "kind": "tool_call",
        "step_index": 0,
        "actor": "agent",
        "tool": {"name": "search", "args_digest": content_digest("{}"), "paths": []},
        "io": {"input_digest": content_digest("in"), "output_digest": None},
        "meta": {"model": "test-model", "tags": ["unit"]},
    }
    base.update(overrides)
    return base


def _normalize(raw: dict) -> dict:
    ok, reasons, normalized = validate_event(raw)
    assert ok, reasons
    assert normalized is not None
    return normalized


def _bare_policy(**overrides: object) -> PolicyConfig:
    base: dict = {
        "schema": POLICY_SCHEMA_ID,
        "max_steps": None,
        "allowed_tools": None,
        "blocked_path_globs": (),
    }
    base.update(overrides)
    return PolicyConfig(**base)


# --------------------------------------------------------------------------- #
# PolicyDecision — new fields, no-probability guard
# --------------------------------------------------------------------------- #


def test_policy_decision_as_dict_key_set_excludes_probability_and_confidence():
    decision = PolicyDecision(
        decision="ASK",
        rule_id="external_variable",
        reason="1 external variable(s)",
        coverage=(2, 3),
        external_variables=("ask_tools:WebFetch",),
        trust_level=1,
    )
    payload = decision.as_dict()
    assert set(payload.keys()) == {
        "decision",
        "rule_id",
        "reason",
        "evaluated_by",
        "coverage",
        "external_variables",
        "trust_level",
    }
    assert "probability" not in payload
    assert "confidence" not in payload
    assert not any(isinstance(v, float) for v in payload.values())


def test_policy_decision_new_fields_default_for_backward_compatible_construction():
    """Existing callers that only pass decision/rule_id/reason must still work."""
    decision = PolicyDecision(decision="ALLOW", rule_id=None, reason=None)
    assert decision.coverage == (0, 0)
    assert decision.external_variables == ()
    assert decision.trust_level == 1
