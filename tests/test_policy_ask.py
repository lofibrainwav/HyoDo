"""TDD for HyoDo Phase 1-A: ASK, external variables, trust, [web].

Spec: docs/superpowers/specs/2026-09-06-hyodo-agent-os-phase1-design.md,
Package 1-A.
"""

from __future__ import annotations

import uuid

import pytest

from hyodo.events import (
    AGENT_EVENT_SCHEMA_VERSION,
    content_digest,
    credential_shaped_path,
    validate_event,
)
from hyodo.policy import (
    POLICY_SCHEMA_ID,
    PolicyConfig,
    PolicyConfigError,
    PolicyDecision,
    TrustPolicy,
    WebPolicy,
    _compute_coverage,
    _domain_allowed,
    _is_web_classified,
    evaluate_policy,
    load_policy_config,
)
from hyodo.policy_trust import (  # noqa: F401
    POLICY_TRUST_SCHEMA_ID,
    grant_policy_trust,
    load_policy_trust,
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


def _web_tool_event(**overrides: object) -> dict:
    tool = {
        "name": "web_fetch",
        "args_digest": None,
        "paths": [],
        "method": overrides.pop("method", "GET"),
        "urls": overrides.pop("urls", [{"domain": "unlisted.example.com", "path": "/v1/data"}]),
    }
    return _event(tool=tool, **overrides)


def test_load_policy_config_defaults_new_fields(tmp_path):
    path = tmp_path / "policy.toml"
    path.write_text(f'schema = "{POLICY_SCHEMA_ID}"\n', encoding="utf-8")
    cfg = load_policy_config(path)
    assert cfg.web is None
    assert cfg.ask_tools == ()
    assert cfg.ask_threshold is None
    assert cfg.trust is None


def test_load_policy_config_parses_web_and_trust(tmp_path):
    path = tmp_path / "policy.toml"
    path.write_text(
        f'''schema = "{POLICY_SCHEMA_ID}"

ask_tools = ["send_email"]
ask_threshold = 2

[web]
allowed_domains = ["api.example.com", "*.internal.example.com"]
allow_non_get = false
allow_credential_paths = false

[trust]
max_level = 2
''',
        encoding="utf-8",
    )
    cfg = load_policy_config(path)
    assert cfg.web == WebPolicy(
        allowed_domains=("api.example.com", "*.internal.example.com"),
        allow_non_get=False,
        allow_credential_paths=False,
    )
    assert cfg.ask_tools == ("send_email",)
    assert cfg.ask_threshold == 2
    assert cfg.trust == TrustPolicy(max_level=2)


@pytest.mark.parametrize(
    "body",
    [
        f'schema = "{POLICY_SCHEMA_ID}"\n\n[trust]\nmax_level = 7\n',
        f'schema = "{POLICY_SCHEMA_ID}"\n\nask_threshold = -1\n',
        f'schema = "{POLICY_SCHEMA_ID}"\n\n[web]\nallow_non_get = "yes"\n',
    ],
)
def test_load_policy_config_rejects_invalid_new_fields(tmp_path, body):
    path = tmp_path / "policy.toml"
    path.write_text(body, encoding="utf-8")
    with pytest.raises(PolicyConfigError):
        load_policy_config(path)


def test_is_web_classified_and_domain_helpers():
    policy = _bare_policy(ask_tools=("send_email",))
    assert _is_web_classified("WebFetch", policy)
    assert _is_web_classified("send_email", policy)
    assert not _is_web_classified("read_file", policy)
    assert _domain_allowed("api.example.com", ("api.example.com",))
    assert _domain_allowed("svc.internal.example.com", ("*.internal.example.com",))
    assert not _domain_allowed("evil.example", ("api.example.com",))


def test_credential_shaped_paths():
    assert credential_shaped_path("/.git/config")
    assert credential_shaped_path("/.env")
    assert credential_shaped_path("/wp-admin/")
    assert credential_shaped_path("/v1/users?api_key=secret")
    assert not credential_shaped_path("/v1/users")
    assert not credential_shaped_path(None)


def test_compute_coverage_counts_applicable_surfaces():
    policy = _bare_policy(allowed_tools=("search",), max_steps=10)
    assert _compute_coverage(
        policy, "tool_call", "search", [], [], None, 3, None, effective_level=1
    ) == (2, 2)


def test_evaluate_unlisted_domain_is_ask():
    policy = _bare_policy(web=WebPolicy(allowed_domains=("api.example.com",)))
    decision = evaluate_policy(_normalize(_web_tool_event()), policy)
    assert decision.decision == "ASK"
    assert "web_domain_unlisted:unlisted.example.com" in decision.external_variables
    assert decision.trust_level == 1


def test_evaluate_non_get_is_hard_deny():
    policy = _bare_policy(web=WebPolicy(allowed_domains=("api.example.com",)))
    event = _normalize(
        _web_tool_event(method="POST", urls=[{"domain": "api.example.com", "path": "/v1"}])
    )
    decision = evaluate_policy(event, policy)
    assert decision.decision == "DENY"
    assert decision.rule_id == "web_non_get_denied"


def test_evaluate_credential_path_is_hard_deny_and_can_be_allowed():
    event = _normalize(_web_tool_event(urls=[{"domain": "api.example.com", "path": "/wp-admin/"}]))
    denied = evaluate_policy(
        event, _bare_policy(web=WebPolicy(allowed_domains=("api.example.com",)))
    )
    assert denied.rule_id == "web_credential_path_denied"
    allowed = evaluate_policy(
        event,
        _bare_policy(
            web=WebPolicy(allowed_domains=("api.example.com",), allow_credential_paths=True)
        ),
    )
    assert allowed.decision != "DENY"


def test_evaluate_clean_event_is_allow_with_coverage():
    decision = evaluate_policy(_normalize(_event()), _bare_policy(allowed_tools=("search",)))
    assert decision.decision == "ALLOW"
    assert decision.external_variables == ()
    assert decision.coverage == (1, 1)


def test_evaluate_ask_threshold_does_not_create_deny():
    policy = _bare_policy(ask_tools=("send_email",), ask_threshold=0)
    event = _normalize(_event(tool={"name": "send_email", "args_digest": None, "paths": []}))
    decision = evaluate_policy(event, policy)
    assert decision.decision == "ASK"
    assert "above configured threshold" in (decision.reason or "")


def test_evaluate_path_outside_root_is_ask(tmp_path):
    event = _normalize(
        _event(tool={"name": "read_file", "args_digest": None, "paths": ["/etc/passwd"]})
    )
    decision = evaluate_policy(event, _bare_policy(), root=tmp_path)
    assert decision.decision == "ASK"
    assert "path_outside_root:/etc/passwd" in decision.external_variables


def test_trust_levels_0_to_3_and_unobserved(tmp_path):
    event = _normalize(_event(tool={"name": "send_email", "args_digest": None, "paths": []}))
    policy = _bare_policy(ask_tools=("send_email",), trust=TrustPolicy(max_level=3))

    grant_policy_trust(tmp_path, 0, by="human:test")
    level0 = evaluate_policy(event, policy, observed_steps=1, root=tmp_path)
    assert (level0.decision, level0.trust_level) == ("ASK", 0)

    grant_policy_trust(tmp_path, 2, by="human:test")
    level2 = evaluate_policy(event, policy, observed_steps=1, root=tmp_path)
    assert (level2.decision, level2.rule_id, level2.trust_level) == ("ALLOW", "autorun_level2", 2)
    missing_observation = evaluate_policy(event, policy, observed_steps=None, root=tmp_path)
    assert missing_observation.decision == "UNOBSERVED"

    grant_policy_trust(tmp_path, 3, by="human:test")
    level3 = evaluate_policy(event, policy, observed_steps=1, root=tmp_path)
    assert (level3.decision, level3.rule_id, level3.trust_level) == ("ALLOW", "autorun_level3", 3)


def test_trust_level_2_does_not_allow_unlisted_web_domain(tmp_path):
    policy = _bare_policy(
        web=WebPolicy(allowed_domains=("api.example.com",)), trust=TrustPolicy(max_level=3)
    )
    grant_policy_trust(tmp_path, 2, by="human:test")
    decision = evaluate_policy(
        _normalize(_web_tool_event()), policy, observed_steps=1, root=tmp_path
    )
    assert decision.decision == "ASK"
    assert decision.trust_level == 2


def test_trust_level_3_allows_unlisted_web_domain(tmp_path):
    policy = _bare_policy(
        web=WebPolicy(allowed_domains=("api.example.com",)), trust=TrustPolicy(max_level=3)
    )
    grant_policy_trust(tmp_path, 3, by="human:test")
    decision = evaluate_policy(
        _normalize(_web_tool_event()), policy, observed_steps=1, root=tmp_path
    )
    assert decision.decision == "ALLOW"
    assert decision.rule_id == "autorun_level3"


def test_damaged_trust_file_is_unobserved_for_external_variable(tmp_path):
    trust_path = tmp_path / ".hyodo" / "policy-trust.json"
    trust_path.parent.mkdir(parents=True)
    trust_path.write_text("{not json", encoding="utf-8")
    policy = _bare_policy(ask_tools=("send_email",), trust=TrustPolicy(max_level=3))
    event = _normalize(_event(tool={"name": "send_email", "args_digest": None, "paths": []}))
    decision = evaluate_policy(event, policy, observed_steps=1, root=tmp_path)
    assert decision.decision == "UNOBSERVED"
    assert decision.rule_id == "trust_grant_unobserved"


def test_trust_missing_does_not_block_clean_event(tmp_path):
    policy = _bare_policy(allowed_tools=("search",), trust=TrustPolicy(max_level=3))
    decision = evaluate_policy(_normalize(_event()), policy, root=tmp_path)
    assert decision.decision == "ALLOW"


def test_existing_policy_shape_stays_backward_compatible(tmp_path):
    policy = PolicyConfig(
        schema=POLICY_SCHEMA_ID,
        max_steps=10,
        allowed_tools=("search",),
        blocked_path_globs=(),
    )
    event = _normalize(_event())
    without_root = evaluate_policy(event, policy, observed_steps=1)
    with_root = evaluate_policy(event, policy, observed_steps=1, root=tmp_path)
    assert without_root.decision == with_root.decision == "ALLOW"
    assert without_root.trust_level == with_root.trust_level == 1


@pytest.mark.parametrize("value", ["true", "false", '"yes"', "1"])
def test_require_mission_prompt_config(tmp_path, value):
    path = tmp_path / "policy.toml"
    path.write_text('schema = "hyodo.policy/v1"\nrequire_mission_prompt = ' + value)
    if value in ("true", "false"):
        assert load_policy_config(path).require_mission_prompt is (value == "true")
    else:
        with pytest.raises(PolicyConfigError, match="require_mission_prompt must be a boolean"):
            load_policy_config(path)


def test_digest_only_url_cannot_pass_credential_boundary():
    from hyodo.events import strip_full_bodies

    event = strip_full_bodies(
        _normalize(_web_tool_event(urls=[{"domain": "api.example.com", "digest": "abcdef123456"}]))
    )
    decision = evaluate_policy(event, _bare_policy(web=WebPolicy()))
    assert decision.decision == "UNOBSERVED"
    assert decision.rule_id == "web_credential_path_unobserved"


def test_legacy_path_credential_deny():
    event = _web_tool_event(urls=[{"domain": "api.example.com", "path": "/.env"}])
    decision = evaluate_policy(event, _bare_policy(web=WebPolicy()))
    assert decision.decision == "DENY"
    assert decision.rule_id == "web_credential_path_denied"
