"""Local origin anchors for HyoDo's append-only ledgers.

A ledger inside the checkout (``.hyodo/agent-events.jsonl``,
``.hyodo/mcp-access.jsonl``) can arrive with the checkout: a clone can ship a
ledger that already shows two hosts, clean policy decisions, and a paired
second device. Parsing cleanly is not the same as having been written here.

Every time HyoDo appends to a ledger it records, in per-user state, the digest
and size of the file it just wrote. A reader then asks one question: are the
bytes on disk exactly the bytes this machine's HyoDo last wrote?

- ``ABSENT``      -- no ledger file.
- ``VERIFIED``    -- the file matches the last local anchor, and every byte in
  it was appended by HyoDo on this machine for this workspace.
- ``UNVERIFIED``  -- the file has no local anchor (it arrived with the tree),
  or HyoDo first appended to a file that already held unanchored bytes.
  Appending never launders those bytes: the anchor stays tainted until the
  ledger file is removed and a fresh one is started.
- ``DIVERGED``    -- an anchor exists but the file changed outside HyoDo.

Only ``VERIFIED`` (or ``ABSENT``) may contribute to a READY verdict.
"""

from __future__ import annotations

import contextlib
import hashlib
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hyodo.user_state import (
    read_json,
    workspace_identity,
    workspace_state_dir,
    workspace_state_path,
    write_json_private,
)

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX platforms
    fcntl = None  # type: ignore[assignment]

LEDGER_ORIGIN_SCHEMA = "hyodo.ledger-origin/v1"
LEDGER_ORIGIN_STATE_NAME = "ledger-origin.json"

ORIGIN_ABSENT = "ABSENT"
ORIGIN_VERIFIED = "VERIFIED"
ORIGIN_UNVERIFIED = "UNVERIFIED"
ORIGIN_DIVERGED = "DIVERGED"


def _digest_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _load_anchors(root: Path) -> dict[str, Any]:
    data, _error = read_json(workspace_state_path(root, LEDGER_ORIGIN_STATE_NAME))
    if (
        not isinstance(data, dict)
        or data.get("schema") != LEDGER_ORIGIN_SCHEMA
        or data.get("workspace_id") != workspace_identity(root)
        or not isinstance(data.get("ledgers"), dict)
    ):
        return {}
    return data["ledgers"]


def _classify(anchor: Any, content: bytes) -> str:
    if not isinstance(anchor, dict):
        return ORIGIN_UNVERIFIED
    if anchor.get("tainted") is True:
        return ORIGIN_UNVERIFIED
    if anchor.get("bytes") != len(content) or anchor.get("digest") != _digest_bytes(content):
        return ORIGIN_DIVERGED
    return ORIGIN_VERIFIED


def ledger_origin(root: Path, relative: Path) -> str:
    """Classify the ledger at *root* / *relative* against its local anchor."""
    resolved = root.expanduser().resolve()
    path = resolved / relative
    if not path.exists():
        return ORIGIN_ABSENT
    try:
        content = path.read_bytes()
    except OSError:
        return ORIGIN_UNVERIFIED
    return _classify(_load_anchors(resolved).get(relative.as_posix()), content)


@contextlib.contextmanager
def _anchor_lock(root: Path) -> Iterator[None]:
    """Serialize append-and-anchor so concurrent writers never race the anchor."""
    if fcntl is None:  # pragma: no cover - non-POSIX platforms
        yield
        return
    directory = workspace_state_dir(root)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (directory / ".ledger-origin.lock").open("a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def anchored_append(root: Path, relative: Path, line: str) -> None:
    """Append *line* to the ledger and move its local anchor forward.

    Raises ``OSError`` when the ledger cannot be written. A failure to write
    the anchor itself is swallowed: the ledger line is still recorded, and the
    next reader sees ``DIVERGED`` rather than a false ``VERIFIED``.
    """
    resolved = root.expanduser().resolve()
    path = resolved / relative
    key = relative.as_posix()
    with _anchor_lock(resolved):
        anchors = _load_anchors(resolved)
        try:
            before = path.read_bytes() if path.exists() else b""
        except OSError:
            before = None
        if before == b"":
            tainted = False
        elif before is None:
            tainted = True
        else:
            # Bytes that were not verifiably ours stay unverified forever:
            # appending one honest line must never launder a shipped ledger.
            tainted = _classify(anchors.get(key), before) != ORIGIN_VERIFIED
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
        try:
            content = path.read_bytes()
            anchors[key] = {
                "digest": _digest_bytes(content),
                "bytes": len(content),
                "tainted": tainted,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            write_json_private(
                resolved,
                LEDGER_ORIGIN_STATE_NAME,
                {
                    "schema": LEDGER_ORIGIN_SCHEMA,
                    "workspace_id": workspace_identity(resolved),
                    "ledgers": anchors,
                },
            )
        except OSError:
            pass
