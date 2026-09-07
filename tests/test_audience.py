"""Audience profiles are a presentation lens only -- never a decision input.

Covers: profile resolution order, invalid-value handling, byte-identical
--json payloads (minus the added "audience" key) and exit codes across
profiles for check/safe/policy check, vibe/professional verdict lines
carrying the same n/m figures as engineer, the vibe RED word on DENY,
--explain fallback to engineer text, rule_id parity across the three
explanation tables, and `hyodo start`'s single-question onboarding.
"""

from __future__ import annotations

import builtins
import json
import uuid
from pathlib import Path

import pytest
from typer.testing import CliRunner

import hyodo.cli.main as cli
from hyodo.audience import (
    VALID_PROFILES,
    AudienceProfile,
    InvalidAudienceError,
    load_config,
    resolve_audience,
    write_config,
)
from hyodo.events import AGENT_EVENT_SCHEMA_VERSION, content_digest
from hyodo.verdict import (
    EXPLANATIONS,
    EXPLANATIONS_PROFESSIONAL,
    EXPLANATIONS_VIBE,
    explain_decision,
)

runner = CliRunner()


# --------------------------------------------------------------------------- #
# hyodo.audience: resolution order, config I/O, invalid values
# --------------------------------------------------------------------------- #


def test_default_is_engineer_with_no_flag_env_or_config(tmp_path: Path):
    assert resolve_audience(tmp_path) == AudienceProfile(profile="engineer", domain=None)


def test_missing_and_unreadable_config_never_errors(tmp_path: Path):
    # No .hyodo directory at all.
    assert resolve_audience(tmp_path).profile == "engineer"
    # .hyodo exists but config.toml is malformed TOML.
    hyodo_dir = tmp_path / ".hyodo"
    hyodo_dir.mkdir()
    (hyodo_dir / "config.toml").write_text("not [ valid toml", encoding="utf-8")
    assert load_config(tmp_path) is None
    assert resolve_audience(tmp_path).profile == "engineer"


def test_config_file_supplies_profile_and_domain(tmp_path: Path):
    write_config(tmp_path, "professional", domain="law")
    resolved = resolve_audience(tmp_path)
    assert resolved == AudienceProfile(profile="professional", domain="law")


def test_domain_only_applies_to_professional(tmp_path: Path):
    hyodo_dir = tmp_path / ".hyodo"
    hyodo_dir.mkdir()
    (hyodo_dir / "config.toml").write_text(
        'schema = "hyodo.config/v1"\n\n[audience]\nprofile = "vibe"\ndomain = "law"\n',
        encoding="utf-8",
    )
    resolved = resolve_audience(tmp_path)
    assert resolved.profile == "vibe"
    assert resolved.domain is None


def test_flag_overrides_env_overrides_config(tmp_path: Path):
    write_config(tmp_path, "professional")
    assert resolve_audience(tmp_path, flag="vibe", env="professional").profile == "vibe"
    assert resolve_audience(tmp_path, env="vibe").profile == "vibe"
    assert resolve_audience(tmp_path).profile == "professional"


def test_invalid_flag_or_env_raises_but_invalid_config_falls_back(tmp_path: Path):
    with pytest.raises(InvalidAudienceError) as exc:
        resolve_audience(tmp_path, flag="hacker")
    assert str(exc.value) == "invalid_audience:hacker"
    with pytest.raises(InvalidAudienceError):
        resolve_audience(tmp_path, env="hacker")

    hyodo_dir = tmp_path / ".hyodo"
    hyodo_dir.mkdir()
    (hyodo_dir / "config.toml").write_text(
        'schema = "hyodo.config/v1"\n\n[audience]\nprofile = "hacker"\n', encoding="utf-8"
    )
    # A bad config-file value is never an error -- falls through to default.
    assert resolve_audience(tmp_path).profile == "engineer"


def test_write_config_rejects_unknown_profile(tmp_path: Path):
    with pytest.raises(ValueError, match="invalid_audience:hacker"):
        write_config(tmp_path, "hacker")


# --------------------------------------------------------------------------- #
# CLI: invalid --audience exits 2 UNOBSERVED with a reason
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("args", [["check", ".", "--quiet"], ["safe", ".", "--quiet"]])
def test_invalid_audience_flag_exits_two(args):
    result = runner.invoke(cli.app, [*args, "--audience", "hacker"])
    assert result.exit_code == 2
    assert "invalid_audience:hacker" in result.output


def test_invalid_audience_flag_json_shape():
    result = runner.invoke(cli.app, ["check", ".", "--json", "--audience", "hacker"])
    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["decision"] == "UNOBSERVED"
    assert payload["reason"] == "invalid_audience:hacker"
    assert payload["exit_code"] == 2


def test_invalid_audience_env_exits_two(monkeypatch):
    monkeypatch.setenv("HYODO_AUDIENCE", "hacker")
    result = runner.invoke(cli.app, ["check", ".", "--quiet"])
    assert result.exit_code == 2
    assert "invalid_audience:hacker" in result.output


# --------------------------------------------------------------------------- #
# check / safe / policy check: identical exit code + --json payload (minus
# "audience"), across all three profiles, on the same input.
# --------------------------------------------------------------------------- #


def _json_payloads(args: list[str]) -> dict[str, tuple[int, dict]]:
    out = {}
    for profile in VALID_PROFILES:
        result = runner.invoke(cli.app, [*args, "--json", "--audience", profile])
        out[profile] = (result.exit_code, json.loads(result.output))
    return out


def _payloads_identical_minus_audience(payloads: dict[str, tuple[int, dict]]) -> bool:
    """Return True only when every profile agrees on exit code and payload minus audience."""
    codes = {code for code, _ in payloads.values()}
    assert len(codes) == 1, payloads
    baseline = dict(payloads["engineer"][1])
    baseline.pop("audience", None)
    for profile, (_code, payload) in payloads.items():
        assert payload.get("audience") == profile
        stripped = dict(payload)
        stripped.pop("audience", None)
        assert stripped == baseline, (profile, payload)
    return True


def test_check_json_payload_identical_across_profiles(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(cli, "find_repo_root", lambda target: tmp_path)
    for name in ("run_pyright_check", "run_ruff_check", "run_pytest_check", "run_sbom_check"):
        monkeypatch.setattr(cli, name, lambda *args: cli.GateResult(cli.GateStatus.PASS, "test"))
    assert _payloads_identical_minus_audience(_json_payloads(["check", str(tmp_path)]))


def test_safe_json_payload_identical_across_profiles(tmp_path: Path):
    target = tmp_path / "danger.py"
    target.write_text('import os\nos.system("rm -rf /")\n')
    assert _payloads_identical_minus_audience(_json_payloads(["safe", str(target)]))


def test_policy_check_json_payload_identical_across_profiles(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    args = [
        "policy",
        "check",
        "--file",
        str(root / "examples/fde-evidence-spine/sample-tool-call.json"),
        "--config",
        str(root / "examples/fde-evidence-spine/policy.toml"),
        "--root",
        str(tmp_path),
    ]
    assert _payloads_identical_minus_audience(_json_payloads(args))


# --------------------------------------------------------------------------- #
# Verdict line wording: same n/m figures across profiles; RED on vibe DENY.
# --------------------------------------------------------------------------- #


def test_vibe_and_professional_verdict_lines_carry_same_figures_as_engineer(tmp_path: Path):
    target = tmp_path / "danger.py"
    target.write_text('import os\nos.system("rm -rf /")\n')
    lines = {}
    for profile in VALID_PROFILES:
        result = runner.invoke(cli.app, ["safe", str(target), "--quiet", "--audience", profile])
        lines[profile] = result.output.strip()
    assert "1/1 files" in lines["engineer"]
    for profile in ("vibe", "professional"):
        assert "1/1 files" in lines[profile], lines[profile]


def _event(tool: dict[str, object], run_id: str) -> dict[str, object]:
    return {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "run_id": run_id,
        "ts": "2026-09-06T12:00:00+00:00",
        "kind": "tool_call",
        "step_index": 0,
        "actor": "agent",
        "tool": tool,
        "io": {"input_digest": content_digest("in"), "output_digest": None},
        "meta": {"model": "test-model", "tags": []},
    }


def test_deny_in_vibe_contains_red(tmp_path: Path):
    policy_path = tmp_path / ".hyodo" / "policy.toml"
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(
        'schema = "hyodo.policy/v1"\nallowed_tools = ["safe_tool"]\n', encoding="utf-8"
    )
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(_event({"name": "blocked_tool", "args_digest": None}, "deny-run")),
        encoding="utf-8",
    )
    result = runner.invoke(
        cli.app,
        [
            "policy",
            "check",
            "--file",
            str(event_path),
            "--config",
            str(policy_path),
            "--root",
            str(tmp_path),
            "--quiet",
            "--audience",
            "vibe",
        ],
    )
    assert result.exit_code == 1
    assert "RED" in result.output


# --------------------------------------------------------------------------- #
# --explain: fallback to engineer text when a profile entry is missing.
# --------------------------------------------------------------------------- #


def test_explain_falls_back_to_engineer_text_when_profile_entry_missing():
    # A rule_id vibe has no dedicated entry for still resolves to vibe's own
    # (command, decision, None) text -- the profile's own fallback, not a
    # jump straight to engineer.
    text = explain_decision("policy check", "ALLOW", "never_seen_rule_xyz", audience="vibe")
    assert text == EXPLANATIONS_VIBE["policy check", "ALLOW", None]
    assert text != EXPLANATIONS["policy check", "ALLOW", None]

    # Only when the profile table has *no* entry at all for the key (neither
    # the exact rule_id nor the decision-level None) does it fall back to
    # engineer's exact text -- never a fabricated string.
    key = ("check", "PASS", None)
    saved = EXPLANATIONS_VIBE.pop(key)
    try:
        assert explain_decision(*key[:2], audience="vibe") == EXPLANATIONS[key]
    finally:
        EXPLANATIONS_VIBE[key] = saved


# --------------------------------------------------------------------------- #
# Every engineer rule_id entry has a vibe and a professional counterpart.
# --------------------------------------------------------------------------- #


def test_every_engineer_entry_has_vibe_and_professional_counterpart():
    assert set(EXPLANATIONS_VIBE.keys()) == set(EXPLANATIONS.keys())
    assert set(EXPLANATIONS_PROFESSIONAL.keys()) == set(EXPLANATIONS.keys())


# --------------------------------------------------------------------------- #
# `hyodo start`: at most one question; writes nothing non-interactively.
# --------------------------------------------------------------------------- #


def test_start_noninteractive_asks_nothing_and_writes_nothing(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    cli.start()
    assert not (tmp_path / ".hyodo" / "config.toml").exists()


def test_start_interactive_asks_exactly_one_question_and_writes_on_explicit_answer(
    monkeypatch, tmp_path: Path
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    prompts: list[str] = []

    def fake_input(prompt: str = "") -> str:
        prompts.append(prompt)
        return "3"

    monkeypatch.setattr(builtins, "input", fake_input)
    cli.start()
    assert len(prompts) == 1
    written = (tmp_path / ".hyodo" / "config.toml").read_text(encoding="utf-8")
    assert 'profile = "professional"' in written


def test_start_interactive_unrecognized_answer_writes_nothing(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(builtins, "input", lambda prompt="": "banana")
    cli.start()
    assert not (tmp_path / ".hyodo" / "config.toml").exists()
