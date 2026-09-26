"""Native hook root contract: an explicit ``--root`` wins over the payload cwd.

Without ``--root`` the payload ``cwd`` stays the fallback root (unchanged).
Both ``event record`` and ``policy check`` apply the same rule.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.events import AGENT_EVENTS_RELATIVE_PATH

runner = CliRunner()

_ALLOW_POLICY = 'schema = "hyodo.policy/v1"\nallowed_tools = ["Bash", "Shell"]\n'


def _payload(hook: str, cwd: Path, event_id: str) -> dict[str, object]:
    if hook == "claude-code":
        return {
            "session_id": "run-root",
            "tool_use_id": event_id,
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "printf safe"},
            "cwd": str(cwd),
        }
    if hook == "codex":
        return {
            "session_id": "run-root",
            "tool_use_id": event_id,
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "printf safe"},
            "cwd": str(cwd),
        }
    return {
        "conversation_id": "run-root",
        "tool_use_id": event_id,
        "hook_event_name": "preToolUse",
        "tool_name": "Shell",
        "tool_input": {"command": "printf safe"},
        "cwd": str(cwd),
    }


def _roots(tmp_path: Path) -> tuple[Path, Path]:
    root_a = tmp_path / "A"
    cwd_b = tmp_path / "B"
    (root_a / ".hyodo").mkdir(parents=True)
    (root_a / ".hyodo" / "policy.toml").write_text(_ALLOW_POLICY, encoding="utf-8")
    cwd_b.mkdir()
    return root_a, cwd_b


def _ledger(root: Path) -> list[dict[str, object]]:
    path = root / AGENT_EVENTS_RELATIVE_PATH
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


@pytest.mark.parametrize("hook", ["claude-code", "codex", "cursor"])
def test_explicit_root_wins_over_payload_cwd(
    tmp_path: Path, hook: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    root_a, cwd_b = _roots(tmp_path)
    monkeypatch.chdir(tmp_path)

    first = runner.invoke(
        app,
        ["event", "record", "--stdin", "--hook", hook, "--root", str(root_a), "--json"],
        input=json.dumps(_payload(hook, cwd_b, "evt-1")),
    )
    assert first.exit_code == 0, first.output
    events = _ledger(root_a)
    assert len(events) == 1
    assert events[0]["step_index"] == 0

    second = runner.invoke(
        app,
        ["event", "record", "--stdin", "--hook", hook, "--root", str(root_a), "--json"],
        input=json.dumps(_payload(hook, cwd_b, "evt-2")),
    )
    assert second.exit_code == 0, second.output
    events = _ledger(root_a)
    assert len(events) == 2
    # Step counting read A's ledger, not B's (which would restart at 0).
    assert events[1]["step_index"] == 1

    # Policy lookup and step budget come from A: B has no policy, so a
    # cwd-rooted check would be UNOBSERVED rather than ALLOW.
    check = runner.invoke(
        app,
        ["policy", "check", "--stdin", "--hook", hook, "--root", str(root_a), "--json"],
        input=json.dumps(_payload(hook, cwd_b, "evt-3")),
    )
    assert check.exit_code == 0, check.output
    assert json.loads(check.stdout)["decision"] == "ALLOW"

    assert not (cwd_b / ".hyodo").exists()


@pytest.mark.parametrize("hook", ["claude-code", "codex", "cursor"])
def test_no_root_keeps_payload_cwd_fallback(
    tmp_path: Path, hook: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    root_a, cwd_b = _roots(tmp_path)
    (cwd_b / ".hyodo").mkdir()
    (cwd_b / ".hyodo" / "policy.toml").write_text(_ALLOW_POLICY, encoding="utf-8")
    monkeypatch.chdir(root_a)

    record = runner.invoke(
        app,
        ["event", "record", "--stdin", "--hook", hook, "--json"],
        input=json.dumps(_payload(hook, cwd_b, "evt-1")),
    )
    assert record.exit_code == 0, record.output
    assert len(_ledger(cwd_b)) == 1
    assert _ledger(root_a) == []

    check = runner.invoke(
        app,
        ["policy", "check", "--stdin", "--hook", hook, "--json"],
        input=json.dumps(_payload(hook, cwd_b, "evt-2")),
    )
    assert check.exit_code == 0, check.output
    assert json.loads(check.stdout)["decision"] == "ALLOW"


def test_explicit_root_does_not_repair_missing_cwd(tmp_path: Path) -> None:
    root_a, _ = _roots(tmp_path)
    payload = {
        "hook_event_name": "UserPromptSubmit",
        "session_id": "run-root",
        "turn_id": "turn-1",
        "prompt": "hello",
        "model": "m",
        "permission_mode": "default",
        "cwd": "",
    }
    result = runner.invoke(
        app,
        ["event", "record", "--stdin", "--hook", "codex", "--root", str(root_a), "--json"],
        input=json.dumps(payload),
    )
    assert result.exit_code == 2, result.output
    assert json.loads(result.stdout)["reasons"] == ["missing_field:cwd"]
    assert _ledger(root_a) == []
