"""MCP reader self-registration and cutover census.

A long-running ``hyodo mcp stdio`` process resolves its ``--root`` once, at
startup.  When a host later points a runtime symlink at a new slot, readers that
were already running keep measuring the old slot with the code they loaded.
Nothing outside the process can ask a stdio reader who it is: its stdin and
stdout belong to the host that spawned it.

So each reader records its own identity when it starts, keyed by PID *and*
process start time (a reused PID never matches an old record), and removes the
record when it exits.  The census joins those records with the live process
table.  A live reader without a record predates this gate and cannot be judged,
so it counts as old.

A registration is observation evidence written by the reader itself, not a
tamper-proof attestation: a hostile process running as the same user could
forge or delete one.  HyoDo does not defend against a hostile local host.

This module observes and records.  It never restarts, kills, or reconfigures a
reader, and its cutover status is evidence for the host's promotion decision,
not the decision itself.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hyodo import __version__

READER_SCHEMA_VERSION = "hyodo.mcp-reader/v1"
CENSUS_SCHEMA_VERSION = "hyodo.mcp-reader-census/v1"
READER_DIR_ENV = "HYODO_MCP_READER_DIR"

PROMOTION_COMPLETE = "PROMOTION_COMPLETE"
PROMOTION_INCOMPLETE = "PROMOTION_INCOMPLETE"
UNOBSERVED = "UNOBSERVED"

_READER_TRANSPORTS = frozenset({"stdio", "serve"})
_PS_TIMEOUT_SECONDS = 10


def default_reader_dir() -> Path:
    """Return the per-user registry that every reader on this machine shares.

    It lives outside any workspace so a census can see readers of every slot,
    including the one being retired.
    """
    override = os.environ.get(READER_DIR_ENV)
    if override:
        return Path(override)
    return Path.home() / ".hyodo" / "runtime" / "mcp-readers"


def _ps(*args: str) -> str | None:
    # ``lstart`` is rendered in the caller's locale and time zone.  Pin both so a
    # reader and a census started from different shells agree on the same text.
    env = {**os.environ, "LC_ALL": "C", "TZ": "UTC"}
    try:
        completed = subprocess.run(
            ["ps", *args],
            capture_output=True,
            text=True,
            env=env,
            timeout=_PS_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def process_start(pid: int) -> str | None:
    """Return the OS start time of *pid*, or ``None`` when it is not observable."""
    output = _ps("-o", "lstart=", "-p", str(pid))
    if output is None:
        return None
    text = " ".join(output.split())
    return text or None


def parent_host(ppid: int) -> str | None:
    """Return the executable name of the process that owns a reader."""
    output = _ps("-o", "comm=", "-p", str(ppid))
    if output is None:
        return None
    text = output.strip()
    return Path(text).name if text else None


def _git_head(root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=_PS_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    head = completed.stdout.strip()
    return head if completed.returncode == 0 and head else None


def reader_transport(command: str) -> str | None:
    """Return ``stdio``/``serve`` when *command* runs a HyoDo MCP reader.

    Matches ``.../hyodo mcp stdio`` and ``python -m hyodo.cli.main mcp stdio``.
    Arguments are split on whitespace, so an executable path containing spaces
    is not recognised; such a reader stays visible through its registration.
    """
    tokens = command.split()
    for index in range(len(tokens) - 1):
        if tokens[index] != "mcp" or tokens[index + 1] not in _READER_TRANSPORTS:
            continue
        launcher = tokens[:index]
        if any(Path(token).name == "hyodo" or token == "hyodo.cli.main" for token in launcher):
            return tokens[index + 1]
    return None


@dataclass(frozen=True)
class ReaderProcess:
    """One live process that looks like a HyoDo MCP reader."""

    pid: int
    ppid: int
    process_start: str
    transport: str


def list_reader_processes() -> list[ReaderProcess] | None:
    """Return live MCP readers from the process table, or ``None`` if unobservable."""
    output = _ps("-Ao", "pid=,ppid=,lstart=,command=")
    if output is None:
        return None
    readers: list[ReaderProcess] = []
    for line in output.splitlines():
        # pid ppid Dow Mon Day HH:MM:SS YYYY command...
        parts = line.split(maxsplit=7)
        if len(parts) < 8:
            continue
        try:
            pid, ppid = int(parts[0]), int(parts[1])
        except ValueError:
            continue
        transport = reader_transport(parts[7])
        if transport is None or pid == os.getpid():
            continue
        readers.append(
            ReaderProcess(
                pid=pid,
                ppid=ppid,
                process_start=" ".join(parts[2:7]),
                transport=transport,
            )
        )
    return readers


_VERSION_LINE = re.compile(r'^__version__ = "([^"]+)"', re.MULTILINE)

CURRENT = "CURRENT"
STALE = "STALE"
UNKNOWN = "UNKNOWN"
STALE_RUNTIME_ERROR = "STALE_RUNTIME_RECONNECT_REQUIRED"


def _version_on_disk() -> str | None:
    """Read the version literal from the file this process imported ``hyodo`` from.

    A package upgrade replaces that file while a long-running reader keeps the
    old module in memory; the tools it spawns then run the new code.
    """
    import hyodo

    try:
        text = Path(hyodo.__file__).read_text(encoding="utf-8")
    except (OSError, TypeError, UnicodeDecodeError):
        return None
    match = _VERSION_LINE.search(text)
    return match.group(1) if match else None


@dataclass(frozen=True)
class ReaderPin:
    """What one reader bound itself to when it started.

    The root is pinned on purpose: a session whose target silently changed
    between two calls would be worse than a stale one.  Instead, every call
    compares the pin with what the configured root points at *now*, and a
    reader whose pin no longer holds says so instead of measuring.
    """

    configured_root: Path
    resolved_root: Path
    server_version: str
    process_start: str | None
    runtime_commit: str | None

    @classmethod
    def at_startup(cls, configured_root: Path, resolved_root: Path) -> ReaderPin:
        """Pin the current process to *resolved_root* and record who it is."""
        return cls(
            configured_root=configured_root,
            resolved_root=resolved_root,
            server_version=__version__,
            process_start=process_start(os.getpid()),
            runtime_commit=_git_head(resolved_root),
        )

    def status(self) -> dict[str, Any]:
        """Return CURRENT or STALE with the observations behind it."""
        reasons: list[str] = []
        try:
            points_to: str | None = str(self.configured_root.expanduser().resolve(strict=True))
        except (OSError, RuntimeError):
            points_to = None
        if points_to is None:
            reasons.append("configured_root_unresolvable")
        elif points_to != str(self.resolved_root):
            reasons.append("root_moved")
        on_disk = _version_on_disk()
        if on_disk is None:
            # The code the tools would run cannot be identified; that is not
            # evidence that it is still the code this reader loaded.
            reasons.append("code_unobservable")
        elif on_disk != self.server_version:
            reasons.append("code_replaced")
        return {
            "state": STALE if reasons else CURRENT,
            "reasons": reasons,
            "action": "RECONNECT_REQUIRED" if reasons else None,
            "reader_pid": os.getpid(),
            "process_start": self.process_start,
            "server_version": self.server_version,
            "code_version_on_disk": on_disk,
            "python_version": ".".join(str(part) for part in sys.version_info[:3]),
            "configured_root": str(self.configured_root),
            "pinned_root": str(self.resolved_root),
            "configured_root_now": points_to,
            "runtime_commit": self.runtime_commit,
        }


def build_registration(root_arg: Path, resolved_root: Path, transport: str) -> dict[str, Any]:
    """Describe the current process as an MCP reader."""
    pid = os.getpid()
    ppid = os.getppid()
    return {
        "schema_version": READER_SCHEMA_VERSION,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "reader_pid": pid,
        "process_start": process_start(pid),
        "parent_pid": ppid,
        "parent_host": parent_host(ppid),
        "transport": transport,
        "server_version": __version__,
        "python_version": ".".join(str(part) for part in sys.version_info[:3]),
        "python_executable": sys.executable,
        "tool_source": str(Path(__file__).resolve().parent),
        "root_arg": str(root_arg),
        "resolved_root": str(resolved_root),
        "runtime_commit": _git_head(resolved_root),
    }


def _pid_exists(pid: int) -> bool:
    """Return False only when the OS process table proves *pid* is absent."""
    if os.name != "posix":
        # The census itself is currently POSIX-ps based. On other hosts, keep
        # residue rather than risk treating an unobservable process as dead.
        return True
    try:
        completed = subprocess.run(
            ["ps", "-p", str(pid), "-o", "pid="],
            capture_output=True,
            text=True,
            timeout=_PS_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return True
    if completed.returncode == 0:
        return completed.stdout.strip() == str(pid)
    return completed.returncode != 1


def prune_retired_registrations(
    *,
    directory: Path | None = None,
    start_lookup: Callable[[int], str | None] = process_start,
    exists_lookup: Callable[[int], bool] = _pid_exists,
) -> int:
    """Remove only registrations whose process is provably gone or reused.

    This runs when a new reader starts. It cleans residue left by SIGTERM,
    SIGKILL, or crashes, where the context manager's finally block may not run.
    If process identity cannot be observed, the record is kept.
    """
    target_dir = Path(directory) if directory is not None else default_reader_dir()
    if not target_dir.is_dir():
        return 0
    removed = 0
    for path in sorted(target_dir.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if (
            not isinstance(record, dict)
            or record.get("schema_version") != READER_SCHEMA_VERSION
            or not isinstance(record.get("reader_pid"), int)
            or not isinstance(record.get("process_start"), str)
        ):
            continue
        pid = record["reader_pid"]
        recorded_start = record["process_start"]
        alive = exists_lookup(pid)
        observed_start = start_lookup(pid) if alive else None
        retired = (not alive) or (observed_start is not None and observed_start != recorded_start)
        if not retired:
            continue
        try:
            path.unlink()
        except OSError:
            continue
        removed += 1
    return removed


def register_reader(
    root_arg: Path,
    resolved_root: Path,
    transport: str,
    *,
    directory: Path | None = None,
) -> Path | None:
    """Atomically write this reader's record and return its path.

    Registration is best effort: a reader that cannot register still serves,
    and the census reports it as unregistered.  Failures go to stderr because
    stdout carries the stdio protocol.
    """
    # A prior reader may have been terminated by signal/crash and skipped
    # registered_reader's finally block. Clean only provably retired records.
    prune_retired_registrations(directory=directory)
    record = build_registration(root_arg, resolved_root, transport)
    if record["process_start"] is None:
        print("[hyodo] mcp reader not registered: process start unobservable", file=sys.stderr)
        return None
    target_dir = Path(directory) if directory is not None else default_reader_dir()
    destination = target_dir / f"{record['reader_pid']}.json"
    payload = json.dumps(record, indent=2, sort_keys=True) + "\n"
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".reader.", suffix=".tmp", dir=target_dir)
    except OSError:
        print(f"[hyodo] mcp reader not registered: {target_dir}", file=sys.stderr)
        return None
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(temporary, destination)
    except OSError:
        with suppress(OSError):
            os.unlink(temporary)
        print(f"[hyodo] mcp reader not registered: {destination}", file=sys.stderr)
        return None
    return destination


@contextmanager
def registered_reader(
    root: Path,
    transport: str,
    *,
    directory: Path | None = None,
) -> Iterator[Path | None]:
    """Hold a registration for the lifetime of one reader."""
    resolved = root.expanduser().resolve()
    path = register_reader(root, resolved, transport, directory=directory)
    try:
        yield path
    finally:
        if path is not None:
            with suppress(OSError):
                path.unlink()


def load_registrations(directory: Path | None = None) -> tuple[list[dict[str, Any]], int]:
    """Return valid registration records and the number of unreadable ones."""
    target_dir = Path(directory) if directory is not None else default_reader_dir()
    if not target_dir.is_dir():
        return [], 0
    records: list[dict[str, Any]] = []
    corrupt = 0
    for path in sorted(target_dir.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            corrupt += 1
            continue
        if (
            not isinstance(raw, dict)
            or raw.get("schema_version") != READER_SCHEMA_VERSION
            or not isinstance(raw.get("reader_pid"), int)
            or not isinstance(raw.get("process_start"), str)
        ):
            corrupt += 1
            continue
        records.append(raw)
    return records, corrupt


def _judge(
    record: dict[str, Any],
    *,
    expected_root: str,
    expected_commit: str | None,
    expected_version: str | None,
) -> list[str]:
    reasons: list[str] = []
    if record.get("resolved_root") != expected_root:
        reasons.append("root_mismatch")
    if expected_commit is not None and record.get("runtime_commit") != expected_commit:
        reasons.append("commit_mismatch")
    if expected_version is not None and record.get("server_version") != expected_version:
        reasons.append("version_mismatch")
    return reasons


def run_census(
    expect_root: Path,
    *,
    promotion_from: str | None = None,
    expect_version: str | None = None,
    directory: Path | None = None,
    processes: list[ReaderProcess] | None = None,
    start_lookup: Callable[[int], str | None] = process_start,
    host_lookup: Callable[[int], str | None] = parent_host,
) -> dict[str, Any]:
    """Judge every live reader against the promoted slot and return a receipt.

    ``processes`` and the lookups exist for tests; by default the live process
    table is read.  A reader is CURRENT only when its own record shows the
    promoted root and commit (and version, when one is expected).  A reader with
    no record is UNKNOWN and counts as old, so the status can only be
    ``PROMOTION_COMPLETE`` when every live reader proved it moved.
    """
    target = expect_root.expanduser().resolve()
    expected_root = str(target)
    expected_commit = _git_head(target)
    live = processes if processes is not None else list_reader_processes()
    records, corrupt = load_registrations(directory)

    receipt: dict[str, Any] = {
        "schema_version": CENSUS_SCHEMA_VERSION,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "promotion_from": promotion_from,
        "promotion_to": expected_root,
        "expected_commit": expected_commit,
        "expected_version": expect_version,
        "commit_judged": expected_commit is not None,
        "registry_dir": str(Path(directory) if directory is not None else default_reader_dir()),
        "corrupt_registrations": corrupt,
        "authority": "evidence only; the host decides whether the promotion is complete",
    }
    if live is None:
        receipt.update(
            {
                "process_table": UNOBSERVED,
                "readers": [],
                "registered_reader_count": len(records),
                "fresh_reader_count": None,
                "old_reader_count": None,
                "stale_reader_count": None,
                "unknown_reader_count": None,
                "retired_reader_count": None,
                "cutover_status": UNOBSERVED,
            }
        )
        return receipt

    by_identity = {(rec["reader_pid"], rec["process_start"]): rec for rec in records}
    seen: set[tuple[int, str]] = set()
    readers: list[dict[str, Any]] = []

    def _add(pid: int, ppid: int | None, start: str, transport: str | None) -> None:
        key = (pid, start)
        if key in seen:
            return
        seen.add(key)
        record = by_identity.get(key)
        if record is None:
            readers.append(
                {
                    "reader_pid": pid,
                    "process_start": start,
                    "parent_pid": ppid,
                    "parent_host": host_lookup(ppid) if ppid is not None else None,
                    "transport": transport,
                    "registration_state": "UNREGISTERED",
                    "server_version": None,
                    "python_version": None,
                    "resolved_root": None,
                    "runtime_commit": None,
                    "reader_status": UNKNOWN,
                    "reasons": ["unregistered"],
                }
            )
            return
        reasons = _judge(
            record,
            expected_root=expected_root,
            expected_commit=expected_commit,
            expected_version=expect_version,
        )
        readers.append(
            {
                "reader_pid": pid,
                "process_start": start,
                "parent_pid": record.get("parent_pid"),
                "parent_host": record.get("parent_host"),
                "transport": record.get("transport"),
                "registration_state": "REGISTERED",
                "server_version": record.get("server_version"),
                "python_version": record.get("python_version"),
                "resolved_root": record.get("resolved_root"),
                "runtime_commit": record.get("runtime_commit"),
                "reader_status": STALE if reasons else CURRENT,
                "reasons": reasons,
            }
        )

    for process in live:
        _add(process.pid, process.ppid, process.process_start, process.transport)
    # A registered reader the command matcher missed is still a reader, as long
    # as the same process (PID and start time) is alive.  A record whose process
    # exited, or whose PID now belongs to another process, is RETIRED.
    retired = 0
    for record in records:
        pid, start = record["reader_pid"], record["process_start"]
        if (pid, start) in seen:
            continue
        if start_lookup(pid) == start:
            _add(pid, record.get("parent_pid"), start, record.get("transport"))
        else:
            retired += 1

    fresh = sum(1 for reader in readers if reader["reader_status"] == CURRENT)
    unknown = sum(1 for reader in readers if reader["reader_status"] == UNKNOWN)
    old = len(readers) - fresh
    receipt.update(
        {
            "process_table": "OBSERVED",
            "readers": readers,
            "registered_reader_count": len(records),
            "fresh_reader_count": fresh,
            "old_reader_count": old,
            "stale_reader_count": old - unknown,
            "unknown_reader_count": unknown,
            "retired_reader_count": retired,
            "cutover_status": PROMOTION_COMPLETE if old == 0 else PROMOTION_INCOMPLETE,
        }
    )
    return receipt
