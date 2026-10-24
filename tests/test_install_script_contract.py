"""Contracts for the interactive installer's dependency handling.

`install_interactive.sh` used to run `python3 -m pip install .`, which lets pip
pick whatever versions the index serves at install time. The repository already
freezes the runtime set; these tests keep the installer on that frozen, hash
verified set instead of a floating resolution (Scorecard PinnedDependenciesID).
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install_interactive.sh"


def _pinned_names(text: str) -> set[str]:
    names: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("--"):
            continue
        if "==" not in stripped:
            continue
        names.add(stripped.split("==", 1)[0])
    return names


def test_installer_does_not_let_pip_resolve_the_project_dependencies() -> None:
    script = INSTALLER.read_text(encoding="utf-8")
    assert "python3 -m pip install --no-deps ." in script
    # A bare project install resolves dependency versions from the index.
    assert 'python3 -m pip install "."' not in script


def test_installer_installs_the_hash_verified_runtime_lock() -> None:
    script = INSTALLER.read_text(encoding="utf-8")
    assert "python3 -m pip install --require-hashes -r requirements.runtime.lock" in script


def test_runtime_lock_covers_every_frozen_runtime_package_with_hashes() -> None:
    lock = (ROOT / "requirements.runtime.lock").read_text(encoding="utf-8")
    export = (ROOT / "requirements.runtime.txt").read_text(encoding="utf-8")
    lock_names = _pinned_names(lock)
    assert lock_names == _pinned_names(export)
    assert lock_names
    assert lock.count("--hash=sha256:") >= len(lock_names)


def test_security_workflow_keeps_the_hash_lock_in_sync_with_the_export() -> None:
    workflow = (ROOT / ".github" / "workflows" / "security.yml").read_text(encoding="utf-8")
    assert "requirements.runtime.lock" in workflow
    assert "diff -u requirements.runtime.lock" in workflow
