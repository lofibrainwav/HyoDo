"""Per-user authority state, kept outside every checkout.

Operator decisions -- which BYOG command set may run, what policy trust level
was granted, which caller is paired, which scan exceptions were reviewed, and
which ledger bytes this machine wrote -- must not be readable from the tree
being verified. Anything inside a checkout can be authored by that checkout: a
cloned repository can ship a ``.hyodo/gates-trust.json`` as easily as it ships
a ``.hyodo/gates.toml``. A receipt the verified party can write is not a
receipt.

This module owns only *where* that state lives:

- ``user_state_home()`` is ``$HYODO_STATE_HOME`` or ``~/.hyodo/state``.
- ``workspace_identity(root)`` is a digest of the resolved checkout path. A
  clone at another path, or a copy of the tree, is a different workspace and
  inherits nothing.
- ``workspace_state_dir(root)`` is that workspace's private directory.

A same-named file inside the checkout carries zero authority. Callers report
its presence (``checkout_shadow``) so it is never silently mistaken for state
that was honored.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import stat
import uuid
from pathlib import Path
from typing import Any

from hyodo.workspace_io import open_private_directory

USER_STATE_ENV_VAR = "HYODO_STATE_HOME"
WORKSPACE_IDENTITY_PREFIX = "sha256:"


def user_state_home() -> Path:
    """Return the root of per-user HyoDo authority state."""
    override = os.environ.get(USER_STATE_ENV_VAR)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".hyodo" / "state"


def workspace_identity(root: Path, *, pinned: bool = False) -> str:
    """Return ``sha256:<hex>`` of the resolved checkout path."""
    resolved = str(root.absolute() if pinned else root.expanduser().resolve())
    return WORKSPACE_IDENTITY_PREFIX + hashlib.sha256(resolved.encode("utf-8")).hexdigest()


def workspace_state_dir(root: Path, *, pinned: bool = False) -> Path:
    """Return the private per-user directory holding *root*'s authority state."""
    digest = workspace_identity(root, pinned=pinned).removeprefix(WORKSPACE_IDENTITY_PREFIX)
    return user_state_home() / "workspaces" / digest[:32]


def state_home_symlink() -> Path | None:
    """Return the first symlinked component of the state home path, if any.

    Authority state is opened with a no-follow walk from ``/``, so a state
    home reached through a symlink (for example macOS ``/var`` ->
    ``/private/var``) cannot be written or read. That refusal is deliberate;
    this only lets a caller name the cause instead of a bare "unobserved".
    """
    current = Path("/")
    for part in user_state_home().absolute().parts[1:]:
        current /= part
        if current.is_symlink():
            return current
        if not current.exists():
            return None
    return None


def ensure_workspace_state_dir(root: Path) -> Path:
    """Create *root*'s state directory with every level owner-only (0700).

    ``mkdir(parents=True, mode=...)`` applies the mode to the leaf only, which
    would leave the list of workspaces readable to other local users.
    """
    directory, fd = open_workspace_state_dir(root)
    os.close(fd)
    return directory


def open_workspace_state_dir(
    root: Path, *, create: bool = True, pinned: bool = False
) -> tuple[Path, int]:
    """Return the private workspace state path and a pinned directory handle."""
    home = user_state_home().absolute()
    directory = workspace_state_dir(root, pinned=pinned).absolute()
    fd = open_private_directory(directory, create=create, private_from=home)
    return directory, fd


def workspace_state_path(root: Path, name: str) -> Path:
    """Return the path of one authority file for *root* in user state."""
    return workspace_state_dir(root) / name


def checkout_shadow(root: Path, relative: Path) -> bool:
    """Whether the checkout carries a same-named file that is ignored."""
    return (root.expanduser().resolve() / relative).exists()


def file_digest(path: Path) -> str | None:
    """Return ``sha256:<hex>`` of *path*'s bytes, or ``None`` if unreadable."""
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def read_json(path: Path) -> tuple[Any, str | None]:
    """Read one JSON document, distinguishing missing from unreadable.

    Returns ``(data, error)``; ``error`` is ``None``, ``"missing"``, or
    ``"invalid"``.
    """
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, "invalid"


def read_json_private(root: Path, name: str, *, pinned: bool = False) -> tuple[Any, str | None]:
    """Read a workspace state JSON file through its pinned private directory."""
    try:
        _, directory_fd = open_workspace_state_dir(root, create=False, pinned=pinned)
        try:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd)
            with os.fdopen(fd, "r", encoding="utf-8") as handle:
                return json.load(handle), None
        finally:
            os.close(directory_fd)
    except FileNotFoundError:
        return None, "missing"
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, "invalid"


def write_json_private(root: Path, name: str, payload: Any, *, pinned: bool = False) -> Path:
    """Atomically write *payload* as owner-only JSON into *root*'s state dir.

    Raises ``OSError`` when the state cannot be written; callers decide
    whether that is fatal. The workspace's resolved path is written beside the
    state so a person reading ``~/.hyodo/state`` can tell which checkout a
    directory belongs to.
    """
    directory, directory_fd = open_workspace_state_dir(root, pinned=pinned)
    try:
        try:
            marker = os.stat("workspace.json", dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            marker = None
        if marker is not None and stat.S_ISLNK(marker.st_mode):
            raise OSError("private state marker is a symlink")
        if marker is None:
            _atomic_write_at(
                directory_fd,
                "workspace.json",
                {
                    "root": str(root.absolute() if pinned else root.expanduser().resolve()),
                    "workspace_id": workspace_identity(root, pinned=pinned),
                },
            )
        _atomic_write_at(directory_fd, name, payload)
        return directory / name
    finally:
        os.close(directory_fd)


def _atomic_write_at(directory_fd: int, name: str, payload: Any) -> None:
    if not name or name in {".", ".."} or "/" in name:
        raise OSError("invalid private state filename")
    try:
        existing = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        existing = None
    if existing is not None and stat.S_ISLNK(existing.st_mode):
        raise OSError("private state file is a symlink")
    temporary = f".{name}.{uuid.uuid4().hex}.tmp"
    fd = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=directory_fd,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        os.replace(temporary, name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temporary, dir_fd=directory_fd)
        raise
