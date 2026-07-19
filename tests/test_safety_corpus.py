"""Unit tests for collect_scan_corpus dir-scan and default git-path branches."""

import subprocess
from types import SimpleNamespace
from unittest.mock import patch

from hyodo.safety import collect_scan_corpus

GIT_MARKER = "GIT_INTERNAL_MARKER_SHOULD_BE_EXCLUDED"
BINARY_MARKER = "PNG_BINARY_MARKER_SHOULD_BE_SKIPPED"


def test_collect_scan_corpus_dir_scan_cap_git_and_binary(tmp_path):
    """Directory scan caps at 40 files, excludes .git, and skips binary suffixes."""
    # 41 text files: cap of 40 must drop the last one alphabetically.
    for i in range(41):
        (tmp_path / f"file_{i:02d}.txt").write_text(
            f"text file {i:02d} content\n", encoding="utf-8"
        )

    # .git contents must never enter the corpus (sorts first, so it would be
    # read within the first 40 slots if exclusion were absent).
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text(GIT_MARKER + "\n", encoding="utf-8")

    # Binary-extension file must be skipped (sorts before file_* names).
    (tmp_path / "binary.png").write_text(BINARY_MARKER + "\n", encoding="utf-8")

    corpus, source = collect_scan_corpus(path=str(tmp_path))

    # 40-file cap holds and is reflected in the source label.
    assert source.startswith(f"dir:{tmp_path}")
    assert "(40 files)" in source

    # .git contents excluded.
    assert GIT_MARKER not in corpus

    # Binary file skipped.
    assert BINARY_MARKER not in corpus

    # At least one real text file made it into the corpus.
    assert "text file 00 content" in corpus


def test_collect_scan_corpus_default_git_diff(tmp_path):
    """path=None with a non-empty git diff HEAD uses the diff as the corpus."""
    diff_output = "diff --git a/x.py b/x.py\n+API_KEY = 'changed'\n"
    with patch(
        "hyodo.safety.subprocess.run",
        return_value=SimpleNamespace(returncode=0, stdout=diff_output),
    ) as mock_run:
        corpus, source = collect_scan_corpus(path=None, cwd=tmp_path)

    assert corpus == diff_output
    assert source == "git diff HEAD"
    # Only the diff call happened; no fallback to status.
    assert mock_run.call_count == 1


def test_collect_scan_corpus_default_falls_back_to_status(tmp_path):
    """Empty git diff HEAD falls back to git status --porcelain."""
    status_output = "?? untracked_file.py\n M tracked_file.py\n"
    with patch(
        "hyodo.safety.subprocess.run",
        side_effect=[
            SimpleNamespace(returncode=0, stdout="   \n"),  # empty diff (whitespace)
            SimpleNamespace(returncode=0, stdout=status_output),  # status fallback
        ],
    ) as mock_run:
        corpus, source = collect_scan_corpus(path=None, cwd=tmp_path)

    assert corpus == status_output
    assert source == "git status (no diff against HEAD)"
    assert mock_run.call_count == 2


def test_collect_scan_corpus_default_git_missing(tmp_path):
    """FileNotFoundError (git not installed) yields empty corpus, no crash."""
    with patch(
        "hyodo.safety.subprocess.run",
        side_effect=FileNotFoundError("git not found"),
    ):
        corpus, source = collect_scan_corpus(path=None, cwd=tmp_path)

    assert corpus == ""
    assert source == "empty-corpus"


def test_collect_scan_corpus_default_git_timeout(tmp_path):
    """TimeoutExpired yields empty corpus, no crash."""
    with patch(
        "hyodo.safety.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd=["git", "diff", "HEAD"], timeout=20),
    ):
        corpus, source = collect_scan_corpus(path=None, cwd=tmp_path)

    assert corpus == ""
    assert source == "empty-corpus"
