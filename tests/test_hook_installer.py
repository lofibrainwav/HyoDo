"""Verify the documented hook installer against temporary Git repositories."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    home = repo.parent / "home"
    home.mkdir(exist_ok=True)
    env = os.environ | {
        "GIT_CONFIG_NOSYSTEM": "1",
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
    }
    return subprocess.run(
        ["git", *args], cwd=repo, env=env, check=True, capture_output=True, text=True
    )


def _repo_with_hook(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / ".githooks").mkdir()
    hook = repo / ".githooks" / "pre-push"
    hook.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    hook.chmod(0o755)
    (repo / "scripts").mkdir()
    shutil.copy2(ROOT / "scripts" / "install-hooks.sh", repo / "scripts")
    return repo


def test_hook_installer_sets_local_relative_hook_path(tmp_path: Path) -> None:
    repo = _repo_with_hook(tmp_path)

    result = subprocess.run(
        ["bash", str(repo / "scripts" / "install-hooks.sh")],
        cwd=repo,
        env=os.environ
        | {
            "GIT_CONFIG_NOSYSTEM": "1",
            "HOME": str(tmp_path / "home"),
            "XDG_CONFIG_HOME": str(tmp_path / "home" / ".config"),
        },
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "HOOK_INSTALL_GREEN: core.hooksPath=.githooks" in result.stdout
    assert _git(repo, "config", "--local", "--get", "core.hooksPath").stdout.strip() == ".githooks"


def test_hook_installer_preserves_an_existing_custom_path(tmp_path: Path) -> None:
    repo = _repo_with_hook(tmp_path)
    _git(repo, "config", "--local", "core.hooksPath", "custom-hooks")

    result = subprocess.run(
        ["bash", str(repo / "scripts" / "install-hooks.sh")],
        cwd=repo,
        env=os.environ
        | {
            "GIT_CONFIG_NOSYSTEM": "1",
            "HOME": str(tmp_path / "home"),
            "XDG_CONFIG_HOME": str(tmp_path / "home" / ".config"),
        },
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "HOOK_INSTALL_CONFLICT" in result.stderr
    assert (
        _git(repo, "config", "--local", "--get", "core.hooksPath").stdout.strip() == "custom-hooks"
    )
