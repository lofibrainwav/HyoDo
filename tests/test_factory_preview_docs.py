"""Factory Developer Preview documentation contracts.

The published Factory commands must run from a bare source checkout, keep the
global `--root` option before the subcommand, and stay aligned across the
GitHub docs and the site. The run block is executed in a clean environment so
a first-time reader gets the same first result the docs promise.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
FACTORY_README = REPO / "examples" / "factory-loop" / "README.md"
ROOT_README = REPO / "README.md"
SITE_DOC = REPO / "site" / "src" / "content" / "docs" / "docs" / "factory.md"
SITE_INDEX = REPO / "site" / "src" / "pages" / "index.astro"
SITE_CONFIG = REPO / "site" / "astro.config.mjs"
BOUNDARY = REPO / "docs" / "PRODUCT_BOUNDARY.md"

PUBLIC_URL = "https://github.com/lofibrainwav/HyoDo.git"
REF_RE = re.compile(r"git checkout --detach ([0-9a-f]{40})")
SUBCOMMANDS = (
    "add",
    "list",
    "enable",
    "disable",
    "update",
    "rollback",
    "remove",
    "doctor",
    "route",
    "discover",
    "gaps",
    "trust",
    "hosts",
    "recover-stale-lock",
    "run",
)
PREVIEW_DOCS = [FACTORY_README, ROOT_README, SITE_DOC, SITE_INDEX]


def _factory_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if "hyodo_factory" in line and "--root" in line
    ]


@pytest.mark.parametrize("path", [FACTORY_README, ROOT_README, SITE_DOC])
def test_root_option_comes_before_the_factory_subcommand(path: Path) -> None:
    """argparse defines `--root` on the parent parser, so it must precede the subcommand."""
    for line in _factory_lines(path):
        tokens = line.replace('"', " ").split()
        sub_idx = next((i for i, t in enumerate(tokens) if t in SUBCOMMANDS), None)
        root_idx = tokens.index("--root")
        if sub_idx is not None:
            assert root_idx < sub_idx, f"{path.name}: --root after the subcommand: {line.strip()}"


def _fenced_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    for match in re.finditer(r"```(\S*)[ \t]*([^\n]*)\n(.*?)```", text, re.DOTALL):
        label = match.group(2).strip()
        if label:
            blocks[label] = match.group(3)
    return blocks


def test_canonical_quickstart_pins_one_reviewed_source_ref() -> None:
    text = FACTORY_README.read_text(encoding="utf-8")
    refs = set(REF_RE.findall(text))
    assert len(refs) == 1, "the canonical quickstart must pin exactly one source ref"
    (ref,) = refs
    for path in (ROOT_README, SITE_DOC):
        assert path.is_file(), f"{path} must exist"
        assert ref in path.read_text(encoding="utf-8"), f"{path.name} is not on ref {ref}"


def test_quickstart_bootstraps_the_checkout_and_places_root_first() -> None:
    blocks = _fenced_blocks(FACTORY_README.read_text(encoding="utf-8"))
    assert "factory-preview-run" in blocks
    run = blocks["factory-preview-run"]
    assert 'export PYTHONPATH="$PWD"' in run
    assert "--root" in run


def _clean_env(tmp_path: Path) -> dict[str, str]:
    home = tmp_path / "home"
    bin_dir = home / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "python3").symlink_to(sys.executable)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    # macOS `mktemp -d` ignores $TMPDIR; this shim keeps the test hermetic everywhere.
    shim = bin_dir / "mktemp"
    shim.write_text(
        "#!/bin/sh\n"
        '[ "$1" = "-d" ] || exit 2\n'
        "d=\"$TMPDIR/tmp.$$.$(od -An -N4 -tx1 /dev/urandom | tr -d ' \\n')\"\n"
        'mkdir "$d" && printf \'%s\\n\' "$d"\n',
        encoding="utf-8",
    )
    shim.chmod(0o755)
    return {
        "HOME": str(home),
        "PATH": f"{bin_dir}:/usr/bin:/bin",
        "TMPDIR": str(scratch),
        "LANG": "C.UTF-8",
    }


def _local_public_source(tmp_path: Path) -> Path:
    """A throwaway git repo holding the parts of the checkout the quickstart uses."""
    source = tmp_path / "public-source"
    for rel in ("hyodo", "examples/factory-loop", "schemas"):
        shutil.copytree(
            REPO / rel,
            source / rel,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    for rel in ("pyproject.toml", "VERSION"):
        shutil.copy2(REPO / rel, source / rel)
    git_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }
    for cmd in (["init", "-q"], ["add", "."], ["commit", "-q", "-m", "source"]):
        subprocess.run(["git", *cmd], cwd=source, env=git_env, check=True, capture_output=True)
    return source


def _git_status(path: Path) -> str:
    return subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required")
@pytest.mark.skipif(shutil.which("git") is None, reason="git is required")
def test_quickstart_from_an_existing_folder_leaves_nothing_in_it(tmp_path: Path) -> None:
    """Clone and example work both land in an explicitly created temporary path."""
    blocks = _fenced_blocks(FACTORY_README.read_text(encoding="utf-8"))
    clone = blocks["factory-preview-clone"]
    run = blocks["factory-preview-run"]
    source = _local_public_source(tmp_path)
    clone = clone.replace(PUBLIC_URL, str(source))
    clone = REF_RE.sub("git checkout --detach HEAD", clone)
    assert str(source) in clone, "the clone block must name the public repository URL"

    existing = tmp_path / "existing-folder"
    existing.mkdir()
    (existing / "keep.txt").write_text("mine", encoding="utf-8")
    env = _clean_env(tmp_path)
    repo_before = _git_status(REPO)

    result = subprocess.run(
        ["bash", "-c", f"set -e\n{clone}\n{run}"],
        cwd=existing,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "DIVERGENT" in out
    assert "HOST_DECISION_REQUIRED" in out
    assert "verify-demo" in out
    assert "selected" in out.lower()
    assert "UNOBSERVED" in out  # a fresh workspace has no registered modules

    # Nothing was left in the folder the reader ran the commands from.
    assert sorted(p.name for p in existing.iterdir()) == ["keep.txt"]
    # The clone and the example work live under the explicitly created temp paths.
    scratch = Path(env["TMPDIR"])
    created = sorted(p.name for p in scratch.iterdir())
    assert len(created) >= 2, created
    assert any((p / "HyoDo" / ".git").exists() for p in scratch.iterdir() if p.is_dir())
    assert not (Path(env["HOME"]) / ".hyodo").exists()
    assert _git_status(REPO) == repo_before


def test_every_published_git_clone_names_an_explicit_destination() -> None:
    clone_re = re.compile(r"git clone\s+(\S+)(.*)")
    seen = 0
    for path in (FACTORY_README, ROOT_README, SITE_DOC, SITE_INDEX):
        for match in clone_re.finditer(path.read_text(encoding="utf-8")):
            if "HyoDo" not in match.group(1):
                continue
            seen += 1
            dest = match.group(2).strip().split("&&")[0].strip()
            assert re.match(r'"\$[A-Za-z_]+/[^"\s]+"', dest), (
                f"{path.name}: git clone needs an explicit temporary destination: {match.group(0)}"
            )
    assert seen >= 2


def test_site_has_a_dedicated_preview_page_and_landing_section() -> None:
    assert SITE_DOC.is_file()
    doc = SITE_DOC.read_text(encoding="utf-8")
    assert re.search(r"^title: Factory Developer Preview$", doc, re.MULTILINE)
    assert "slug: 'docs/factory'" in SITE_CONFIG.read_text(encoding="utf-8")
    index = SITE_INDEX.read_text(encoding="utf-8")
    assert 'id="factory-preview-heading"' in index
    assert "/docs/factory/" in index


def test_preview_copy_is_truthful_about_scope() -> None:
    doc = " ".join(SITE_DOC.read_text(encoding="utf-8").lower().split())
    for phrase in (
        "developer preview",
        "source checkout",
        "not part of the published hyodo package",
        "experimental",
        "host",
    ):
        assert phrase in doc, f"site page lacks: {phrase}"
    for banned in (
        "verified host",
        "verified session",
        "production-ready",
        "kingdom",
        "pypi release",
    ):
        assert banned not in doc, f"site page must not say: {banned}"
    # Execution belongs to the host, and no host is claimed as verified.
    assert "host owns" in doc or "host-owned" in doc


def test_preview_docs_carry_no_private_paths_or_internal_names() -> None:
    patterns = ("/Users/", "/.local/", "orca_session", "ctx_")
    for path in (FACTORY_README, ROOT_README, SITE_DOC, SITE_INDEX, BOUNDARY):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for pat in patterns:
            assert pat not in text, f"{path.name} contains {pat}"
    assert "PYTHONPATH" in FACTORY_README.read_text(encoding="utf-8")
