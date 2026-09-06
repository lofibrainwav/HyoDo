#!/usr/bin/env python3
"""Check version synchronization across every version-bearing source.

Sources checked:

- ``VERSION`` (plain text)
- ``pyproject.toml`` (``[project] version = "..."``)
- ``hyodo/__init__.py`` (``__version__ = "..."``)
- ``Dockerfile`` (``LABEL version="..."``)
- ``.claude-plugin/plugin.json`` (``"version"`` field)

Exit 0 if every source agrees and is valid semver. Exit 1 on mismatch or
invalid/missing format, with diagnostics on stderr.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-(alpha|beta|rc)\.\d+)?$")


class VersionSyncError(Exception):
    """Raised when a version source is missing or malformed."""


def _read_regex_version(path: Path, pattern: str, label: str) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise VersionSyncError(f"{label} not found at {path}") from exc
    m = re.search(pattern, text, re.MULTILINE)
    if not m:
        raise VersionSyncError(f"version field not found in {label}")
    return m.group(1)


def read_version_file(root: Path = ROOT) -> str:
    path = root / "VERSION"
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise VersionSyncError(f"VERSION not found at {path}") from exc


def read_pyproject_version(root: Path = ROOT) -> str:
    return _read_regex_version(
        root / "pyproject.toml", r'^version\s*=\s*"([^"]+)"', "pyproject.toml"
    )


def read_init_version(root: Path = ROOT) -> str:
    return _read_regex_version(
        root / "hyodo" / "__init__.py",
        r'^__version__\s*=\s*"([^"]+)"',
        "hyodo/__init__.py",
    )


def read_dockerfile_version(root: Path = ROOT) -> str:
    return _read_regex_version(root / "Dockerfile", r'^LABEL\s+version="([^"]+)"', "Dockerfile")


def read_plugin_manifest_version(root: Path = ROOT) -> str:
    path = root / ".claude-plugin" / "plugin.json"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise VersionSyncError(f".claude-plugin/plugin.json not found at {path}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise VersionSyncError(f".claude-plugin/plugin.json is not valid JSON: {exc}") from exc
    version = data.get("version")
    if not version:
        raise VersionSyncError("version field not found in .claude-plugin/plugin.json")
    return str(version)


def collect_sources(root: Path = ROOT) -> dict[str, str]:
    return {
        "VERSION": read_version_file(root),
        "pyproject.toml": read_pyproject_version(root),
        "hyodo/__init__.py": read_init_version(root),
        "Dockerfile": read_dockerfile_version(root),
        ".claude-plugin/plugin.json": read_plugin_manifest_version(root),
    }


def check_semver(version: str, source: str) -> bool:
    if not SEMVER_RE.match(version):
        print(f"ERROR: {source} version '{version}' is not valid semver", file=sys.stderr)
        return False
    return True


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    argv = sys.argv[1:] if argv is None else argv
    expected = argv[0] if argv else None

    try:
        sources = collect_sources(root)
    except VersionSyncError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

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

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
