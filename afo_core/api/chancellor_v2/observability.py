from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

"""Chancellor Graph V2 - Observability Tools.

Tools for viewing traces, events, and checkpoints.
"""


def list_traces() -> list[str]:
    """List all trace IDs from events directory."""
    events_dir = Path("artifacts/chancellor_events")
    if not events_dir.exists():
        return []
    return [f.stem for f in events_dir.glob("*.jsonl")]


def get_trace_events(trace_id: str) -> list[dict[str, Any]]:
    """Get all events for a trace."""
    path = Path("artifacts/chancellor_events") / f"{trace_id}.jsonl"
    if not path.exists():
        return []

    events = []
    for line in path.read_text(encoding="utf-8").strip().split("\n"):
        if line:
            events.append(json.loads(line))
    return events


def get_trace_checkpoints(trace_id: str) -> dict[str, dict[str, Any]]:
    """Get all checkpoints for a trace."""
    checkpoints_dir = Path("artifacts/chancellor_checkpoints") / trace_id
    if not checkpoints_dir.exists():
        return {}

    checkpoints = {}
    for f in checkpoints_dir.glob("*.json"):
        checkpoints[f.stem] = json.loads(f.read_text(encoding="utf-8"))
    return checkpoints


def format_trace_timeline(trace_id: str) -> str:
    """Format trace events as human-readable timeline."""
    events = get_trace_events(trace_id)
    if not events:
        return f"No events found for trace {trace_id}"

    lines = [f"📊 Timeline for trace: {trace_id}", "=" * 60]

    for event in events:
        ts = datetime.fromtimestamp(event["ts"]).strftime("%H:%M:%S.%f")[:-3]
        step = event["step"]
        ev_type = event["event"]
        ok = "✅" if event["ok"] else "❌"
        detail = event.get("detail", "")
        detail_str = f" ({detail})" if detail else ""

        lines.append(f"[{ts}] {ok} {step:10} | {ev_type}{detail_str}")

    return "\n".join(lines)


def format_trace_summary(trace_id: str) -> str:
    """Format trace summary with checkpoints and final state."""
    events = get_trace_events(trace_id)
    checkpoints = get_trace_checkpoints(trace_id)

    if not events:
        return f"No trace found: {trace_id}"

    # Extract stats
    steps_ok = sum(1 for e in events if e["event"] == "exit" and e["ok"])
    steps_fail = sum(1 for e in events if not e["ok"])

    # Get final checkpoint
    final_checkpoint = checkpoints.get("REPORT") or checkpoints.get("VERIFY") or {}
    errors = final_checkpoint.get("errors", [])

    lines = [
        f"📋 Summary for trace: {trace_id}",
        "=" * 60,
        f"Total events:     {len(events)}",
        f"Steps completed:  {steps_ok}",
        f"Steps failed:     {steps_fail}",
        f"Checkpoints:      {list(checkpoints.keys())}",
        f"Errors:           {errors if errors else 'None'}",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    traces = list_traces()
    print(f"Found {len(traces)} traces\n")

    if traces:
        # Show most recent trace
        latest = sorted(traces)[-1]
        print(format_trace_timeline(latest))
        print()
        print(format_trace_summary(latest))
