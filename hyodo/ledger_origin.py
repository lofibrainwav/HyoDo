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

The anchor also carries the ledger's continuity (Eternity evidence). ``seq``
counts the lines HyoDo appended here and never goes backwards, even when the
ledger file is restarted. When HyoDo appends after the file changed outside
it, the break is recorded as a gap -- ``{"after_seq", "reason",
"recorded_at"}`` -- instead of being left as silence: a gap says "not
observed here", which is different from "nothing happened". Gaps are reported,
never repaired, and they do not change the origin classification above.
"""

from __future__ import annotations

import contextlib
import hashlib
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hyodo.user_state import (
    ensure_workspace_state_dir,
    read_json,
    workspace_identity,
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

GAP_UNANCHORED = "unanchored_prior_bytes"
GAP_CHANGED = "prior_bytes_changed_outside_hyodo"
GAP_UNREADABLE = "prior_bytes_unreadable"
GAP_RESTARTED = "ledger_restarted"
GAP_CONCURRENT = "concurrent_writer"
#: Newest gaps kept per ledger; ``gap_count`` still counts every one.
MAX_RECORDED_GAPS = 100


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


def ledger_continuity(root: Path, relative: Path) -> dict[str, Any]:
    """Report the ledger's origin with its local sequence and recorded gaps.

    ``seq`` is ``None`` when HyoDo has no anchor for this ledger: nothing was
    counted here, which is not the same as zero lines.
    """
    resolved = root.expanduser().resolve()
    anchor = _load_anchors(resolved).get(relative.as_posix())
    anchor = anchor if isinstance(anchor, dict) else {}
    seq = anchor.get("seq")
    gaps = anchor.get("gaps")
    gaps = [gap for gap in gaps if isinstance(gap, dict)] if isinstance(gaps, list) else []
    gap_count = anchor.get("gap_count")
    return {
        "origin": ledger_origin(resolved, relative),
        "seq": seq if isinstance(seq, int) else None,
        "gap_count": gap_count if isinstance(gap_count, int) else len(gaps),
        "gaps": gaps,
    }


def _prior_gap(anchor: Any, before: bytes | None) -> str | None:
    """Name the break between the last anchor and the bytes found now, if any."""
    if before is None:
        return GAP_UNREADABLE
    if not isinstance(anchor, dict):
        return GAP_UNANCHORED if before else None
    if anchor.get("bytes") == len(before) and anchor.get("digest") == _digest_bytes(before):
        return None
    return GAP_RESTARTED if before == b"" else GAP_CHANGED


def _prior_seq(anchor: Any, before: bytes | None) -> int:
    """Sequence reached before this append; derived for pre-sequence anchors."""
    if isinstance(anchor, dict):
        seq = anchor.get("seq")
        if isinstance(seq, int) and seq >= 0:
            return seq
        # An anchor written before sequences existed: when it still matches,
        # every line in the file was appended by HyoDo, so the lines count.
        if before and _prior_gap(anchor, before) is None and anchor.get("tainted") is not True:
            return before.count(b"\n")
    return 0


@contextlib.contextmanager
def _anchor_lock(root: Path) -> Iterator[None]:
    """Serialize append-and-anchor so concurrent writers never race the anchor."""
    if fcntl is None:  # pragma: no cover - non-POSIX platforms
        yield
        return
    directory = ensure_workspace_state_dir(root)
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
        previous = anchors.get(key)
        seq_before = _prior_seq(previous, before)
        previous_gaps = previous.get("gaps") if isinstance(previous, dict) else None
        gaps = [g for g in previous_gaps if isinstance(g, dict)] if previous_gaps else []
        previous_count = previous.get("gap_count") if isinstance(previous, dict) else None
        gap_count = previous_count if isinstance(previous_count, int) else len(gaps)
        gap_reasons = [reason] if (reason := _prior_gap(previous, before)) else []
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
            # Anything other than exactly "what was there + our line" means a
            # writer outside this lock touched the file; never fold its bytes
            # into an anchor as if HyoDo wrote them.
            if before is None or content != before + line.encode("utf-8"):
                tainted = True
                if before is not None:
                    gap_reasons.append(GAP_CONCURRENT)
            now = datetime.now(timezone.utc).isoformat()
            for gap_reason in gap_reasons:
                gaps.append({"after_seq": seq_before, "reason": gap_reason, "recorded_at": now})
                gap_count += 1
            anchors[key] = {
                "digest": _digest_bytes(content),
                "bytes": len(content),
                "tainted": tainted,
                "updated_at": now,
                "seq": seq_before + 1,
                "gap_count": gap_count,
                "gaps": gaps[-MAX_RECORDED_GAPS:],
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
