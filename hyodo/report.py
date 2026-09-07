"""Local, evidence-only FDE sign-off report rendering."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any

import hyodo
from hyodo.event_graph import build_event_graph, render_event_graph_json
from hyodo.events import read_agent_events
from hyodo.graph_export import compute_backlinks
from hyodo.graph_view import build_actor_rows
from hyodo.policy import POLICY_RELATIVE_PATH, try_load_policy

REPORTS_RELATIVE_DIR = Path(".hyodo") / "reports"

SARIF_SCHEMA_URI = "https://json.schemastore.org/sarif-2.1.0.json"


def _eval_summary(root: Path) -> tuple[str, float | None]:
    ledger = root / ".hyodo" / "eval-runs.jsonl"
    if not ledger.exists():
        return "Not measured", None
    try:
        rows = [
            json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line
        ]
    except (OSError, json.JSONDecodeError):
        return "Not measured", None
    rates: list[float] = []
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("pass_rate"), (int, float)):
            rates.append(float(row["pass_rate"]))
    return (f"{rates[-1] * 100:.1f}%", rates[-1]) if rates else ("Not measured", None)


def _collect_evidence(root: Path) -> dict[str, Any]:
    """Collect the local evidence spine shared by all report formats."""
    events, corrupt = read_agent_events(root)

    def _measured(event: dict[str, Any]) -> dict[str, Any]:
        """Policy block only when HyoDo itself evaluated it (``evaluated_by`` stamped).

        A caller can put ``{"policy": {"decision": "ALLOW"}}`` in its own event, so an
        unstamped decision is an assertion, not evidence, and must never be counted.
        """
        block = event.get("policy")
        if isinstance(block, dict) and block.get("evaluated_by"):
            return block
        return {}

    # A ledger we could not read is not an empty ledger. Saying "Events: 0" for both
    # turns a broken observation into a clean bill of health on the sign-off document.
    ledger_unreadable = events is None
    events = events or []
    allow = sum(_measured(event).get("decision") == "ALLOW" for event in events)
    deny = sum(_measured(event).get("decision") == "DENY" for event in events)
    unevaluated = len(events) - sum(bool(_measured(event)) for event in events)
    policy, policy_error = try_load_policy(root / POLICY_RELATIVE_PATH)
    eval_text, _ = _eval_summary(root)
    policy_text = (
        f"allowlist: {', '.join(policy.allowed_tools or ()) or 'not configured'}"
        if policy is not None
        else "Not measured"
    )
    return {
        "events": events,
        "corrupt": corrupt,
        "ledger_unreadable": ledger_unreadable,
        "allow": allow,
        "deny": deny,
        "unevaluated": unevaluated,
        "eval_text": eval_text,
        "policy_text": policy_text,
        "policy": policy,
        "policy_error": policy_error,
    }


def _render_sarif(evidence: dict[str, Any]) -> str:
    """Render the evidence spine as a SARIF v2.1.0 log.

    Only measured HyoDo policy decisions become results: a DENY is an error and
    an unreadable ledger is surfaced as a tool notification, never converted into
    a clean run. Unmeasured evidence stays out of ``results`` entirely so the
    GitHub Security tab cannot display "not measured" as "no alerts".
    """
    rules: list[dict[str, Any]] = [
        {
            "id": "hyodo/policy-deny",
            "name": "PolicyDeny",
            "shortDescription": {"text": "HyoDo policy evaluation denied an agent action."},
            "helpUri": "https://github.com/lofibrainwav/HyoDo#readme",
            "defaultConfiguration": {"level": "error"},
        },
        {
            "id": "hyodo/ledger-unreadable",
            "name": "LedgerUnreadable",
            "shortDescription": {"text": "The HyoDo evidence ledger exists but could not be read."},
            "helpUri": "https://github.com/lofibrainwav/HyoDo#readme",
            "defaultConfiguration": {"level": "error"},
        },
    ]
    results: list[dict[str, Any]] = [
        {
            "ruleId": "hyodo/policy-deny",
            "level": "error",
            "message": {"text": "HyoDo policy recorded a DENY decision for this action."},
        }
        for event in evidence["events"]
        if isinstance(event, dict)
        and isinstance(event.get("policy"), dict)
        and event["policy"].get("evaluated_by")
        and event["policy"].get("decision") == "DENY"
    ]
    if evidence["ledger_unreadable"]:
        results.append(
            {
                "ruleId": "hyodo/ledger-unreadable",
                "level": "error",
                "message": {
                    "text": (
                        "The HyoDo evidence ledger exists but could not be read; "
                        "this is not equivalent to zero events."
                    )
                },
            }
        )
    log = {
        "$schema": SARIF_SCHEMA_URI,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "HyoDo",
                        "version": hyodo.__version__,
                        "informationUri": "https://github.com/lofibrainwav/HyoDo",
                        "rules": rules,
                    }
                },
                "results": results,
                "invocations": [
                    {
                        "executionSuccessful": not evidence["ledger_unreadable"],
                        "properties": {
                            "evaluated_allow": evidence["allow"],
                            "evaluated_deny": evidence["deny"],
                            "unevaluated_events": evidence["unevaluated"],
                            "corrupt_event_lines": evidence["corrupt"],
                            "eval_pass_rate": evidence["eval_text"],
                        },
                    }
                ],
            }
        ],
    }
    return json.dumps(log, indent=2) + "\n"


def build_report_graph(root: Path, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the live `hyodo.evidence-graph/v1` dict for *root*.

    Shared by ``hyodo report --format graph`` and the local graph viewer's
    ``GET /api/graph`` (`hyodo/cli/main.py`) so both read the same ledger
    with identical corrupt/unreadable and mission-policy handling — the
    viewer never computes a second, looser notion of "ready".

    Package 2-C adds two additive fields on top of 1-B's shape:
    ``backlinks`` (the reverse index of every non-broken ``evidence_refs``
    entry, `hyodo.graph_export.compute_backlinks`) and ``rows`` (the
    per-actor row tree with role/hyo-hierarchy annotations,
    `hyodo.graph_view.build_actor_rows`) — the same rows the ``/graph``
    page and the actor-rings endpoint (`GET /api/actor`) render from.
    Neither field changes this function's ``status``/``reason`` contract.
    """
    evidence = evidence if evidence is not None else _collect_evidence(root)
    graph = build_event_graph(
        evidence["events"],
        corrupt=evidence["corrupt"],
        ledger_unreadable=evidence["ledger_unreadable"],
    )
    policy = evidence["policy"]
    if (
        policy is not None
        and policy.require_mission_prompt
        and graph["summary"]["intent_unobserved_runs"]
        and graph["status"] == "READY"
    ):
        graph["status"] = "UNOBSERVED"
        graph["reason"] = f"mission_unobserved:{graph['summary']['intent_unobserved_runs'][0]}"
    graph["backlinks"] = compute_backlinks(graph["edges"])
    graph["rows"] = build_actor_rows(graph["nodes"], graph["edges"])
    return graph


def render_report(root: Path, report_format: str) -> tuple[str, str, dict[str, Any]]:
    """Render deterministic local Markdown, HTML, or SARIF and return its SHA-256 hash."""
    evidence = _collect_evidence(root)
    events = evidence["events"]
    allow = evidence["allow"]
    deny = evidence["deny"]
    unevaluated = evidence["unevaluated"]
    corrupt = evidence["corrupt"]
    eval_text = evidence["eval_text"]
    policy_text = evidence["policy_text"]
    policy_error = evidence["policy_error"]

    details = {"events": len(events), "allow": allow, "deny": deny, "eval_pass_rate": eval_text}

    if report_format == "graph":
        graph = build_report_graph(root, evidence)
        graph_json = render_event_graph_json(graph)
        digest = hashlib.sha256(graph_json.encode("utf-8")).hexdigest()
        summary = graph["summary"]
        return (
            graph_json,
            digest,
            {
                "status": graph["status"],
                "reason": graph["reason"],
                "events": summary["events"],
                "edges": summary["edges"],
                "parent_links": summary["parent_links"],
                "evidence_refs": summary["evidence_refs"],
                "unresolved_refs": summary["unresolved_refs"],
                "corrupt_event_lines": summary["corrupt_event_lines"],
            },
        )

    if report_format == "sarif":
        sarif = _render_sarif(evidence)
        digest = hashlib.sha256(sarif.encode("utf-8")).hexdigest()
        return sarif, digest, details

    spine_line = (
        "Events: UNOBSERVED (ledger exists but could not be read) — this is not zero events"
        if evidence["ledger_unreadable"]
        else f"Events: {len(events)} (ALLOW: {allow}, DENY: {deny})"
    )
    lines = [
        "# HyoDo FDE sign-off report",
        "",
        "## Scope and non-goals",
        "Local evidence summary only. This report does not approve deployment, certify compliance, or intercept agents.",
        "",
        "## Policy summary",
        f"Policy: {policy_text}" + (f" ({policy_error})" if policy_error else ""),
        "",
        "## Evidence spine",
        spine_line,
        f"Unevaluated by HyoDo (caller-asserted or no policy run): {unevaluated}",
        f"Corrupt event lines: {corrupt}",
        "",
        "## Schema gate results",
        "Schema gate results: Not measured (no persisted schema result artifact)",
        "",
        "## Eval results",
        f"Eval pass rate: {eval_text}"
        if eval_text != "Not measured"
        else "Eval pass rate: Not measured",
        "",
        "## Residual risks and not measured",
        "Not measured evidence is not PASS. Human review remains required.",
        "",
        "## Human sign-off",
        "Name: ____________________  Role: ____________________  Date: ____________________",
        "",
    ]
    markdown = "\n".join(lines)
    digest = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    if report_format == "md":
        return markdown, digest, details
    body = "\n".join(f"<p>{html.escape(line)}</p>" if line else "" for line in lines)
    return f"<!doctype html>\n<html><body>{body}</body></html>\n", digest, details


def write_report(root: Path, report_format: str) -> tuple[int, dict[str, Any]]:
    """Write one local report and return the observable CLI summary."""
    try:
        content, digest, details = render_report(root, report_format)
        suffix = "graph.json" if report_format == "graph" else report_format
        relative = REPORTS_RELATIVE_DIR / f"hyodo-report.{suffix}"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        return 2, {"status": "UNOBSERVED", "reason": f"cannot write report: {exc}"}
    status = str(details.pop("status", "READY"))
    reason = details.pop("reason", None)
    exit_code = 0 if status == "READY" else 2
    summary = {
        "status": status,
        "result_path": relative.as_posix(),
        "report_hash": digest,
        **details,
    }
    if reason is not None:
        summary["reason"] = reason
    return exit_code, summary
