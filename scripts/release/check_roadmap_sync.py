#!/usr/bin/env python3
"""Check ROADMAP release-target truth without rewriting published history.

``check_version_sync`` covers the seven sources that carry a version as a
field. ROADMAP.md carries two different prose facts and they must stay separate:

1. the latest version actually published to users; and
2. the version this source tree is currently preparing to release.

A release candidate may legitimately have ``VERSION=4.20.0`` while the latest
published package is still ``4.19.2``. Treating those as one value makes release
preparation publish a false claim before any tag, GitHub Release, or PyPI
receipt exists.

This check therefore asks three questions:

1. does the roadmap state a parseable public baseline?
2. does the roadmap's current release target match ``VERSION``?
3. is there a release entry for that target?

The public baseline may lag the release target, but it may not be newer than the
target. Every missing or rewritten sentence fails closed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

BASELINE_RE = re.compile(r"(\d+\.\d+\.\d+)\s+is the latest published release")
TARGET_RE = re.compile(r"(\d+\.\d+\.\d+)\s+is the current release target")


class RoadmapSyncError(Exception):
    """Raised when ROADMAP.md cannot be read or required state is missing."""


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


def _matched_version(text: str, pattern: re.Pattern[str], label: str) -> str:
    match = pattern.search(text)
    if not match:
        raise RoadmapSyncError(
            f"ROADMAP.md states no {label}: expected a sentence matching {pattern.pattern!r}"
        )
    return match.group(1)


def baseline_version(text: str) -> str:
    """The version ROADMAP.md calls the latest actually published release."""
    return _matched_version(text, BASELINE_RE, "public baseline")


def target_version(text: str) -> str:
    """The version ROADMAP.md says the source tree is preparing to release."""
    return _matched_version(text, TARGET_RE, "release target")


def _semver_tuple(version: str) -> tuple[int, int, int]:
    try:
        major, minor, patch = version.split(".")
        return int(major), int(minor), int(patch)
    except (ValueError, TypeError) as exc:
        raise RoadmapSyncError(f"invalid roadmap semver: {version!r}") from exc


def has_release_entry(text: str, version: str) -> bool:
    """True when ROADMAP.md carries a ``### <version>`` release section."""
    return re.search(rf"^### {re.escape(version)}(?=\s|$)", text, re.MULTILINE) is not None


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    argv = sys.argv[1:] if argv is None else argv

    try:
        text = read_roadmap(root)
        source_version = read_version(root)
        published = baseline_version(text)
        target = target_version(text)
    except RoadmapSyncError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    ok = True
    if target != source_version:
        print(
            f"ERROR: ROADMAP.md calls {target} the current release target, "
            f"but VERSION is {source_version}",
            file=sys.stderr,
        )
        ok = False

    try:
        if _semver_tuple(published) > _semver_tuple(target):
            print(
                f"ERROR: public baseline {published} is newer than release target {target}",
                file=sys.stderr,
            )
            ok = False
    except RoadmapSyncError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        ok = False

    if not has_release_entry(text, source_version):
        print(
            f"ERROR: ROADMAP.md has no '### {source_version}' release entry",
            file=sys.stderr,
        )
        ok = False

    if ok:
        print(
            f"OK: ROADMAP.md public baseline {published}; "
            f"release target and entry both name {source_version}"
        )

    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
