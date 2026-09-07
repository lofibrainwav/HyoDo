"""Tests for ``hyodo connect``: dry run, --write, --status, shadow mode, and
the Claude Code hook contract (``policy check``/``event record --hook
claude-code``).
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.connect import (
    CONNECT_RELATIVE_PATH,
    map_claude_code_hook_payload,
)

runner = CliRunner()


def _init_repo(tmp_path: Path) -> Path:
    (tmp_path / ".claude").mkdir()
    return tmp_path


# --------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------


def test_detect_reports_present_and_absent_harnesses(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    result = runner.invoke(app, ["connect", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["detected"]["claude-code"] is True
    assert payload["detected"]["pre-commit"] is False
    assert payload["detected"]["github-actions"] is False
    assert set(payload["unobserved"]) == {"cursor", "codex"}
    # Detection never writes anything.
    assert not (tmp_path / ".hyodo").exists()


# --------------------------------------------------------------------------
# Dry run
# --------------------------------------------------------------------------


def test_dry_run_writes_nothing_and_prints_file_list(tmp_path: Path) -> None:
    result = runner.invoke(app, ["connect", "claude-code", "--root", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "would create" in result.output
    assert ".claude/settings.json" in result.output
    assert not (tmp_path / ".claude" / "settings.json").exists()


def test_dry_run_json_includes_planned_content(tmp_path: Path) -> None:
    result = runner.invoke(app, ["connect", "claude-code", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["write"] is False
    assert payload["status"] == "would_write"
    files = payload["files"]
    assert len(files) == 1
    assert files[0]["path"] == ".claude/settings.json"
    assert files[0]["existed_before"] is False
    settings = json.loads(files[0]["content"])
    pre = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    post = settings["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
    assert pre == "hyodo policy check --stdin --hook claude-code --root ."
    assert post == "hyodo event record --stdin --hook claude-code --policy .hyodo/policy.toml"
    assert not (tmp_path / ".claude" / "settings.json").exists()


def test_generated_claude_code_hook_json_matches_documented_shape(tmp_path: Path) -> None:
    """The generated hooks JSON validates against the shape the spec documents:
    ``hooks.PreToolUse``/``PostToolUse`` -> [{"matcher", "hooks": [{"type",
    "command"}]}]."""
    result = runner.invoke(
        app, ["connect", "claude-code", "--write", "--yes", "--root", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    for event_name in ("PreToolUse", "PostToolUse"):
        entries = settings["hooks"][event_name]
        assert isinstance(entries, list)
        assert len(entries) == 1
        entry = entries[0]
        assert entry["matcher"] == "*"
        hook = entry["hooks"][0]
        assert hook["type"] == "command"
        assert isinstance(hook["command"], str)
        assert hook["command"].startswith("hyodo ")


# --------------------------------------------------------------------------
# --write / idempotency
# --------------------------------------------------------------------------


def test_write_creates_exact_files_with_expected_content(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["connect", "github-actions", "--write", "--yes", "--root", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    workflow = tmp_path / ".github" / "workflows" / "hyodo.yml"
    assert workflow.is_file()
    text = workflow.read_text()
    assert "hyodo-check" in text
    assert "actions/checkout@" in text
    assert (tmp_path / ".hyodo" / "connect.json").is_file()


def test_second_write_is_idempotent(tmp_path: Path) -> None:
    first = runner.invoke(
        app, ["connect", "pre-commit", "--write", "--yes", "--root", str(tmp_path)]
    )
    assert first.exit_code == 0, first.output
    config_path = tmp_path / ".pre-commit-config.yaml"
    mtime_before = config_path.stat().st_mtime_ns
    content_before = config_path.read_text()

    second = runner.invoke(
        app, ["connect", "pre-commit", "--write", "--yes", "--root", str(tmp_path), "--json"]
    )
    assert second.exit_code == 0, second.output
    payload = json.loads(second.output)
    assert payload["status"] == "up_to_date"
    assert config_path.read_text() == content_before
    assert config_path.stat().st_mtime_ns == mtime_before
    # No backup should ever be created for a file HyoDo itself created.
    assert not (tmp_path / ".pre-commit-config.yaml.bak").exists()


def test_first_write_backs_up_a_foreign_file(tmp_path: Path) -> None:
    config_path = tmp_path / ".pre-commit-config.yaml"
    original = "repos:\n  - repo: https://github.com/psf/black\n    rev: 24.0.0\n    hooks:\n      - id: black\n"
    config_path.write_text(original, encoding="utf-8")

    result = runner.invoke(
        app, ["connect", "pre-commit", "--write", "--yes", "--root", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    backup_path = tmp_path / ".pre-commit-config.yaml.bak"
    assert backup_path.is_file()
    assert backup_path.read_text() == original
    merged = config_path.read_text()
    assert "psf/black" in merged
    assert "hyodo-check" in merged


def test_unknown_target_exits_two(tmp_path: Path) -> None:
    result = runner.invoke(app, ["connect", "not-a-real-target", "--root", str(tmp_path)])
    assert result.exit_code == 2, result.output


def test_unobserved_target_exits_two_with_honest_message(tmp_path: Path) -> None:
    for target in ("cursor", "codex"):
        result = runner.invoke(app, ["connect", target, "--root", str(tmp_path), "--json"])
        assert result.exit_code == 2, result.output
        payload = json.loads(result.output)
        assert payload["status"] == "unobserved"
        assert "not verified" in payload["message"]
    # Never writes for an unsupported target, even with --write.
    result = runner.invoke(app, ["connect", "cursor", "--write", "--yes", "--root", str(tmp_path)])
    assert result.exit_code == 2, result.output
    assert not (tmp_path / ".cursor").exists()


# --------------------------------------------------------------------------
# --status / drift
# --------------------------------------------------------------------------


def test_status_reports_no_drift_after_write(tmp_path: Path) -> None:
    write = runner.invoke(
        app, ["connect", "claude-code", "--write", "--yes", "--root", str(tmp_path)]
    )
    assert write.exit_code == 0, write.output
    status = runner.invoke(app, ["connect", "--status", "--root", str(tmp_path), "--json"])
    assert status.exit_code == 0, status.output
    payload = json.loads(status.output)
    assert payload["drift"] is False
    assert all(t["status"] == "ok" for t in payload["targets"])


def test_status_reports_drift_as_unobserved(tmp_path: Path) -> None:
    write = runner.invoke(
        app, ["connect", "claude-code", "--write", "--yes", "--root", str(tmp_path)]
    )
    assert write.exit_code == 0, write.output
    settings_path = tmp_path / ".claude" / "settings.json"
    settings_path.write_text(settings_path.read_text() + "\n# tampered\n", encoding="utf-8")

    status = runner.invoke(app, ["connect", "--status", "--root", str(tmp_path), "--json"])
    assert status.exit_code == 2, status.output
    payload = json.loads(status.output)
    assert payload["drift"] is True
    drifted = [t for t in payload["targets"] if t["status"] != "ok"]
    assert drifted
    assert drifted[0]["reason"] == "digest_mismatch"


def test_status_with_nothing_connected_is_clean(tmp_path: Path) -> None:
    result = runner.invoke(app, ["connect", "--status", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["targets"] == []
    assert payload["drift"] is False


# --------------------------------------------------------------------------
# Shadow mode content
# --------------------------------------------------------------------------


def test_shadow_write_adds_shadow_flag_to_generated_hook_commands(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["connect", "claude-code", "--shadow", "--write", "--yes", "--root", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    pre = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    post = settings["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
    assert pre.endswith("--shadow")
    assert post.endswith("--shadow")

    state = json.loads((tmp_path / CONNECT_RELATIVE_PATH).read_text())
    assert state["targets"]["claude-code"]["shadow"] is True


def test_shadow_has_no_effect_on_pre_commit_content(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["connect", "pre-commit", "--shadow", "--write", "--yes", "--root", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    state = json.loads((tmp_path / CONNECT_RELATIVE_PATH).read_text())
    assert state["targets"]["pre-commit"]["shadow"] is False


# --------------------------------------------------------------------------
# Claude Code hook payload mapping
# --------------------------------------------------------------------------


def test_map_claude_code_hook_payload_maps_bash_tool(tmp_path: Path) -> None:
    payload = {
        "session_id": "run-abc",
        "tool_use_id": "evt-1",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "echo hi"},
        "cwd": str(tmp_path),
    }
    mapped, err = map_claude_code_hook_payload(payload, tmp_path)
    assert err is None
    assert mapped is not None
    assert mapped.raw["event_id"] == "evt-1"
    assert mapped.raw["run_id"] == "run-abc"
    assert mapped.raw["kind"] == "tool_call"
    assert mapped.raw["actor"] == "agent"
    assert mapped.raw["tool"]["name"] == "Bash"
    assert mapped.raw["tool"]["args_digest"] is not None
    # The hook already uses session_id as run_id; actor_id additionally
    # carries the same value (Ruling 2).
    assert mapped.raw["actor_id"] == "run-abc"
    assert mapped.raw["actor_id"] == mapped.raw["run_id"]


def test_map_claude_code_hook_payload_rejects_malformed(tmp_path: Path) -> None:
    mapped, err = map_claude_code_hook_payload({"not": "a hook payload"}, tmp_path)
    assert mapped is None
    assert err is not None


# --------------------------------------------------------------------------
# Shadow hook end-to-end: exit 0, ledger carries policy.shadow: true
# --------------------------------------------------------------------------


def _write_deny_policy(root: Path) -> Path:
    policy_dir = root / ".hyodo"
    policy_dir.mkdir(parents=True, exist_ok=True)
    policy_path = policy_dir / "policy.toml"
    policy_path.write_text(
        'schema = "hyodo.policy/v1"\nallowed_tools = ["Read"]\n', encoding="utf-8"
    )
    return policy_path


def _hook_payload(event_name: str, event_id: str, run_id: str, root: Path) -> str:
    return json.dumps(
        {
            "session_id": run_id,
            "tool_use_id": event_id,
            "hook_event_name": event_name,
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /"},
            "cwd": str(root),
        }
    )


def test_policy_check_hook_shadow_exits_zero_on_deny(tmp_path: Path) -> None:
    _write_deny_policy(tmp_path)
    result = runner.invoke(
        app,
        [
            "policy",
            "check",
            "--stdin",
            "--hook",
            "claude-code",
            "--root",
            str(tmp_path),
            "--shadow",
            "--json",
        ],
        input=_hook_payload("PreToolUse", "evt-1", "run-1", tmp_path),
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["decision"] == "DENY"
    assert payload["shadow"] is True
    assert payload["exit_code"] == 0


def test_policy_check_hook_enforced_follows_decision(tmp_path: Path) -> None:
    _write_deny_policy(tmp_path)
    result = runner.invoke(
        app,
        [
            "policy",
            "check",
            "--stdin",
            "--hook",
            "claude-code",
            "--root",
            str(tmp_path),
            "--json",
        ],
        input=_hook_payload("PreToolUse", "evt-2", "run-2", tmp_path),
    )
    assert result.exit_code == 2, result.output
    payload = json.loads(result.stdout)
    assert payload["decision"] == "DENY"
    assert payload["exit_code"] == 2


def test_policy_check_hook_allow_exits_zero(tmp_path: Path) -> None:
    policy_dir = tmp_path / ".hyodo"
    policy_dir.mkdir(parents=True, exist_ok=True)
    (policy_dir / "policy.toml").write_text('schema = "hyodo.policy/v1"\n', encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "policy",
            "check",
            "--stdin",
            "--hook",
            "claude-code",
            "--root",
            str(tmp_path),
            "--json",
        ],
        input=json.dumps(
            {
                "session_id": "run-3",
                "tool_use_id": "evt-3",
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_input": {"file_path": str(tmp_path / "x.txt")},
                "cwd": str(tmp_path),
            }
        ),
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["decision"] == "ALLOW"
    assert payload["exit_code"] == 0


def test_event_record_shadow_hook_records_shadow_true_and_exits_zero(tmp_path: Path) -> None:
    policy_path = _write_deny_policy(tmp_path)
    result = runner.invoke(
        app,
        [
            "event",
            "record",
            "--stdin",
            "--hook",
            "claude-code",
            "--policy",
            str(policy_path),
            "--shadow",
            "--json",
        ],
        input=_hook_payload("PostToolUse", "evt-post-1", "run-1", tmp_path),
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["shadow"] is True
    assert payload["decision"] == "DENY"

    ledger = tmp_path / ".hyodo" / "agent-events.jsonl"
    events = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    assert len(events) == 1
    assert events[0]["policy"]["shadow"] is True
    assert events[0]["policy"]["decision"] == "DENY"


def test_event_record_hook_fire_and_forget_exits_zero_regardless_of_decision(
    tmp_path: Path,
) -> None:
    policy_path = _write_deny_policy(tmp_path)
    result = runner.invoke(
        app,
        [
            "event",
            "record",
            "--stdin",
            "--hook",
            "claude-code",
            "--policy",
            str(policy_path),
            "--json",
        ],
        input=_hook_payload("PostToolUse", "evt-post-2", "run-1", tmp_path),
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["decision"] == "DENY"
    assert payload["shadow"] is False


def test_event_record_shadow_requires_policy(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["event", "record", "--stdin", "--shadow", "--json"],
        input=json.dumps({"not": "an event"}),
    )
    assert result.exit_code == 2, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is False


# --------------------------------------------------------------------------
# Judge findings: non-interactive consent, fire-and-forget hooks, unobserved steps
# --------------------------------------------------------------------------


def test_write_without_yes_is_refused_when_not_interactive(tmp_path: Path) -> None:
    """Silence is not consent: a non-TTY caller must pass --yes to write."""
    result = runner.invoke(app, ["connect", "github-actions", "--write", "--root", str(tmp_path)])
    assert result.exit_code == 1, result.output
    assert "confirmation_required" in result.output
    assert not (tmp_path / ".github" / "workflows" / "hyodo.yml").exists()
    assert not (tmp_path / ".hyodo" / "connect.json").exists()


def test_write_without_yes_json_is_refused_with_receipt(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["connect", "github-actions", "--write", "--json", "--root", str(tmp_path)]
    )
    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["exit_code"] == 1
    assert payload["reasons"][0].startswith("confirmation_required")


def test_hook_event_that_fails_validation_never_blocks(tmp_path: Path) -> None:
    """PostToolUse is fire-and-forget: an unrecordable event exits 0, not 1."""
    (tmp_path / ".hyodo").mkdir()
    payload = {
        "hook_event_name": "PostToolUse",
        "session_id": "run-1",
        "tool_use_id": "evt-1",
        "tool_name": "WebFetch",
        "tool_input": {"url": "not-a-url"},
        "cwd": str(tmp_path),
    }
    result = runner.invoke(
        app,
        ["event", "record", "--stdin", "--hook", "claude-code", "--root", str(tmp_path), "--json"],
        input=json.dumps(payload),
    )
    assert result.exit_code == 0, result.output
    receipt = json.loads(result.output)
    assert receipt["ok"] is False
    assert receipt["exit_code"] == 0
    assert any("tool.urls" in reason for reason in receipt["reasons"])
    assert not (tmp_path / ".hyodo" / "agent-events.jsonl").exists()


def test_mapped_hook_event_tags_an_unobserved_step_index(tmp_path: Path) -> None:
    """An unreadable ledger yields a placeholder step_index that is tagged, not silent."""
    (tmp_path / ".hyodo").mkdir()
    (tmp_path / ".hyodo" / "agent-events.jsonl").mkdir()  # a directory cannot be read
    payload = {
        "hook_event_name": "PreToolUse",
        "session_id": "run-1",
        "tool_use_id": "evt-1",
        "tool_name": "Bash",
        "tool_input": {"command": "ls"},
        "cwd": str(tmp_path),
    }
    mapped, err = map_claude_code_hook_payload(payload, tmp_path)
    assert err is None
    assert mapped is not None
    assert mapped.raw["step_index"] == 0
    assert "step_index:unobserved" in mapped.raw["meta"]["tags"]
