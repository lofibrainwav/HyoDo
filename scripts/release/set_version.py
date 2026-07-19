#!/usr/bin/env python3
"""Set version across VERSION, pyproject.toml, and __init__.py, then verify."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

VERSION_FILE = ROOT / "VERSION"
PYPROJECT_FILE = ROOT / "pyproject.toml"
INIT_FILE = ROOT / "hyodo" / "__init__.py"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-(alpha|beta|rc)\.\d+)?$")


def validate_semver(version: str) -> None:
    if not SEMVER_RE.match(version):
        print(f"ERROR: '{version}' is not valid semver (X.Y.Z or X.Y.Z-{alpha,beta,rc}.N)", file=sys.stderr)
        sys.exit(1)


def write_version_file(version: str) -> None:
    VERSION_FILE.write_text(f"{version}\n", encoding="utf-8")


def write_pyproject_version(version: str) -> None:
    text = PYPROJECT_FILE.read_text(encoding="utf-8")
    text = re.sub(r'^version\s*=\s*"[^"]+"', f'version = "{version}"', text, flags=re.MULTILINE)
    PYPROJECT_FILE.write_text(text, encoding="utf-8")


def write_init_version(path: Path, version: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r'^__version__\s*=\s*"[^"]+"',
        f'__version__ = "{version}"',
        text,
        flags=re.MULTILINE,
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: set_version.py <version>", file=sys.stderr)
        sys.exit(1)

    version = sys.argv[1]
    validate_semver(version)

    print(f"Setting version to {version} ...")
    write_version_file(version)
    write_pyproject_version(version)
    write_init_version(INIT_FILE, version)

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
