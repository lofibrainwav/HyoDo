"""Read-only reconciliation projection for tool terminal coverage."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from hyodo.events import read_agent_events
from hyodo.report import build_report_graph
from hyodo.verification_view import build_verification_view

TERMINAL_RECONCILIATION_SCHEMA_VERSION = "hyodo.terminal-reconciliation/v0"
_KNOWN_TOOL_FAMILIES = frozenset({"Bash", "apply_patch"})
# Dated 2026-09-20 producer readback: the measured Codex hook payload carried
# no structured terminal-mode field. This is not a promise about future hosts.
_HOST_TERMINAL_CAPABILITY = {"codex": "UNSUPPORTED_BY_HOST"}


def _host(event: dict[str, Any]) -> str | None:
    """Read an explicit host tag; never infer host identity from an event id."""
    meta = event.get("meta")
    tags = meta.get("tags") if isinstance(meta, dict) else None
    if not isinstance(tags, list):
        return None
    for tag in tags:
        if isinstance(tag, str) and tag.startswith("host:"):
            value = tag.removeprefix("host:").strip()
            return value or None
    return None


def _tool_family(event: dict[str, Any]) -> str:
    tool = event.get("tool")
    name = tool.get("name") if isinstance(tool, dict) else None
    if name in _KNOWN_TOOL_FAMILIES:
        return str(name)
    return "other"


def build_terminal_reconciliation(root: Path) -> dict[str, Any]:
    """Build a non-mutating disposition report for missing terminal callbacks.

    A recorded PostToolUse/tool_result proves RETURNED only; it does not prove
    semantic success. Missing callbacks stay UNOBSERVED. The current Codex
    payload exposes no explicit success/error/cancel/timeout/abort field, so
    absence cannot be upgraded into one of those states.
    """
    events, corrupt = read_agent_events(root)
    if events is None:
        return {
            "schema_version": TERMINAL_RECONCILIATION_SCHEMA_VERSION,
            "status": "UNOBSERVED",
            "authority": "UNOBSERVED",
            "reason": "ledger_unreadable",
            "summary": {
                "corrupt_event_lines": 0,
                "calls_without_terminal_outcome": None,
            },
            "records": [],
        }

    graph = build_report_graph(root)
    view = build_verification_view(graph, root=root)
    missing_ids = view["missing"].get("calls_without_terminal_outcome") or []
    duplicate_ids = view["missing"].get("duplicate_terminal_outcomes") or []
    event_by_id = {
        event.get("event_id"): event for event in events if isinstance(event.get("event_id"), str)
    }

    records: list[dict[str, Any]] = []
    family_counts: Counter[str] = Counter()
    host_counts: Counter[str] = Counter()
    run_counts: Counter[str] = Counter()
    capability_counts: Counter[str] = Counter()

    for call_id in missing_ids:
        event = event_by_id.get(call_id)
        if event is None:
            continue
        family = _tool_family(event)
        host = _host(event)
        run_id = event.get("run_id") if isinstance(event.get("run_id"), str) else None
        capability = _HOST_TERMINAL_CAPABILITY.get(host or "", "UNOBSERVED")
        family_counts[family] += 1
        host_counts[host or "UNOBSERVED"] += 1
        run_counts[run_id or "UNOBSERVED"] += 1
        capability_counts[capability] += 1
        records.append(
            {
                "event_id": call_id,
                "run_id": run_id,
                "actor_id": event.get("actor_id"),
                "tool_name": (
                    event.get("tool", {}).get("name")
                    if isinstance(event.get("tool"), dict)
                    else None
                ),
                "tool_family": family,
                "host": host,
                "producer_terminal_capability": capability,
                "terminal_disposition": "UNOBSERVED",
                "termination_evidence": "UNOBSERVED",
                "reason": "no terminal callback receipt was recorded for this call",
            }
        )

    status = "OBSERVED"
    if duplicate_ids:
        status = "CONTRADICTED"
    elif records:
        status = "RECONCILIATION_REQUIRED"

    terminal_summary = view.get("reconciliation", {}).get("terminal_outcomes", {})
    return {
        "schema_version": TERMINAL_RECONCILIATION_SCHEMA_VERSION,
        "status": status,
        "authority": "UNOBSERVED",
        "reason": (
            "producer_terminal_capability_gap"
            if records
            else "duplicate_terminal_outcomes"
            if duplicate_ids
            else "all_tool_calls_have_one_observed_terminal_receipt"
        ),
        "summary": {
            "corrupt_event_lines": corrupt,
            "calls_without_terminal_outcome": len(records),
            "duplicate_terminal_outcomes": len(duplicate_ids),
            "terminal_counts": terminal_summary.get("counts", {}),
            "by_tool_family": dict(sorted(family_counts.items())),
            "by_host": dict(sorted(host_counts.items())),
            "by_run": dict(sorted(run_counts.items())),
            "by_producer_terminal_capability": dict(sorted(capability_counts.items())),
            "genuinely_missing_proven": 0,
            "unauthorized_runs_proven": 0,
        },
        "records": records,
    }
