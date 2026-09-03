"""MCP access ledger — audit trail for tool invocations (M4 slice 2).

Append-only local JSONL at ``.hyodo/mcp-access.jsonl``.  Each entry records
one MCP tool call served by the local adapter: which tool, which workspace,
how long it took, and whether it succeeded.

This module is intentionally separate from :mod:`hyodo.events` (which
records *agent* steps) and from :mod:`hyodo.policy` (which defines rules).
The access ledger exists so operators can inspect what the MCP adapter has
actually served, without needing to parse agent-event payloads.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ACCESS_LEDGER_PATH = Path(".hyodo") / "mcp-access.jsonl"


@dataclass(frozen=True)
class AccessEntry:
    """One recorded MCP tool invocation."""

    timestamp: str  # ISO 8601
    tool_name: str
    root: str
    exit_code: int
    duration_ms: int
    caller_id: str | None = None


def record_access(entry: AccessEntry, root: Path | None = None) -> Path:
    """Append one access entry to the ledger.  Never raises.

    Best-effort: a ledger write failure does not propagate.  The caller
    (the MCP server) must remain functional even when the ledger is on a
    read-only mount or the disk is full.  On failure the error is printed
    to stderr and the function returns the *intended* path anyway so
    callers don't have to branch on the result type.

    Returns the path to the ledger file (whether or not the write
    succeeded).
    """
    if root is None:
        root = Path(".")
    path = root / ACCESS_LEDGER_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(entry), sort_keys=True) + "\n")
    except OSError:
        print(f"[hyodo] access ledger write failed: {path}", file=sys.stderr)
    return path


def read_access_log(root: Path, limit: int = 100) -> list[AccessEntry]:
    """Read the last *limit* entries from the access ledger.

    Returns entries in chronological (file) order.  If the ledger file
    does not exist yet, returns an empty list.  Malformed lines are
    silently skipped.
    """
    path = root / ACCESS_LEDGER_PATH
    if not path.exists():
        return []

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []

    entries: list[AccessEntry] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            try:
                entries.append(
                    AccessEntry(
                        timestamp=parsed.get("timestamp", ""),
                        tool_name=parsed.get("tool_name", ""),
                        root=parsed.get("root", ""),
                        exit_code=int(parsed.get("exit_code", -1)),
                        duration_ms=int(parsed.get("duration_ms", 0)),
                        caller_id=parsed.get("caller_id"),
                    )
                )
            except (TypeError, ValueError):
                continue

    # Return the last *limit* entries (most recent)
    if len(entries) > limit:
        return entries[-limit:]
    return entries
