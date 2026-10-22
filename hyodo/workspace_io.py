"""Small descriptor-relative file operations for root-locked HyoDo data.

An in-root symlink may resolve to another in-root file. The resolved path is
opened component by component beneath a pinned root descriptor with NOFOLLOW,
so replacing a checked link with an outward link cannot redirect the I/O.
Platforms without those primitives fail closed for these operations.
"""

from __future__ import annotations

import errno
import os
from contextlib import suppress
from pathlib import Path

_SUPPORTED = (
    os.open in os.supports_dir_fd
    and os.mkdir in os.supports_dir_fd
    and hasattr(os, "O_DIRECTORY")
    and hasattr(os, "O_NOFOLLOW")
)


def open_workspace_root(root: Path) -> tuple[Path, int]:
    """Pin a lexical absolute root without following any directory link."""
    if not _SUPPORTED:
        raise OSError(errno.ENOTSUP, "descriptor-relative no-follow I/O is unavailable")
    absolute = root.expanduser().absolute()
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory_fd = os.open("/", flags)
    try:
        for part in absolute.parts[1:]:
            child_fd = os.open(part, flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = child_fd
        result = directory_fd
        directory_fd = -1
        return absolute, result
    finally:
        if directory_fd >= 0:
            os.close(directory_fd)


def open_workspace_file(
    root: Path,
    relative: Path,
    flags: int,
    *,
    create_parents: bool = False,
    root_fd: int | None = None,
) -> int:
    """Open a file beneath *root* without following a link during the open.

    The returned descriptor belongs to the caller. Root and leaf names are
    canonicalized first to allow stable links inside the workspace; every
    component is then reopened relative to the pinned root without links.
    """
    if not _SUPPORTED:
        raise OSError(errno.ENOTSUP, "descriptor-relative no-follow I/O is unavailable")
    if relative.is_absolute():
        raise OSError(errno.EPERM, "path escapes the locked workspace")
    if root_fd is not None:
        # A live MCP server must never reinterpret its root pathname after
        # startup. Links in this mode fail closed, including links within root.
        parts = relative.parts
        if not parts or any(part in {"", ".", ".."} for part in parts):
            raise OSError(errno.EPERM, "path escapes the locked workspace")
        directory_fd = os.dup(root_fd)
        try:
            directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            for part in parts[:-1]:
                if create_parents:
                    with suppress(FileExistsError):
                        os.mkdir(part, 0o700, dir_fd=directory_fd)
                child_fd = os.open(part, directory_flags, dir_fd=directory_fd)
                os.close(directory_fd)
                directory_fd = child_fd
            return os.open(parts[-1], flags | os.O_NOFOLLOW, 0o600, dir_fd=directory_fd)
        finally:
            os.close(directory_fd)
    try:
        resolved_root = root.resolve(strict=True)
        parts = (resolved_root / relative).resolve().relative_to(resolved_root).parts
    except (ValueError, RuntimeError) as exc:
        raise OSError(errno.EPERM, "path escapes the locked workspace") from exc
    if not parts:
        raise OSError(errno.EISDIR, "workspace root is not a file")

    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory_fd = os.open(resolved_root, directory_flags)
    try:
        for part in parts[:-1]:
            if create_parents:
                with suppress(FileExistsError):
                    os.mkdir(part, 0o700, dir_fd=directory_fd)
            child_fd = os.open(part, directory_flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = child_fd
        return os.open(parts[-1], flags | os.O_NOFOLLOW, 0o600, dir_fd=directory_fd)
    finally:
        os.close(directory_fd)


def read_workspace_bytes(root: Path, relative: Path, *, root_fd: int | None = None) -> bytes:
    """Read bytes beneath the workspace through a no-follow file descriptor."""
    fd = open_workspace_file(root, relative, os.O_RDONLY, root_fd=root_fd)
    with os.fdopen(fd, "rb") as stream:
        return stream.read()


def append_workspace_bytes(
    root: Path, relative: Path, data: bytes, *, root_fd: int | None = None
) -> None:
    """Append bytes beneath the workspace without following replaced links."""
    fd = open_workspace_file(
        root,
        relative,
        os.O_WRONLY | os.O_APPEND | os.O_CREAT,
        create_parents=True,
        root_fd=root_fd,
    )
    with os.fdopen(fd, "ab") as stream:
        stream.write(data)


def open_private_directory(
    path: Path, *, create: bool = False, private_from: Path | None = None
) -> int:
    """Pin an absolute private directory without following any path component.

    Newly created components are owner-only. Existing components at and below
    *private_from* are chmodded through their verified descriptors.
    """
    if not _SUPPORTED:
        raise OSError(errno.ENOTSUP, "descriptor-relative no-follow I/O is unavailable")
    if not path.is_absolute():
        raise OSError(errno.EINVAL, "private directory must be absolute")
    current = Path("/")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory_fd = os.open(current, directory_flags)
    try:
        for part in path.parts[1:]:
            current /= part
            if create:
                with suppress(FileExistsError):
                    os.mkdir(part, 0o700, dir_fd=directory_fd)
            child_fd = os.open(part, directory_flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = child_fd
            if private_from is not None and (
                current == private_from or private_from in current.parents
            ):
                os.fchmod(directory_fd, 0o700)
        result = directory_fd
        directory_fd = -1
        return result
    finally:
        if directory_fd >= 0:
            os.close(directory_fd)
