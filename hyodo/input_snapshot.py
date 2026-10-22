"""Bounded content identity for Git-backed BYOG check inputs.

This observes tracked and unignored files, plus the BYOG configuration. It is
not a snapshot of ignored dependencies, the runtime, or external gate inputs.
The generated history ledger is excluded. Missing coverage is never a digest.
"""

from __future__ import annotations

import hashlib
import os
import stat
import subprocess
from pathlib import Path

from hyodo.provenance import _GIT_LOCATION_ENV

MAX_FILES = 20_000
MAX_BYTES = 128 * 1024 * 1024


def git_input_digest(root: Path) -> str | None:
    """Hash bounded file names and bytes without following symlinks outside root."""
    try:
        root = root.resolve(strict=True)
        result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "-z",
                "--cached",
                "--others",
                "--exclude-standard",
                "--",
                ".",
            ],
            capture_output=True,
            check=False,
            timeout=10,
            env={k: v for k, v in os.environ.items() if k not in _GIT_LOCATION_ENV},
        )
        if result.returncode:
            return None
        names = {os.fsdecode(name) for name in result.stdout.split(b"\0") if name}
        if (root / ".hyodo/gates.toml").is_file():
            names.add(".hyodo/gates.toml")
        names.discard(".hyodo/history.jsonl")
        if len(names) > MAX_FILES:
            return None
        digest = hashlib.sha256()
        total = 0
        for name in sorted(names):
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts:
                return None
            path = root / relative
            # Do not traverse a parent link, even if the leaf itself is a link.
            if not path.parent.resolve(strict=True).is_relative_to(root):
                return None
            encoded = os.fsencode(name)
            digest.update(len(encoded).to_bytes(8, "big") + encoded)
            try:
                info = path.lstat()
            except FileNotFoundError:
                digest.update(b"missing\0")
                continue
            if stat.S_ISLNK(info.st_mode):
                data = os.fsencode(os.readlink(path))
                digest.update(b"link\0")
            elif stat.S_ISREG(info.st_mode):
                if total + info.st_size > MAX_BYTES:
                    return None
                # The descriptor must still name a regular leaf, not a raced link.
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(fd, "rb") as handle:
                    if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                        return None
                    data = handle.read(MAX_BYTES - total + 1)
                digest.update(b"file\0" + (info.st_mode & 0o111).to_bytes(2, "big"))
            else:
                return None
            total += len(data)
            if total > MAX_BYTES:
                return None
            digest.update(len(data).to_bytes(8, "big") + data)
        return digest.hexdigest()
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
