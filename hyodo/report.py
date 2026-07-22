"""Local, evidence-only FDE sign-off report rendering."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any

from hyodo.events import read_agent_events
from hyodo.policy import POLICY_RELATIVE_PATH, try_load_policy

REPORTS_RELATIVE_DIR = Path(".hyodo") / "reports"


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


def render_report(root: Path, report_format: str) -> tuple[str, str, dict[str, Any]]:
    """Render deterministic local Markdown or HTML and return its SHA-256 hash."""
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
        f"Events: {len(events)} (ALLOW: {allow}, DENY: {deny})",
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
        return (
            markdown,
            digest,
            {"events": len(events), "allow": allow, "deny": deny, "eval_pass_rate": eval_text},
        )
    body = "\n".join(f"<p>{html.escape(line)}</p>" if line else "" for line in lines)
    return (
        f"<!doctype html>\n<html><body>{body}</body></html>\n",
        digest,
        {"events": len(events), "allow": allow, "deny": deny, "eval_pass_rate": eval_text},
    )


def write_report(root: Path, report_format: str) -> tuple[int, dict[str, Any]]:
    """Write one local report and return the observable CLI summary."""
    try:
        content, digest, details = render_report(root, report_format)
        relative = REPORTS_RELATIVE_DIR / f"hyodo-report.{report_format}"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        return 2, {"status": "UNOBSERVED", "reason": f"cannot write report: {exc}"}
    return 0, {
        "status": "READY",
        "result_path": relative.as_posix(),
        "report_hash": digest,
        **details,
    }
