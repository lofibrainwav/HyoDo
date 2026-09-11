from __future__ import annotations

from pathlib import Path

import pytest

from scripts.release.check_roadmap_sync import (
    RoadmapSyncError,
    baseline_version,
    has_release_entry,
    main,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

ROADMAP = """# HyoDo roadmap

## Current public baseline

HyoDo {baseline} is the latest published release after the public 4.18.0
measured run.

### 4.18.0 (released 2026-09-10)

- something.

### {entry} (released 2026-09-11)

- something else.
"""


def write_repo(root: Path, *, version: str, baseline: str, entry: str) -> None:
    (root / "VERSION").write_text(f"{version}\n")
    (root / "ROADMAP.md").write_text(ROADMAP.format(baseline=baseline, entry=entry))


def test_the_real_roadmap_names_the_version_this_repo_ships() -> None:
    """The gate that was missing: ROADMAP.md drifted three releases behind."""
    assert main(argv=[], root=REPO_ROOT) == 0


def test_synced_roadmap_exits_zero(tmp_path: Path, capsys) -> None:
    write_repo(tmp_path, version="4.19.2", baseline="4.19.2", entry="4.19.2")

    code = main(argv=[], root=tmp_path)

    assert code == 0
    assert "4.19.2" in capsys.readouterr().out


def test_stale_baseline_exits_one_and_names_both_versions(tmp_path: Path, capsys) -> None:
    write_repo(tmp_path, version="4.19.2", baseline="4.19.0", entry="4.19.2")

    code = main(argv=[], root=tmp_path)

    err = capsys.readouterr().err
    assert code == 1
    assert "4.19.0" in err
    assert "4.19.2" in err


def test_missing_release_entry_exits_one(tmp_path: Path, capsys) -> None:
    write_repo(tmp_path, version="4.19.2", baseline="4.19.2", entry="4.19.1")

    code = main(argv=[], root=tmp_path)

    err = capsys.readouterr().err
    assert code == 1
    assert "### 4.19.2" in err


def test_a_rewritten_baseline_sentence_fails_rather_than_passing_silently() -> None:
    """Losing the sentence must not switch the check off."""
    with pytest.raises(RoadmapSyncError):
        baseline_version("# HyoDo roadmap\n\nWe ship good software.\n")


def test_missing_roadmap_exits_one(tmp_path: Path, capsys) -> None:
    (tmp_path / "VERSION").write_text("4.19.2\n")

    code = main(argv=[], root=tmp_path)

    assert code == 1
    assert "ROADMAP.md" in capsys.readouterr().err


def test_release_entry_match_is_anchored_not_a_prefix() -> None:
    """The version has to end the token, not merely start it.

    A word boundary passed `### 4.19.20` but let `### 4.19.2-oops` through,
    because `\\b` sits between `2` and `-`. Deliberately renaming the real
    entry that way is how that was caught.
    """
    assert has_release_entry("### 4.19.2 (released)", "4.19.2")
    assert has_release_entry("### 4.19.2", "4.19.2")
    assert not has_release_entry("### 4.19.20 (released)", "4.19.2")
    assert not has_release_entry("### 4.19.2-oops (released)", "4.19.2")
    assert not has_release_entry("### 4.19.2-rc.1 (released)", "4.19.2")
