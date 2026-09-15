"""Exercise the SSOT hook and drift guard in isolated temporary repositories."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_repo(repo: Path) -> None:
    repo.mkdir(exist_ok=True)
    _run_git(repo, "init", "-q")
    _run_git(repo, "config", "user.email", "test@example.invalid")
    _run_git(repo, "config", "user.name", "HyoDo test")
    (repo / ".githooks").mkdir()
    (repo / "scripts").mkdir()
    shutil.copy2(ROOT / ".githooks" / "pre-push", repo / ".githooks" / "pre-push")
    shutil.copy2(
        ROOT / "scripts" / "verify-ssot-drift.sh",
        repo / "scripts" / "verify-ssot-drift.sh",
    )
    (repo / "tracked.txt").write_text("fixture\n", encoding="utf-8")
    _run_git(repo, "add", "-A")
    _run_git(repo, "commit", "-q", "-m", "fixture")


def test_pre_push_accepts_a_valid_commitish_base_ref(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    env = os.environ | {"HYODO_SSOT_BASE_REF": "HEAD"}

    result = subprocess.run(
        ["bash", str(tmp_path / ".githooks" / "pre-push")],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "SSOT_GREEN:" in result.stdout


def test_pre_push_reports_unavailable_base_ref_without_running_guard(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    env = os.environ | {"HYODO_SSOT_BASE_REF": "refs/heads/missing-base"}

    result = subprocess.run(
        ["bash", str(tmp_path / ".githooks" / "pre-push")],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "SSOT_UNOBSERVED: refs/heads/missing-base is unavailable" in result.stderr


def test_drift_guard_rejects_a_branch_checked_out_in_multiple_worktrees(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    branch = _run_git(tmp_path, "branch", "--show-current").stdout.strip()
    duplicate = tmp_path / "duplicate-worktree"
    _run_git(tmp_path, "worktree", "add", "--force", str(duplicate), branch)

    result = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts" / "verify-ssot-drift.sh"),
            "HEAD",
            "HEAD",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert f"SSOT_DRIFT: branch {branch} is checked out in 2 worktrees" in result.stderr


def test_ssot_workflow_cancels_superseded_runs() -> None:
    workflow = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "ssot-drift.yml").read_text(encoding="utf-8")
    )

    assert workflow["concurrency"]["cancel-in-progress"] is True
    assert workflow["concurrency"]["group"] == (
        "ssot-drift-${{ github.event.pull_request.number || github.ref }}"
    )
