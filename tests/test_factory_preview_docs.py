"""Factory Developer Preview documentation contracts.

The published Factory commands must run from a bare source checkout, keep the
global `--root` option before the subcommand, and stay aligned across the
GitHub docs and the site. The run block is executed in a clean environment so
a first-time reader gets the same first result the docs promise.
"""

from __future__ import annotations

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


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required")
def test_quickstart_run_block_reaches_a_first_meaningful_result(tmp_path: Path) -> None:
    run = _fenced_blocks(FACTORY_README.read_text(encoding="utf-8"))["factory-preview-run"]
    home = tmp_path / "home"
    bin_dir = home / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "python3").symlink_to(sys.executable)
    env = {
        "HOME": str(home),
        "PATH": f"{bin_dir}:/usr/bin:/bin",
        "TMPDIR": str(tmp_path),
        "LANG": "C.UTF-8",
    }
    result = subprocess.run(
        ["bash", "-c", f"set -e\n{run}"],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "DIVERGENT" in out
    assert "HOST_DECISION_REQUIRED" in out
    assert "verify-demo" in out
    assert "selected" in out.lower()
    assert "UNOBSERVED" in out  # a fresh workspace has no registered modules
    assert not (home / ".hyodo").exists()


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
