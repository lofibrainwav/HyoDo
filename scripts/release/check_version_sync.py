#!/usr/bin/env python3
"""Check version synchronization across VERSION, pyproject.toml, and __init__.py.

Exit 0 if all three sources agree and are valid semver.
Exit 1 on mismatch or invalid format, with diagnostics on stderr.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

VERSION_FILE = ROOT / "VERSION"
PYPROJECT_FILE = ROOT / "pyproject.toml"
INIT_FILE = ROOT / "hyodo" / "__init__.py"
CLI_INIT_FILE = ROOT / "hyodo" / "cli" / "__init__.py"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-(alpha|beta|rc)\.\d+)?$")


def read_version_file() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def read_pyproject_version() -> str:
    text = PYPROJECT_FILE.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        print("ERROR: version field not found in pyproject.toml", file=sys.stderr)
        sys.exit(1)
    return m.group(1)


def read_init_version(path: Path, label: str) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(r'^__version__\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        print(f"ERROR: __version__ not found in {label}", file=sys.stderr)
        sys.exit(1)
    return m.group(1)


def check_semver(version: str, source: str) -> bool:
    if not SEMVER_RE.match(version):
        print(f"ERROR: {source} version '{version}' is not valid semver", file=sys.stderr)
        return False
    return True


def main() -> None:
    expected = sys.argv[1] if len(sys.argv) > 1 else None

    sources = {
        "VERSION": read_version_file(),
        "pyproject.toml": read_pyproject_version(),
        "hyodo/__init__.py": read_init_version(INIT_FILE, "hyodo/__init__.py"),
        "hyodo/cli/__init__.py": read_init_version(CLI_INIT_FILE, "hyodo/cli/__init__.py"),
    }

    ok = True
    for label, val in sources.items():
        if not check_semver(val, label):
            ok = False

    base = sources["VERSION"]
    for label, val in sources.items():
        if val != base:
            print(f"ERROR: VERSION ({base}) != {label} ({val})", file=sys.stderr)
            ok = False

    if expected and base != expected:
        print(f"ERROR: expected {expected}, got {base}", file=sys.stderr)
        ok = False

    if ok:
        print(f"OK: version {base} synchronized across all sources")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
