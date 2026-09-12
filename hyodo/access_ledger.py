"""MCP access ledger — audit trail for tool invocations (M4 slice 2)."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ACCESS_LEDGER_PATH = Path(".hyodo") / "mcp-access.jsonl"


@dataclass(frozen=True)
class AccessEntry:
    """One recorded MCP tool invocation."""

    timestamp: str
    tool_name: str
    root: str
    exit_code: int
    duration_ms: int
    caller_id: str | None = None


@dataclass(frozen=True)
class AccessWriteResult:
    """Observed outcome of one best-effort append."""

    path: Path
    state: str
    reason: str | None = None


@dataclass(frozen=True)
class AccessReadResult:
    """Observed state of the access ledger and its valid entries."""

    state: str
    entries: list[AccessEntry]
    corrupt_lines: int = 0
    reason: str | None = None


def record_access_result(entry: AccessEntry, root: Path | None = None) -> AccessWriteResult:
    """Append one access entry while making persistence loss observable."""
    if root is None:
        root = Path(".")
    path = root / ACCESS_LEDGER_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(entry), sort_keys=True) + "\n")
    except OSError:
        print(f"[hyodo] access ledger write failed: {path}", file=sys.stderr)
        return AccessWriteResult(path=path, state="UNOBSERVED", reason="write_failed")
    return AccessWriteResult(path=path, state="OBSERVED")


def record_access(entry: AccessEntry, root: Path | None = None) -> Path:
    """Compatibility wrapper returning the intended ledger path."""
    return record_access_result(entry, root=root).path


def read_access_log_result(root: Path, limit: int = 100) -> AccessReadResult:
    """Read valid rows while distinguishing absent, corrupt, and unreadable state."""
    path = root / ACCESS_LEDGER_PATH
    if not path.exists():
        return AccessReadResult(state="ABSENT", entries=[])

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return AccessReadResult(state="UNOBSERVED", entries=[], reason="read_failed")

    entries: list[AccessEntry] = []
    corrupt_lines = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            corrupt_lines += 1
            continue
        if not isinstance(parsed, dict):
            corrupt_lines += 1
            continue
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
            corrupt_lines += 1

    if len(entries) > limit:
        entries = entries[-limit:]
    if corrupt_lines:
        return AccessReadResult(
            state="UNOBSERVED",
            entries=entries,
            corrupt_lines=corrupt_lines,
            reason="corrupt_lines",
        )
    return AccessReadResult(state="OBSERVED", entries=entries)


def read_access_log(root: Path, limit: int = 100) -> list[AccessEntry]:
    """Compatibility wrapper returning only valid entries."""
    return read_access_log_result(root, limit=limit).entries
