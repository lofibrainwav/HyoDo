"""Regression: what we did not look at must never read as what we found clean.

Third companion to test_policy_self_report_boundary.py and test_evidence_integrity.py.
These pin coverage honesty: an unreadable ledger, an unscanned new file, a capped
directory sweep, and a typo'd score are all failures to observe — none of them may be
rendered as a healthy result.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.events import AGENT_EVENTS_RELATIVE_PATH, read_agent_events
from hyodo.safety import _porcelain_paths, collect_scan_corpus, scan_text

runner = CliRunner()


def _git_repo(root: Path) -> None:
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
        "PATH": "/usr/bin:/bin",
    }
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-q", "--allow-empty", "-m", "init"], cwd=root, check=True, env=env
    )


# --------------------------------------------------------------------------- #
# Untracked files are read, not just named
# --------------------------------------------------------------------------- #


def test_untracked_file_contents_reach_the_default_corpus(tmp_path: Path):
    """``git diff HEAD`` is empty precisely when only new files exist."""
    _git_repo(tmp_path)
    (tmp_path / ".env.local").write_text("AWS_SECRET=AKIAABCDEFGHIJKLMNOP\n", encoding="utf-8")

    text, source = collect_scan_corpus(None, cwd=tmp_path)

    assert "AKIAABCDEFGHIJKLMNOP" in text, "new file content was not scanned"
    assert "working-tree file" in source, "corpus must disclose what it actually read"
    assert any(finding.severity == "high" for finding in scan_text(text))


def test_untracked_directory_is_expanded_not_just_named(tmp_path: Path):
    """git collapses a wholly new folder into one ``?? creds/`` line.

    Reading only that line would leave every file inside a newly created directory
    unscanned — the same blind spot as an untracked file, one level up.
    """
    _git_repo(tmp_path)
    (tmp_path / "creds").mkdir()
    (tmp_path / "creds" / "prod.env").write_text("AWS=AKIAABCDEFGHIJKLMNOP\n", encoding="utf-8")

    text, _source = collect_scan_corpus(None, cwd=tmp_path)

    assert "AKIAABCDEFGHIJKLMNOP" in text


def test_binary_and_cache_files_are_still_excluded(tmp_path: Path):
    """Reading working-tree files must not undo the corpus hygiene rules."""
    _git_repo(tmp_path)
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01secret-ish\x00")

    text, _source = collect_scan_corpus(None, cwd=tmp_path)

    assert "secret-ish" not in text


def test_porcelain_paths_handles_renames_and_quotes():
    listing = '?? new.txt\n M src/app.py\nR  old.py -> "new name.py"\n'
    assert _porcelain_paths(listing) == ["new.txt", "src/app.py", "new name.py"]


# --------------------------------------------------------------------------- #
# Unreadable ledger is not an empty ledger
# --------------------------------------------------------------------------- #


def test_read_agent_events_separates_empty_from_unreadable(tmp_path: Path):
    assert read_agent_events(tmp_path) == ([], 0)  # no file yet — an honest zero

    ledger = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text('{"event_id": "a"}\n', encoding="utf-8")
    events, corrupt = read_agent_events(tmp_path)
    assert events is not None
    assert len(events) == 1
    assert corrupt == 0

    ledger.chmod(0o000)
    try:
        events, _ = read_agent_events(tmp_path)
        assert events is None, "unreadable ledger must not look like an empty one"
    finally:
        ledger.chmod(0o644)


def test_report_marks_unreadable_ledger_as_unobserved(tmp_path: Path):
    hyodo_dir = tmp_path / ".hyodo"
    hyodo_dir.mkdir()
    (hyodo_dir / "agent-events.jsonl").write_text('{"event_id": "a"}\n', encoding="utf-8")
    (hyodo_dir / "agent-events.jsonl").chmod(0o000)
    try:
        result = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "md", "--json"])
        assert result.exit_code == 0
        import json

        report = (tmp_path / json.loads(result.output)["result_path"]).read_text(encoding="utf-8")
        assert "UNOBSERVED" in report
        assert "Events: 0 " not in report, "an unreadable ledger must not print as zero events"
    finally:
        (hyodo_dir / "agent-events.jsonl").chmod(0o644)


# --------------------------------------------------------------------------- #
# Score input validation
# --------------------------------------------------------------------------- #


def test_out_of_range_pillar_fails_instead_of_scoring_full_marks():
    """``-t 9`` is a typo for ``-t 0.9``; clamping silently awarded a perfect score."""
    result = runner.invoke(
        app, ["score", "-t", "9", "-g", "0.9", "-b", "0.9", "-i", "0.9", "-c", "0.9"]
    )
    assert result.exit_code == 2
    assert "between 0.0 and 1.0" in result.output


def test_non_finite_pillar_is_rejected():
    result = runner.invoke(
        app, ["score", "-t", "inf", "-g", "0.9", "-b", "0.9", "-i", "0.9", "-c", "0.9"]
    )
    assert result.exit_code == 2


def test_valid_pillars_still_score():
    result = runner.invoke(
        app, ["score", "-t", "0.9", "-g", "0.9", "-b", "0.9", "-i", "0.9", "-c", "0.9"]
    )
    assert result.exit_code == 0
