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
import tempfile
from pathlib import Path
from typing import Any

USER_STATE_ENV_VAR = "HYODO_STATE_HOME"
WORKSPACE_IDENTITY_PREFIX = "sha256:"


def user_state_home() -> Path:
    """Return the root of per-user HyoDo authority state."""
    override = os.environ.get(USER_STATE_ENV_VAR)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".hyodo" / "state"


def workspace_identity(root: Path) -> str:
    """Return ``sha256:<hex>`` of the resolved checkout path."""
    resolved = str(root.expanduser().resolve())
    return WORKSPACE_IDENTITY_PREFIX + hashlib.sha256(resolved.encode("utf-8")).hexdigest()


def workspace_state_dir(root: Path) -> Path:
    """Return the private per-user directory holding *root*'s authority state."""
    digest = workspace_identity(root).removeprefix(WORKSPACE_IDENTITY_PREFIX)
    return user_state_home() / "workspaces" / digest[:32]


def ensure_workspace_state_dir(root: Path) -> Path:
    """Create *root*'s state directory with every level owner-only (0700).

    ``mkdir(parents=True, mode=...)`` applies the mode to the leaf only, which
    would leave the list of workspaces readable to other local users.
    """
    home = user_state_home()
    directory = workspace_state_dir(root)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    current = directory
    while True:
        with contextlib.suppress(OSError):
            if stat.S_IMODE(current.stat().st_mode) != 0o700:
                os.chmod(current, 0o700)
        if current == home or current.parent == current:
            break
        current = current.parent
    return directory


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


def write_json_private(root: Path, name: str, payload: Any) -> Path:
    """Atomically write *payload* as owner-only JSON into *root*'s state dir.

    Raises ``OSError`` when the state cannot be written; callers decide
    whether that is fatal. The workspace's resolved path is written beside the
    state so a person reading ``~/.hyodo/state`` can tell which checkout a
    directory belongs to.
    """
    directory = ensure_workspace_state_dir(root)
    marker = directory / "workspace.json"
    if not marker.exists():
        _atomic_write(
            marker,
            {"root": str(root.expanduser().resolve()), "workspace_id": workspace_identity(root)},
        )
    path = directory / name
    _atomic_write(path, payload)
    return path


def _atomic_write(path: Path, payload: Any) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise
