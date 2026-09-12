"""Verify an sdist by contents, not by a brittle compressed-byte ceiling.

The source of truth for allowed public sdist roots is
``tool.hatch.build.targets.sdist.only-include`` in ``pyproject.toml``.  Hatch
also emits ``PKG-INFO`` at the archive root.  Anything else is package-scope
drift and fails closed.
"""

from __future__ import annotations

import argparse
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 public support
    import tomli as tomllib

_AUTO_ALLOWED = {"PKG-INFO"}


def allowed_roots(pyproject: Path) -> set[str]:
    """Read the declared sdist allowlist from the build configuration."""
    with pyproject.open("rb") as handle:
        data: dict[str, Any] = tomllib.load(handle)
    values = data["tool"]["hatch"]["build"]["targets"]["sdist"]["only-include"]
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise ValueError("sdist.only-include must be a list of paths")
    roots = {PurePosixPath(value).parts[0] for value in values if PurePosixPath(value).parts}
    return roots | _AUTO_ALLOWED


def verify_sdist_scope(sdist: Path, pyproject: Path) -> tuple[str, int]:
    """Return the archive root and member count, raising on scope drift."""
    allowed = allowed_roots(pyproject)
    with tarfile.open(sdist, "r:gz") as archive:
        names = archive.getnames()

    roots: set[str] = set()
    unexpected: list[str] = []
    traversal: list[str] = []
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            traversal.append(name)
            continue
        if not path.parts:
            continue
        roots.add(path.parts[0])

    if traversal:
        raise ValueError(f"sdist contains unsafe paths: {traversal[:5]}")
    if len(roots) != 1:
        raise ValueError(f"sdist must have exactly one archive root, found: {sorted(roots)}")
    archive_root = next(iter(roots))

    for name in names:
        parts = PurePosixPath(name).parts
        if len(parts) < 2:
            continue
        top = parts[1]
        if top not in allowed:
            unexpected.append(name)

    if unexpected:
        raise ValueError(f"sdist contains undeclared public paths: {unexpected[:5]}")
    if any("afo_core" in PurePosixPath(name).parts for name in names):
        raise ValueError("sdist includes afo_core")
    return archive_root, len(names)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sdist", type=Path)
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    args = parser.parse_args(argv)

    try:
        archive_root, members = verify_sdist_scope(args.sdist, args.pyproject)
    except (OSError, KeyError, ValueError, tarfile.TarError) as exc:
        print(f"SDIST_SCOPE_FAIL: {exc}")
        return 1

    print(
        "SDIST_SCOPE_PASS: "
        f"root={archive_root} members={members} compressed_bytes={args.sdist.stat().st_size}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
