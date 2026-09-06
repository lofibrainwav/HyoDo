#!/usr/bin/env python3
"""Set version across every version-bearing source, then verify."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

try:
    from scripts.release.version_sources import VersionSourceUpdateError, update_version_sources
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from version_sources import VersionSourceUpdateError, update_version_sources

ROOT = Path(__file__).resolve().parent.parent.parent

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-(alpha|beta|rc)\.\d+)?$")


def validate_semver(version: str) -> None:
    if not SEMVER_RE.match(version):
        print(
            f"ERROR: '{version}' is not valid semver (X.Y.Z or X.Y.Z-{{alpha,beta,rc}}.N)",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: set_version.py <version>", file=sys.stderr)
        sys.exit(1)

    version = sys.argv[1]
    validate_semver(version)

    print(f"Setting version to {version} ...")
    try:
        update_version_sources(ROOT, version)
    except VersionSourceUpdateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "release" / "check_version_sync.py"), version],
        capture_output=True,
        text=True,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
