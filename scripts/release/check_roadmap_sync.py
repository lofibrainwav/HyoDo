#!/usr/bin/env python3
"""Check that ROADMAP.md still describes the version this repository ships.

``check_version_sync`` covers the seven sources that carry a version as a
*field*. ROADMAP.md carries one as *prose*, so it was never in that set, and it
drifted: it claimed 4.19.0 was the latest published release three releases
later. The claim was wrong in the safe direction, which is exactly why nobody
caught it.

Two questions are asked here:

1. does the baseline sentence name the version in ``VERSION``?
2. is there a release entry for that version?

Both fail closed. If the baseline sentence cannot be found at all, that is an
error rather than a pass -- a rewritten sentence must not silently switch the
check off.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

#: The baseline claim, e.g. "HyoDo 4.19.2 is the latest published release".
BASELINE_RE = re.compile(r"(\d+\.\d+\.\d+)\s+is the latest published release")


class RoadmapSyncError(Exception):
    """Raised when ROADMAP.md cannot be read or does not state a baseline."""


def read_roadmap(root: Path = ROOT) -> str:
    path = root / "ROADMAP.md"
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RoadmapSyncError(f"ROADMAP.md unreadable at {path}") from exc


def read_version(root: Path = ROOT) -> str:
    path = root / "VERSION"
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RoadmapSyncError(f"VERSION unreadable at {path}") from exc


def baseline_version(text: str) -> str:
    """The version ROADMAP.md calls the latest published release."""
    match = BASELINE_RE.search(text)
    if not match:
        raise RoadmapSyncError(
            f"ROADMAP.md states no baseline: expected a sentence matching {BASELINE_RE.pattern!r}"
        )
    return match.group(1)


def has_release_entry(text: str, version: str) -> bool:
    """True when ROADMAP.md carries a ``### <version>`` release section.

    The version must end the token. A word boundary is not enough: it sits
    between ``2`` and ``-``, so ``### 4.19.2-rc.1`` would answer for ``4.19.2``.
    """
    return re.search(rf"^### {re.escape(version)}(?=\s|$)", text, re.MULTILINE) is not None


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    argv = sys.argv[1:] if argv is None else argv

    try:
        text = read_roadmap(root)
        shipped = read_version(root)
        baseline = baseline_version(text)
    except RoadmapSyncError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    ok = True
    if baseline != shipped:
        print(
            f"ERROR: ROADMAP.md calls {baseline} the latest published release, "
            f"but VERSION is {shipped}",
            file=sys.stderr,
        )
        ok = False

    if not has_release_entry(text, shipped):
        print(
            f"ERROR: ROADMAP.md has no '### {shipped}' release entry",
            file=sys.stderr,
        )
        ok = False

    if ok:
        print(f"OK: ROADMAP.md baseline and release entry both name {shipped}")

    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
