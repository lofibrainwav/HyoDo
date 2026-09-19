"""The lockfile records the project's own version, so it is a version source.

CI installs dependencies with `uv sync --locked`. A version bump that leaves
`uv.lock` behind fails every job with "the lockfile needs to be updated" before
a single test runs, which reads as a broad failure rather than a one-line drift.
Catch it here, where the message says what to do.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# The lockfile's own entry for this project, e.g.
#   [[package]]
#   name = "hyodo"
#   version = "4.19.9"
_HYODO_ENTRY = re.compile(
    r'name\s*=\s*"hyodo"\s*\n\s*version\s*=\s*"(?P<version>[^"]+)"',
    re.MULTILINE,
)


def test_uv_lock_records_the_current_version() -> None:
    version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    match = _HYODO_ENTRY.search((REPO_ROOT / "uv.lock").read_text(encoding="utf-8"))
    assert match is not None, "uv.lock has no hyodo package entry to check"
    assert match.group("version") == version, (
        f"uv.lock records hyodo {match.group('version')} but VERSION is {version}. "
        "Run `uv lock` after bumping the version; CI installs with --locked."
    )


def test_release_plan_lists_the_lockfile_in_its_write_set() -> None:
    """A release operator must be told the lockfile changes too."""
    source = (REPO_ROOT / "scripts/release/plan_release.py").read_text(encoding="utf-8")
    assert '"uv.lock"' in source, "plan_release.py omits uv.lock from the expected write set"
