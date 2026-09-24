"""Tests for the untracked policy trust grant store and CLI."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

import hyodo.policy_trust as policy_trust
from hyodo.cli.main import app
from hyodo.policy import POLICY_SCHEMA_ID
from hyodo.policy_trust import (
    POLICY_TRUST_ENV_VAR,
    POLICY_TRUST_MAX_AGE,
    POLICY_TRUST_RELATIVE_PATH,
    POLICY_TRUST_SCHEMA_ID,
    SCOPE_EYE_KEEP,
    SCOPE_POLICY_ASK,
    default_granted_by,
    effective_trust_level,
    grant_policy_trust,
    load_policy_trust,
    policy_trust_path,
    resolve_policy_trust_grant,
)
from hyodo.user_state import workspace_identity

runner = CliRunner()


def test_load_policy_trust_missing_file_is_distinct(tmp_path: Path):
    state, error = load_policy_trust(tmp_path)
    assert state is None
    assert error == "trust_missing"


def test_grant_and_load_round_trip(tmp_path: Path):
    state = grant_policy_trust(tmp_path, 2, by="human:test")
    assert state.level == 2
    loaded, error = load_policy_trust(tmp_path)
    assert error is None
    assert loaded == state
    payload = json.loads(policy_trust_path(tmp_path).read_text(encoding="utf-8"))
    assert payload["schema"] == POLICY_TRUST_SCHEMA_ID
    assert payload["workspace_id"] == workspace_identity(tmp_path)
    assert payload["policy_digest"] == "absent"
    assert set(payload["scopes"]) == {SCOPE_POLICY_ASK, SCOPE_EYE_KEEP}
    assert not (tmp_path / POLICY_TRUST_RELATIVE_PATH).exists()


def test_grant_accumulates_history(tmp_path: Path):
    grant_policy_trust(tmp_path, 1, by="human:a")
    second = grant_policy_trust(tmp_path, 2, by="human:b")
    assert [(item.level, item.granted_by) for item in second.history] == [(1, "human:a")]
    third = grant_policy_trust(tmp_path, 3, by="human:c")
    assert [item.level for item in third.history] == [1, 2]


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ("{not json", "trust_invalid"),
        (json.dumps({"schema": "wrong", "level": 1}), "trust_invalid"),
        (
            json.dumps(
                {
                    "schema": POLICY_TRUST_SCHEMA_ID,
                    "level": 9,
                    "granted_at": "now",
                    "granted_by": "human:test",
                }
            ),
            "trust_invalid",
        ),
    ],
)
def test_malformed_trust_file_is_unobserved(tmp_path: Path, payload: str, error: str):
    path = policy_trust_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(payload, encoding="utf-8")
    state, actual = load_policy_trust(tmp_path)
    assert state is None
    assert actual == error


def test_preseeded_checkout_grant_carries_no_authority(tmp_path: Path):
    """A repository cannot ship its own policy trust grant."""
    path = tmp_path / POLICY_TRUST_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema": POLICY_TRUST_SCHEMA_ID,
                "workspace_id": workspace_identity(tmp_path),
                "policy_digest": "absent",
                "scopes": [SCOPE_POLICY_ASK, SCOPE_EYE_KEEP],
                "level": 3,
                "granted_at": "2020-01-01T00:00:00+00:00",
                "expires_at": "2999-01-01T00:00:00+00:00",
                "granted_by": "human:attacker",
                "history": [],
            }
        ),
        encoding="utf-8",
    )
    state, error = load_policy_trust(tmp_path)
    assert state is None
    assert error == "trust_missing"
    assert effective_trust_level(3, state) == 0


def test_grant_does_not_follow_a_copied_record(tmp_path: Path):
    original = tmp_path / "original"
    other = tmp_path / "other"
    original.mkdir()
    other.mkdir()
    grant_policy_trust(original, 3, by="human:test")
    target = policy_trust_path(other)
    target.parent.mkdir(parents=True)
    target.write_text(policy_trust_path(original).read_text(encoding="utf-8"), encoding="utf-8")
    state, error = load_policy_trust(other)
    assert state is None
    assert error == "trust_workspace_mismatch"


def test_grant_is_void_after_policy_file_changes(tmp_path: Path):
    policy_file = tmp_path / ".hyodo" / "policy.toml"
    policy_file.parent.mkdir(parents=True)
    policy_file.write_text(f'schema = "{POLICY_SCHEMA_ID}"\n', encoding="utf-8")
    grant_policy_trust(tmp_path, 3, by="human:test")
    assert load_policy_trust(tmp_path)[1] is None
    policy_file.write_text(f'schema = "{POLICY_SCHEMA_ID}"\nmax_steps = 99\n', encoding="utf-8")
    state, error = load_policy_trust(tmp_path)
    assert state is None
    assert error == "trust_policy_changed"


def test_grant_only_covers_its_scopes(tmp_path: Path):
    grant_policy_trust(tmp_path, 3, by="human:test", scopes=(SCOPE_POLICY_ASK,))
    assert load_policy_trust(tmp_path, scope=SCOPE_POLICY_ASK)[1] is None
    state, error = load_policy_trust(tmp_path, scope=SCOPE_EYE_KEEP)
    assert state is None
    assert error == "trust_scope_mismatch"


def test_grant_expires(tmp_path: Path):
    granted_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    grant_policy_trust(tmp_path, 3, by="human:test", now=granted_at)
    inside = granted_at + POLICY_TRUST_MAX_AGE - timedelta(seconds=1)
    assert load_policy_trust(tmp_path, now=inside)[1] is None
    state, error = load_policy_trust(tmp_path, now=granted_at + POLICY_TRUST_MAX_AGE)
    assert state is None
    assert error == "trust_expired"
    before = granted_at - timedelta(seconds=1)
    assert load_policy_trust(tmp_path, now=before)[1] == "trust_expired"


def test_effective_trust_level_is_capped(tmp_path: Path):
    state = grant_policy_trust(tmp_path, 3, by="human:test")
    assert effective_trust_level(2, state) == 2
    assert effective_trust_level(3, state) == 3


def test_effective_trust_level_without_grant_is_zero(tmp_path: Path):
    assert effective_trust_level(3, None) == 0


def test_default_granted_by(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("USER", "tester")
    monkeypatch.delenv("USERNAME", raising=False)
    assert default_granted_by() == "tester"


def test_resolve_noninteractive_requires_explicit_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(policy_trust, "_is_noninteractive", lambda: True)
    monkeypatch.delenv(POLICY_TRUST_ENV_VAR, raising=False)
    decision = resolve_policy_trust_grant(2, by="human:test", yes=True)
    assert not decision.approved
    assert POLICY_TRUST_ENV_VAR in decision.reason


def test_resolve_noninteractive_env_approves(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(policy_trust, "_is_noninteractive", lambda: True)
    monkeypatch.setenv(POLICY_TRUST_ENV_VAR, "1")
    decision = resolve_policy_trust_grant(2, by="human:test", yes=False)
    assert decision.approved
    assert decision.via == f"env:{POLICY_TRUST_ENV_VAR}"


def test_resolve_interactive_yes_skips_prompt(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(policy_trust, "_is_noninteractive", lambda: False)
    monkeypatch.setattr(
        "builtins.input", lambda _prompt="": (_ for _ in ()).throw(AssertionError())
    )
    decision = resolve_policy_trust_grant(2, by="human:test", yes=True)
    assert decision.approved
    assert decision.via == "prompt"


def test_resolve_interactive_decline(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(policy_trust, "_is_noninteractive", lambda: False)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "n")
    decision = resolve_policy_trust_grant(2, by="human:test", yes=False)
    assert not decision.approved
    assert decision.via == "declined"


def test_cli_policy_trust_grant_and_show(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv(POLICY_TRUST_ENV_VAR, "1")
    grant = runner.invoke(
        app,
        ["policy", "trust", "grant", "--level", "2", "--by", "tester", "--root", str(tmp_path)],
    )
    assert grant.exit_code == 0, grant.output
    show = runner.invoke(app, ["policy", "trust", "show", "--root", str(tmp_path), "--json"])
    assert show.exit_code == 0, show.output
    payload = json.loads(show.output)
    assert payload["granted_level"] == 2
    assert payload["effective_level"] == 2


def test_cli_policy_trust_rejects_invalid_level(tmp_path: Path):
    result = runner.invoke(
        app, ["policy", "trust", "grant", "--level", "9", "--root", str(tmp_path)]
    )
    assert result.exit_code == 2


def test_cli_policy_trust_show_applies_policy_cap(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv(POLICY_TRUST_ENV_VAR, "1")
    policy_path = tmp_path / ".hyodo" / "policy.toml"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(
        f'schema = "{POLICY_SCHEMA_ID}"\n\n[trust]\nmax_level = 1\n',
        encoding="utf-8",
    )
    grant_policy_trust(tmp_path, 3, by="human:test")
    result = runner.invoke(app, ["policy", "trust", "show", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["cap"] == 1
    assert payload["effective_level"] == 1
