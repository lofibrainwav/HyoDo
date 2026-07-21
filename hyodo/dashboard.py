"""Dependency-free local dashboard rendering for HyoDo measurement evidence."""

from __future__ import annotations

import base64
import hashlib
import re
from html import escape
from typing import Any

# Inline auto-refresh poller. The text must stay byte-identical to the sha256
# CSP allowance below, so the page metadata travels in a data attribute instead
# of being interpolated into the script body.
POLL_SCRIPT = """\
const seen = document.currentScript.dataset.measured;
setInterval(() => {
  // A failed poll means the server stopped; keep the last rendered snapshot.
  fetch("/api/evidence", { cache: "no-store" })
    .then((r) => r.json())
    .then((j) => { if (j.measured_at && j.measured_at !== seen) location.reload(); })
    .catch(() => {});
}, 15000);"""

POLL_SCRIPT_SHA256 = base64.b64encode(hashlib.sha256(POLL_SCRIPT.encode("utf-8")).digest()).decode(
    "ascii"
)


def _gate(evidence: dict[str, Any], name: str) -> dict[str, str]:
    value = evidence.get("gates", {}).get(name, {})
    raw_status = value.get("status", "NOT MEASURED")
    return {
        "status": str(getattr(raw_status, "value", raw_status)),
        "message": str(value.get("message", "")),
    }


def _metric(label: str, value: str, source: str, reference: str = "") -> str:
    reference_html = (
        f'<span class="reference">Reference: {escape(reference)}</span>' if reference else ""
    )
    return (
        '<li><span class="metric-label">'
        + escape(label)
        + "</span><strong>"
        + escape(value)
        + "</strong>"
        + reference_html
        + f"<small>Source: {escape(source)}</small></li>"
    )


def _display_message(message: str) -> str:
    """Remove pytest's decorative separator while retaining its measured summary."""
    summary = re.search(r"\d+ passed(?:, \d+ skipped)?(?: in [^=]+)?", message)
    return summary.group(0).strip() if summary else message


def _card(pillar: str, title: str, color: str, body: str) -> str:
    return (
        f'<section class="card {escape(color)}" aria-labelledby="{escape(pillar)}">'
        f'<h2 id="{escape(pillar)}"><span>{escape(pillar.upper())}</span> {escape(title)}</h2>{body}</section>'
    )


def _not_measured(reason: str) -> str:
    return f'<p class="not-measured">Not measured</p><p class="reason">{escape(reason)}</p>'


def render_dashboard_html(evidence: dict[str, Any]) -> str:
    """Render raw evidence without creating a composite score or fake values."""
    typecheck = _gate(evidence, "typecheck")
    tests = _gate(evidence, "tests")
    lint = _gate(evidence, "lint_format")
    safety = evidence.get("safety", {})
    risk = safety.get("risk_score", "Not measured")
    findings = safety.get("findings", [])
    high = sum(1 for finding in findings if finding.get("severity") == "high")
    measured_at = str(evidence.get("measured_at", "Not recorded"))
    target = str(evidence.get("target", "Not recorded"))

    jin = _card(
        "jin",
        "Truth",
        "blue",
        "<ul>"
        + _metric("Type check", f"{typecheck['status']}: {typecheck['message']}", "Pyright")
        + "</ul>",
    )
    seon = _card(
        "seon",
        "Goodness",
        "green",
        "<ul>"
        + _metric("Tests", f"{tests['status']}: {_display_message(tests['message'])}", "pytest")
        + _metric("Safety risk", f"{risk}/100", "HyoDo safe", "0")
        + _metric("High-risk findings", str(high), "HyoDo safe", "0")
        + "</ul>",
    )
    mi = _card(
        "mi",
        "Beauty",
        "purple",
        "<ul>"
        + _metric("Lint and format", f"{lint['status']}: {lint['message']}", "Ruff")
        + "</ul>",
    )
    in_card = _card(
        "in",
        "In / Benevolence",
        "orange",
        _not_measured(
            "No real UI task-completion events are connected to this HyoDo CLI checkout."
        ),
    )
    hyo = _card(
        "hyo",
        "Hyo",
        "gold",
        _not_measured("No consent, undo, or data-protection event source is connected."),
    )
    yeong = _card(
        "yeong",
        "Yeong / Durability",
        "indigo",
        _not_measured(
            "SBOM status is an inventory artifact, not a direct measurement of long-term reliability. "
            "No incident or recovery data source is connected."
        ),
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>HyoDo Instrument Panel</title><style>
:root {{ color-scheme: light dark; --ink:#182033; --muted:#5b6475; --surface:#fff; --bg:#f5f7fb; --line:#dbe1ed; --line-soft:#edf0f5; --focus:#111827; }}
@media (prefers-color-scheme: dark) {{ :root {{ --ink:#e6eaf3; --muted:#9aa3b5; --surface:#161b28; --bg:#0d1119; --line:#2a3245; --line-soft:#232a3b; --focus:#e6eaf3; }} }}
* {{ box-sizing:border-box }} body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.45 ui-sans-serif,system-ui,sans-serif }}
main {{ max-width:1180px; margin:auto; padding:28px 20px 48px }} header {{ display:flex; justify-content:space-between; gap:24px; align-items:start; margin-bottom:24px }}
h1 {{ margin:0; font-size:clamp(1.7rem,4vw,2.5rem) }} .meta {{ color:var(--muted); margin:.35rem 0 0 }} .legend {{ font-size:.9rem; color:var(--muted); text-align:right }}
.grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px }} .card {{ background:var(--surface); border:1px solid var(--line); border-top:7px solid var(--accent); border-radius:14px; padding:18px; min-height:210px; box-shadow:0 2px 9px #15244a0a }}
.blue {{ --accent:#2563eb }} .green {{ --accent:#059669 }} .purple {{ --accent:#7c3aed }} .orange {{ --accent:#ea580c }} .gold {{ --accent:#ca8a04 }} .indigo {{ --accent:#4f46e5 }}
h2 {{ margin:0 0 14px; font-size:1.1rem }} h2 span {{ color:var(--accent); font-size:.8rem; letter-spacing:.09em }} ul {{ list-style:none; padding:0; margin:0 }} li {{ display:grid; grid-template-columns:1fr auto; gap:5px 10px; padding:10px 0; border-top:1px solid var(--line-soft) }} li:first-child {{ border-top:0; padding-top:0 }} small,.reference {{ grid-column:1/-1; color:var(--muted); font-size:.82rem }} .reference {{ color:var(--accent) }} .not-measured {{ font-size:1.2rem; font-weight:700; margin:20px 0 4px }} .reason {{ color:var(--muted); margin:0 }}
*:focus-visible {{ outline:3px solid var(--focus); outline-offset:3px }} @media (prefers-reduced-motion:reduce) {{ * {{ scroll-behavior:auto }} }}
@media (max-width:820px) {{ header {{ display:block }} .legend {{ text-align:left; margin-top:10px }} .grid {{ grid-template-columns:1fr }} .card {{ min-height:0 }} }}
</style></head><body><main><header><div><h1>HyoDo Instrument Panel</h1><p class="meta">Target: {escape(target)} · Measured: {escape(measured_at)}</p></div><p class="legend">Raw evidence only · No composite score<br>Open the terminal output or JSON artifact for full evidence.</p></header><div class="grid">{jin}{seon}{mi}{in_card}{hyo}{yeong}</div></main><script data-measured="{escape(measured_at)}">{POLL_SCRIPT}</script></body></html>"""
