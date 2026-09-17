#!/usr/bin/env python3
"""Classify old HyoDo/KINGDOM runtime slots without guessing ownership.

The default operation is a JSON dry-run.  A slot is a cleanup candidate only
when it is old, not the current alias, not pinned, clean, and not observed in
the process cwd census.  This script does not stop services or remove
registered Git worktrees; those are separate authority decisions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "hyodo.runtime-gc/v1"
PROTECTED = {"ACTIVE", "PINNED", "DIRTY_UNIQUE"}


def _realpath(path: Path) -> str:
    return str(path.resolve(strict=False))


def _under(path: str, root: str) -> bool:
    try:
        Path(path).relative_to(root)
    except ValueError:
        return False
    return True


def _run(*args: str) -> str:
    try:
        return subprocess.run(args, check=True, capture_output=True, text=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return ""


def _git_status(root: Path) -> list[str] | None:
    output = _run("git", "-C", str(root), "status", "--porcelain=v1")
    if output == "" and not (root / ".git").exists():
        return None
    return [line for line in output.splitlines() if line]


def _worktree_registry(root: Path) -> dict[str, str]:
    output = _run("git", "-C", str(root), "worktree", "list", "--porcelain")
    entries: dict[str, str] = {}
    current: str | None = None
    for line in output.splitlines():
        if line.startswith("worktree "):
            current = _realpath(Path(line[9:]))
            entries[current] = ""
        elif line.startswith("HEAD ") and current is not None:
            entries[current] = line[5:].strip()
    return entries


def _process_cwds() -> list[str]:
    if shutil.which("lsof") is None:
        return []
    output = _run("lsof", "-n", "-w", "-d", "cwd")
    return sorted({line[1:] for line in output.splitlines() if line.startswith("n/")})


def _dirty_digest(paths: Iterable[str]) -> str | None:
    values = list(paths)
    if not values:
        return None
    return hashlib.sha256("\n".join(values).encode()).hexdigest()


def _is_pinned(path: Path, pin_files: set[str]) -> bool:
    real = _realpath(path)
    return real in pin_files or any(
        (path / marker).is_file() for marker in (".runtime-pinned", ".hyodo/runtime-pinned")
    )


def classify_slot(
    path: Path,
    *,
    current_paths: set[str],
    pinned_paths: set[str] | None = None,
    process_cwds: Iterable[str] = (),
    registry_paths: set[str] | None = None,
    now: float | None = None,
    older_than_seconds: float = 86400,
) -> dict[str, object]:
    """Return one deterministic, non-mutating classification for *path*."""
    real = _realpath(path)
    stat = path.stat()
    dirty = _git_status(path)
    registry_paths = registry_paths or set()
    pinned_paths = pinned_paths or set()
    active = real in current_paths or any(_under(cwd, real) for cwd in process_cwds)
    pinned = real in pinned_paths or _is_pinned(path, set())
    age_seconds = max(0.0, (now if now is not None else datetime.now().timestamp()) - stat.st_mtime)

    if dirty is None:
        classification = "UNOBSERVABLE"
        reason = "git_status_unobservable"
    elif active:
        classification = "ACTIVE"
        reason = "current_alias_or_process_cwd"
    elif pinned:
        classification = "PINNED"
        reason = "explicit_runtime_pin"
    elif dirty:
        classification = "DIRTY_UNIQUE"
        reason = "dirty_worktree_or_runtime_artifact"
    elif age_seconds < older_than_seconds:
        classification = "RECENT"
        reason = "below_age_threshold"
    else:
        classification = "OLD_CANDIDATE"
        reason = "clean_inactive_unpinned_and_old"

    return {
        "path": str(path),
        "realpath": real,
        "classification": classification,
        "reason": reason,
        "age_seconds": round(age_seconds, 3),
        "dirty_paths": dirty,
        "dirty_digest": _dirty_digest(dirty or []),
        "registered_worktree": real in registry_paths,
        "head": _run("git", "-C", str(path), "rev-parse", "HEAD").strip() or None,
    }


def scan(
    prefixes: Iterable[Path],
    *,
    current: Iterable[Path] = (),
    registry_roots: Iterable[Path] = (),
    pin_files: Iterable[Path] = (),
    older_than_seconds: float = 86400,
    now: float | None = None,
) -> dict[str, object]:
    slots: dict[str, Path] = {}
    for prefix in prefixes:
        for candidate in prefix.parent.glob(f"{prefix.name}*"):
            if candidate.is_dir() and not candidate.is_symlink():
                slots[_realpath(candidate)] = candidate
    current_paths = {_realpath(path) for path in current if path.exists()}
    registry: dict[str, str] = {}
    for root in registry_roots:
        registry.update(_worktree_registry(root))
    pinned_paths = {_realpath(path) for path in pin_files}
    process_cwds = _process_cwds()
    entries = [
        classify_slot(
            path,
            current_paths=current_paths,
            pinned_paths=pinned_paths,
            process_cwds=process_cwds,
            registry_paths=set(registry),
            older_than_seconds=older_than_seconds,
            now=now,
        )
        for path in sorted(slots.values(), key=str)
    ]
    counts: dict[str, int] = {}
    for entry in entries:
        key = str(entry["classification"])
        counts[key] = counts.get(key, 0) + 1
    return {
        "schema_version": SCHEMA_VERSION,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "process_cwds_observed": bool(process_cwds),
        "registry": {"roots": [str(path) for path in registry_roots], "count": len(registry)},
        "counts": counts,
        "entries": entries,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", action="append", type=Path, required=True)
    parser.add_argument("--current", action="append", type=Path, default=[])
    parser.add_argument("--registry-root", action="append", type=Path, default=[])
    parser.add_argument("--pin-file", action="append", type=Path, default=[])
    parser.add_argument("--older-than-days", type=float, default=1.0)
    args = parser.parse_args(argv)
    print(
        json.dumps(
            scan(
                args.prefix,
                current=args.current,
                registry_roots=args.registry_root,
                pin_files=args.pin_file,
                older_than_seconds=args.older_than_days * 86400,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
