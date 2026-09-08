"""``hyodo start`` — the M5-C first-use onboarding flow.

Interactive: step 1 shows the workspace root and detected hosts; step 2 asks
the (pre-existing) audience question; step 3 asks one "connect which host
now?" question (at most three choices, including "skip") and, on a real
choice, previews the write(s) and asks one yes/no confirm before doing
anything; step 4 prints a first prompt to try and three commands to run by
hand. At most three questions in the whole flow; nothing is written without
an explicit yes. Non-interactive: the same four steps as plain text, asks
nothing, writes nothing.

Audience-profile behavior itself (resolution order, --json byte-identity,
etc.) is covered in ``tests/test_audience.py`` — this file is scoped to the
onboarding flow's shape: question count, write gating, and content.
"""

from __future__ import annotations

import builtins
import json
from pathlib import Path

import pytest

import hyodo.cli.main as cli

pytestmark = pytest.mark.usefixtures("_isolated_home")


@pytest.fixture
def _isolated_home(tmp_path: Path, monkeypatch) -> None:
    """Never let a real machine's ``~/.claude``/``.cursor``/``.codex`` leak
    into "detected hosts" here — every test gets an empty, disposable home.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("COLUMNS", "1000")


def _scripted_input(monkeypatch, answers: list[str]) -> list[str]:
    """Feed *answers* to ``input()`` calls in order; record every prompt asked."""
    prompts: list[str] = []
    remaining = iter(answers)

    def fake_input(prompt: str = "") -> str:
        prompts.append(prompt)
        try:
            return next(remaining)
        except StopIteration:  # pragma: no cover - guards test authoring mistakes
            raise AssertionError("start() asked more questions than were scripted") from None

    monkeypatch.setattr(builtins, "input", fake_input)
    return prompts


# --------------------------------------------------------------------------
# Non-interactive: the four steps as text, asks nothing, writes nothing.
# --------------------------------------------------------------------------


def test_noninteractive_asks_nothing_and_writes_nothing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)

    def _fail_input(prompt: str = "") -> str:  # pragma: no cover - must never run
        raise AssertionError("non-interactive start() must never call input()")

    monkeypatch.setattr(builtins, "input", _fail_input)
    cli.start()
    assert not (tmp_path / ".hyodo").exists()
    assert not (tmp_path / ".claude").exists()
    assert not (tmp_path / ".mcp.json").exists()


def test_noninteractive_prints_all_four_steps_with_exact_commands(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    cli.start()
    output = capsys.readouterr().out
    assert "1. Workspace" in output
    # Rich wraps long macOS pytest paths, so the full str(tmp_path) may be
    # split across lines. The directory name is enough to bind the print.
    assert tmp_path.name in output
    assert "2. Audience" in output
    assert "3. Connect a host" in output
    assert "hyodo connect claude-code --write --yes" in output
    assert "hyodo mcp config claude-code --write" in output
    assert "4. Try this prompt" in output
    assert "Check this project" in output
    for command in cli._STARTER_COMMANDS:
        assert command in output


def test_noninteractive_preserves_literal_audience_bracket_text(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    """Regression: Rich treats a bare ``[audience]`` as markup and silently
    strips it unless escaped - both the legacy hint and the new step 2 text
    must keep the literal ``[audience]`` config-table name visible.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    cli.start()
    output = capsys.readouterr().out
    assert "[audience]" in output


def test_noninteractive_keeps_todays_guide_content(monkeypatch, tmp_path: Path, capsys) -> None:
    """Existing docs/tests quote this guide text; it must stay available."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    cli.start()
    output = capsys.readouterr().out.lower()
    assert "quick start" in output
    assert "score" in output
    # #204 item 31: the guide must not list Cursor/Codex as hooked hosts.
    assert "works with claude code, codex, grok, gemini cli, cursor" not in output
    assert "unobserved" in output
    assert "hyodo connect" in output


# --------------------------------------------------------------------------
# Interactive: question count, write gating.
# --------------------------------------------------------------------------


def test_interactive_audience_choice_writes_config_alone_when_host_skipped(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    prompts = _scripted_input(monkeypatch, ["3", "skip"])
    cli.start()
    assert len(prompts) == 2  # audience + host choice; no confirm since skipped
    written = (tmp_path / ".hyodo" / "config.toml").read_text(encoding="utf-8")
    assert 'profile = "professional"' in written
    assert not (tmp_path / ".claude").exists()
    assert not (tmp_path / ".mcp.json").exists()


def test_interactive_unrecognized_audience_answer_writes_nothing(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    _scripted_input(monkeypatch, ["banana", "skip"])
    cli.start()
    assert not (tmp_path / ".hyodo" / "config.toml").exists()


def test_interactive_never_asks_more_than_three_questions(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    # Choose an actual host and confirm - the longest possible path.
    prompts = _scripted_input(monkeypatch, ["2", "1", "y"])
    cli.start()
    assert len(prompts) <= 3


def test_interactive_host_choice_by_number_previews_then_asks_one_yes_no(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    # No host is detected in an empty tmp_path -> candidates fall back to
    # ["claude-code"], so the menu is "1) claude-code  2) skip".
    prompts = _scripted_input(monkeypatch, ["2", "1", "n"])
    cli.start()
    assert len(prompts) == 3
    assert "Write this now?" in prompts[2]
    # Declined - nothing written for the host, even though a choice was made.
    assert not (tmp_path / ".claude").exists()
    assert not (tmp_path / ".mcp.json").exists()


def test_interactive_claude_code_yes_writes_both_hook_and_mcp_config(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    prompts = _scripted_input(monkeypatch, ["2", "1", "y"])
    cli.start()
    assert len(prompts) == 3

    hook_settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "hyodo policy check" in hook_settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]

    mcp_config = json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))
    assert mcp_config["mcpServers"]["hyodo"]["command"] == "hyodo"
    assert mcp_config["mcpServers"]["hyodo"]["args"][-1] == str(tmp_path)


def test_interactive_skip_answer_writes_nothing_for_host(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    prompts = _scripted_input(monkeypatch, ["1", "skip"])
    cli.start()
    assert len(prompts) == 2
    assert not (tmp_path / ".claude").exists()
    assert not (tmp_path / ".mcp.json").exists()


def test_interactive_unrecognized_host_answer_writes_nothing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    _scripted_input(monkeypatch, ["1", "not-a-host"])
    cli.start()
    assert not (tmp_path / ".claude").exists()
    assert not (tmp_path / ".mcp.json").exists()


def test_interactive_step4_prints_first_prompt_regardless_of_earlier_choices(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    _scripted_input(monkeypatch, ["banana", "skip"])
    cli.start()
    output = capsys.readouterr().out
    assert "Check this project" in output
    for command in cli._STARTER_COMMANDS:
        assert command in output


# --------------------------------------------------------------------------
# Host candidate / detection helpers
# --------------------------------------------------------------------------


def test_candidates_cap_at_two_detected_hosts_plus_skip(tmp_path: Path) -> None:
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".vscode").mkdir()
    detected = cli._onboarding_detected_hosts(tmp_path)
    candidates = cli._onboarding_host_candidates(detected)
    assert len(candidates) == 2
    # Order follows _ONBOARDING_HOST_ORDER: claude-code, then cursor.
    assert candidates == ["claude-code", "cursor"]


def test_candidates_fall_back_to_claude_code_when_nothing_detected(tmp_path: Path) -> None:
    detected = cli._onboarding_detected_hosts(tmp_path)
    assert all(value is False for value in detected.values())
    assert cli._onboarding_host_candidates(detected) == ["claude-code"]


def test_detected_claude_code_true_from_either_hook_or_mcp_signal(tmp_path: Path) -> None:
    (tmp_path / ".mcp.json").write_text("{}", encoding="utf-8")
    detected = cli._onboarding_detected_hosts(tmp_path)
    assert detected["claude-code"] is True
