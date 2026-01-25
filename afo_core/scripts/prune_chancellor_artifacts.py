from __future__ import annotations

import argparse
import contextlib
import time
from dataclasses import dataclass
from pathlib import Path

"""Chancellor Artifacts Pruning Script.

Cleans up old trace events and checkpoints per retention policy.
Default: DRY-RUN (no deletion). Use --apply to actually delete.
"""


EVENTS_DIR = Path("artifacts/chancellor_events")
CHECKPOINTS_DIR = Path("artifacts/chancellor_checkpoints")


@dataclass(frozen=True)
class TraceItem:
    """Represents a trace with its metadata."""

    trace_id: str
    events_path: Path
    mtime: float


def _iter_events() -> list[TraceItem]:
    """Iterate over all event files, sorted by mtime (newest first)."""
    if not EVENTS_DIR.exists():
        return []

    items: list[TraceItem] = []
    for p in EVENTS_DIR.glob("*.jsonl"):
        try:
            st = p.stat()
            trace_id = p.stem
            items.append(TraceItem(trace_id=trace_id, events_path=p, mtime=st.st_mtime))
        except FileNotFoundError:
            continue

    items.sort(key=lambda x: x.mtime, reverse=True)
    return items


def _bytes_of_path(path: Path) -> int:
    """Calculate total bytes of a file or directory."""
    if not path.exists():
        return 0

    if path.is_file():
        try:
            return path.stat().st_size
        except FileNotFoundError:
            return 0

    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except FileNotFoundError:
                continue
    return total


def _rm(path: Path, apply: bool) -> tuple[int, int]:
    """Remove file or directory, return (files_count, bytes_count)."""
    files = 0
    bytes_ = 0

    if not path.exists():
        return (0, 0)

    bytes_ = _bytes_of_path(path)

    if apply:
        if path.is_file():
            try:
                path.unlink()
                files = 1
            except FileNotFoundError:
                pass
        else:
            # Remove directory contents
            for p in sorted(path.rglob("*"), reverse=True):
                if p.is_file():
                    try:
                        p.unlink()
                        files += 1
                    except FileNotFoundError:
                        pass
                elif p.is_dir():
                    with contextlib.suppress(OSError):
                        p.rmdir()
            with contextlib.suppress(OSError):
                path.rmdir()
    else:
        # DRY-RUN: just count
        if path.is_file():
            files = 1
        else:
            for p in path.rglob("*"):
                if p.is_file():
                    files += 1

    return (files, bytes_)


def _human(n: int) -> str:
    """Format bytes as human-readable size."""
    units = ["B", "KB", "MB", "GB", "TB"]
    x = float(n)
    for u in units:
        if x < 1024.0:
            return f"{x:.1f}{u}"
        x /= 1024.0
    return f"{x:.1f}PB"


def main() -> int:
    """Main entry point."""
    ap = argparse.ArgumentParser(description="Prune old Chancellor artifacts per retention policy")
    ap.add_argument(
        "--keep-traces",
        type=int,
        default=200,
        help="Keep at least N most recent traces (default: 200)",
    )
    ap.add_argument(
        "--keep-days",
        type=int,
        default=14,
        help="Keep traces from last D days (default: 14)",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete files (default: dry-run)",
    )
    args = ap.parse_args()

    now = time.time()
    cutoff = now - (args.keep_days * 24 * 60 * 60)

    events = _iter_events()
    keep_ids = {t.trace_id for t in events[: max(args.keep_traces, 0)]}
    to_delete: list[str] = []

    for t in events:
        # Keep if in recent N
        if t.trace_id in keep_ids:
            continue
        # Keep if within D days
        if t.mtime >= cutoff:
            continue
        # Delete candidate
        to_delete.append(t.trace_id)

    total_files = 0
    total_bytes = 0

    for trace_id in to_delete:
        ev = EVENTS_DIR / f"{trace_id}.jsonl"
        ck = CHECKPOINTS_DIR / trace_id
        f1, b1 = _rm(ev, args.apply)
        f2, b2 = _rm(ck, args.apply)
        total_files += f1 + f2
        total_bytes += b1 + b2

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] keep_traces={args.keep_traces} keep_days={args.keep_days}")
    print(f"events_found={len(events)} delete_traces={len(to_delete)}")
    print(f"delete_files={total_files} delete_bytes={_human(total_bytes)}")

    if not args.apply and len(to_delete) > 0:
        print("next: run with --apply to delete")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
