from __future__ import annotations

from hyodo.nameplate import (
    AGENT_NAMEPLATE_SCHEMA_VERSION,
    UNOBSERVED,
    actor_id_linkage,
    build_nameplate,
    validate_nameplate,
    validate_nameplate_for_artifact,
)

SHA = "a" * 40
OBSERVED_AT = "2026-09-18T06:00:00+00:00"


def _nameplate(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": AGENT_NAMEPLATE_SCHEMA_VERSION,
        "actor_id": "builder-01",
        "role": "builder",
        "host": "claude-code",
        "provider": "anthropic",
        "model": "claude-observed",
        "mode": "interactive",
        "session_id": "session-01",
        "github_actor": "lofibrainwav",
        "observed_at": OBSERVED_AT,
        "repo": "lofibrainwav/HyoDo",
        "exact_artifact_sha": SHA,
    }
    value.update(overrides)
    return value


def test_valid_builder_nameplate() -> None:
    ok, reasons, normalized = validate_nameplate(_nameplate())
    assert ok, reasons
    assert normalized is not None
    assert normalized["role"] == "builder"


def test_valid_verifier_nameplate() -> None:
    ok, reasons, normalized = validate_nameplate(_nameplate(role="verifier"))
    assert ok, reasons
    assert normalized is not None
    assert normalized["role"] == "verifier"


def test_unknown_runtime_fields_become_unobserved() -> None:
    nameplate = build_nameplate(
        actor_id="observer-01",
        role="observer",
        repo="lofibrainwav/HyoDo",
        exact_artifact_sha=SHA,
        observed_at=OBSERVED_AT,
        runtime={},
    )
    assert nameplate["host"] == UNOBSERVED
    assert nameplate["provider"] == UNOBSERVED
    assert nameplate["model"] == UNOBSERVED
    assert nameplate["mode"] == UNOBSERVED
    assert nameplate["session_id"] == UNOBSERVED
    assert nameplate["github_actor"] == UNOBSERVED


def test_harness_actor_observation_does_not_infer_role() -> None:
    nameplate = build_nameplate(
        actor_id=None,
        role=None,
        repo="lofibrainwav/HyoDo",
        exact_artifact_sha=SHA,
        observed_at=OBSERVED_AT,
        runtime={"actor_id": "harness-agent-01"},
    )
    assert nameplate["actor_id"] == "harness-agent-01"
    assert nameplate["role"] == UNOBSERVED


def test_invalid_role_rejected() -> None:
    ok, reasons, normalized = validate_nameplate(_nameplate(role="architect"))
    assert not ok
    assert normalized is None
    assert "invalid_field:role" in reasons


def test_malformed_artifact_sha_rejected() -> None:
    ok, reasons, normalized = validate_nameplate(_nameplate(exact_artifact_sha="not-a-sha"))
    assert not ok
    assert normalized is None
    assert "invalid_field:exact_artifact_sha" in reasons


def test_unknown_field_rejected() -> None:
    ok, reasons, normalized = validate_nameplate(_nameplate(authority="merge"))
    assert not ok
    assert normalized is None
    assert "unsupported_field:authority" in reasons


def test_nameplate_has_no_authority_contract() -> None:
    for field in ("authority", "approval", "merge_permission"):
        ok, reasons, normalized = validate_nameplate(_nameplate(**{field: "yes"}))
        assert not ok
        assert normalized is None
        assert f"unsupported_field:{field}" in reasons


def test_exact_artifact_binding_is_required() -> None:
    ok, reasons, normalized = validate_nameplate_for_artifact(_nameplate(), SHA)
    assert ok, reasons
    assert normalized is not None

    ok, reasons, normalized = validate_nameplate_for_artifact(_nameplate(), "b" * 40)
    assert not ok
    assert normalized is None
    assert reasons == ["artifact_sha_mismatch"]


def test_existing_actor_id_can_be_linked_without_becoming_authentication() -> None:
    assert actor_id_linkage(_nameplate(), "builder-01") == "MATCH"
    assert actor_id_linkage(_nameplate(), "other-agent") == "MISMATCH"
    assert actor_id_linkage(_nameplate(actor_id=UNOBSERVED), "builder-01") == "UNOBSERVED"
