from __future__ import annotations

import os
from pathlib import Path

from scripts.runtime_gc import classify_slot


def _git_repo(path: Path) -> None:
    os.system(f"git -C {path} init -q")
    (path / "tracked.txt").write_text("tracked\n")
    os.system(f"git -C {path} add tracked.txt")
    os.system(f"git -C {path} -c user.email=test@example.invalid -c user.name=test commit -qm init")


def test_active_beats_dirty_and_is_protected(tmp_path: Path) -> None:
    _git_repo(tmp_path)
    (tmp_path / "runtime.log").write_text("live\n")
    result = classify_slot(tmp_path, current_paths={str(tmp_path.resolve())}, now=100)
    assert result["classification"] == "ACTIVE"


def test_dirty_slot_is_unique_and_never_candidate(tmp_path: Path) -> None:
    _git_repo(tmp_path)
    (tmp_path / "runtime.log").write_text("wip\n")
    result = classify_slot(tmp_path, current_paths=set(), now=100, older_than_seconds=1)
    assert result["classification"] == "DIRTY_UNIQUE"
    assert result["dirty_digest"]


def test_clean_old_unregistered_slot_is_candidate(tmp_path: Path) -> None:
    _git_repo(tmp_path)
    result = classify_slot(
        tmp_path,
        current_paths=set(),
        now=tmp_path.stat().st_mtime + 2,
        older_than_seconds=1,
    )
    assert result["classification"] == "OLD_CANDIDATE"
    assert result["registered_worktree"] is False


def test_process_cwd_protects_slot(tmp_path: Path) -> None:
    _git_repo(tmp_path)
    result = classify_slot(
        tmp_path,
        current_paths=set(),
        process_cwds=[str(tmp_path / "nested")],
        now=tmp_path.stat().st_mtime + 2,
        older_than_seconds=1,
    )
    assert result["classification"] == "ACTIVE"
