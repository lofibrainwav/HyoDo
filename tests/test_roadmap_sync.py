from __future__ import annotations

from pathlib import Path

import pytest

from scripts.release.check_roadmap_sync import (
    RoadmapSyncError,
    baseline_version,
    has_release_entry,
    main,
    target_version,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

ROADMAP = """# HyoDo roadmap

## Current public baseline

HyoDo {baseline} is the latest published release after the public measured run.

## Current release target

HyoDo {target} is the current release target.

### 4.18.0 (released 2026-09-10)

- something.

### {entry}

- something else.
"""


def write_repo(
    root: Path, *, version: str, baseline: str, target: str, entry: str
) -> None:
    (root / "VERSION").write_text(f"{version}\n")
    (root / "ROADMAP.md").write_text(
        ROADMAP.format(baseline=baseline, target=target, entry=entry)
    )


def test_the_real_roadmap_names_the_version_this_repo_targets() -> None:
    assert main(argv=[], root=REPO_ROOT) == 0


def test_published_baseline_may_lag_release_target(tmp_path: Path, capsys) -> None:
    write_repo(
        tmp_path,
        version="4.20.0",
        baseline="4.19.2",
        target="4.20.0",
        entry="4.20.0",
    )

    code = main(argv=[], root=tmp_path)

    assert code == 0
    out = capsys.readouterr().out
    assert "4.19.2" in out
    assert "4.20.0" in out


def test_stale_release_target_exits_one_and_names_both_versions(
    tmp_path: Path, capsys
) -> None:
    write_repo(
        tmp_path,
        version="4.20.0",
        baseline="4.19.2",
        target="4.19.2",
        entry="4.20.0",
    )

    code = main(argv=[], root=tmp_path)

    err = capsys.readouterr().err
    assert code == 1
    assert "4.19.2" in err
    assert "4.20.0" in err


def test_public_baseline_cannot_be_newer_than_release_target(
    tmp_path: Path, capsys
) -> None:
    write_repo(
        tmp_path,
        version="4.20.0",
        baseline="4.21.0",
        target="4.20.0",
        entry="4.20.0",
    )

    code = main(argv=[], root=tmp_path)

    assert code == 1
    assert "newer than release target" in capsys.readouterr().err


def test_missing_release_entry_exits_one(tmp_path: Path, capsys) -> None:
    write_repo(
        tmp_path,
        version="4.20.0",
        baseline="4.19.2",
        target="4.20.0",
        entry="4.19.2",
    )

    code = main(argv=[], root=tmp_path)

    err = capsys.readouterr().err
    assert code == 1
    assert "### 4.20.0" in err


def test_a_rewritten_baseline_sentence_fails_rather_than_passing_silently() -> None:
    with pytest.raises(RoadmapSyncError):
        baseline_version("# HyoDo roadmap\n\nWe ship good software.\n")


def test_a_rewritten_target_sentence_fails_rather_than_passing_silently() -> None:
    with pytest.raises(RoadmapSyncError):
        target_version("# HyoDo roadmap\n\nWe target good software.\n")


def test_missing_roadmap_exits_one(tmp_path: Path, capsys) -> None:
    (tmp_path / "VERSION").write_text("4.20.0\n")

    code = main(argv=[], root=tmp_path)

    assert code == 1
    assert "ROADMAP.md" in capsys.readouterr().err


def test_release_entry_match_is_anchored_not_a_prefix() -> None:
    assert has_release_entry("### 4.19.2 (released)", "4.19.2")
    assert has_release_entry("### 4.19.2", "4.19.2")
    assert not has_release_entry("### 4.19.20 (released)", "4.19.2")
    assert not has_release_entry("### 4.19.2-oops (released)", "4.19.2")
    assert not has_release_entry("### 4.19.2-rc.1 (released)", "4.19.2")
