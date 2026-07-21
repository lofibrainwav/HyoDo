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
const statusNode = document.getElementById("measurement-status");
const measureButton = document.querySelector(".controls button");
setInterval(() => {
  // A failed poll means the server stopped; keep the last rendered snapshot.
  Promise.all([
    fetch("/api/evidence", { cache: "no-store" }).then((r) => r.json()),
    fetch("/api/status", { cache: "no-store" }).then((r) => r.json()),
  ])
    .then(([evidence, status]) => {
      if (statusNode) statusNode.textContent = status.message;
      if (measureButton) measureButton.disabled = status.refreshing;
      if (evidence.measured_at && evidence.measured_at !== seen) location.reload();
    })
    .catch(() => {});
}, 2000);"""

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


# Single source of truth for the six-pillar identity and card order:
# (key, Hanja, Korean, English, accent class). Headings are always trilingual.
PILLAR_SPECS: tuple[tuple[str, str, str, str, str], ...] = (
    ("jin", "眞", "진", "Truth", "blue"),
    ("seon", "善", "선", "Goodness", "green"),
    ("mi", "美", "미", "Beauty", "purple"),
    ("in", "仁", "인", "Benevolence", "orange"),
    ("hyo", "孝", "효", "Filial Piety", "gold"),
    ("yeong", "永", "영", "Eternity", "indigo"),
)


def _card(pillar: str, hanja: str, korean: str, english: str, color: str, body: str) -> str:
    return (
        f'<section class="card {escape(color)}" aria-labelledby="{escape(pillar)}">'
        f'<h2 id="{escape(pillar)}"><span lang="ko">{escape(hanja)} {escape(korean)}</span> '
        f"{escape(english)}</h2>{body}</section>"
    )


def _not_measured(reason: str) -> str:
    return f'<p class="not-measured">Not measured</p><p class="reason">{escape(reason)}</p>'


def _pillar_metrics(pillar: Any) -> tuple[dict[str, Any], str]:
    """Return (metrics, source label) for a pillar entry; empty means not measured."""
    if not isinstance(pillar, dict):
        return {}, ""
    metrics = pillar.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        return {}, ""
    sources = pillar.get("sources") or []
    return metrics, "; ".join(str(source) for source in sources)


def _coverage(pair: Any, done_key: str, total_key: str) -> str:
    if not isinstance(pair, dict):
        return "Not measured"
    done = int(pair.get(done_key, 0))
    total = int(pair.get(total_key, 0))
    percent = f"{done / total:.0%}" if total else "n/a"
    return f"{percent} ({done}/{total})"


def _in_body(pillar: Any) -> str:
    metrics, source = _pillar_metrics(pillar)
    if not metrics:
        return _not_measured(
            "No real UI task-completion events are connected to this HyoDo CLI checkout."
        )
    return (
        "<ul>"
        + _metric(
            "Public docstring coverage",
            _coverage(metrics.get("public_docstring_coverage"), "documented", "public"),
            source,
        )
        + _metric(
            "CLI parameters with help text",
            _coverage(metrics.get("cli_parameters_with_help"), "with_help", "total"),
            source,
        )
        + _metric("Message-less raises", str(metrics.get("messageless_raises", 0)), source, "0")
        + "</ul>"
    )


def _hyo_body(pillar: Any) -> str:
    metrics, source = _pillar_metrics(pillar)
    if not metrics:
        return _not_measured("No consent, undo, or data-protection event source is connected.")
    flags = metrics.get("mutating_flags")
    flags = flags if isinstance(flags, dict) else {}
    flag_list = ", ".join(flags.get("flags", [])) or "none found"
    defaulting_on = flags.get("defaulting_on", [])
    consent = "all opt-in" if not defaulting_on else "defaulting ON: " + ", ".join(defaulting_on)
    return (
        "<ul>"
        + _metric(f"Mutating flags ({flag_list})", consent, source)
        + _metric(
            "Outbound network import sites",
            str(metrics.get("outbound_network_import_sites", 0)),
            source,
            "0",
        )
        + _metric(
            "Non-loopback bind literals",
            str(metrics.get("non_loopback_bind_literals", 0)),
            source,
            "0",
        )
        + "</ul>"
    )


def _yeong_body(pillar: Any) -> str:
    metrics, source = _pillar_metrics(pillar)
    if not metrics:
        return _not_measured(
            "SBOM status is an inventory artifact, not a direct measurement of long-term "
            "reliability. No incident or recovery data source is connected."
        )
    corrupt = int(metrics.get("corrupt_lines", 0))
    corrupt_item = _metric("Corrupt ledger lines", str(corrupt), source, "0") if corrupt else ""
    all_pass_runs = int(metrics.get("all_pass_runs", 0))
    total_runs = int(metrics.get("recorded_runs", 0))
    pass_rate = (
        f"{all_pass_runs / total_runs:.0%} ({all_pass_runs}/{total_runs})" if total_runs else "n/a"
    )
    last_non_pass_at = str(metrics.get("last_non_pass_at", ""))
    last_non_pass_item = (
        _metric("Last non-PASS run", last_non_pass_at, source) if last_non_pass_at else ""
    )
    return (
        "<ul>"
        + _metric("Recorded measurement runs", str(metrics.get("recorded_runs", 0)), source)
        + _metric("All-PASS run rate", pass_rate, source)
        + _metric(
            "Consecutive all-PASS runs",
            str(metrics.get("consecutive_all_pass_runs", 0)),
            source,
        )
        + _metric("First recorded", str(metrics.get("first_recorded_at", "")), source)
        + _metric("Last recorded", str(metrics.get("last_recorded_at", "")), source)
        + last_non_pass_item
        + corrupt_item
        + "</ul>"
        + '<p class="reason">SBOM remains an inventory artifact, not a reliability '
        "measurement.</p>"
    )


def render_dashboard_html(
    evidence: dict[str, Any],
    *,
    refresh_token: str = "",
    interval: int = 0,
    refreshing: bool = False,
    refresh_message: str = "Snapshot ready.",
) -> str:
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

    pillars = evidence.get("pillars")
    pillars = pillars if isinstance(pillars, dict) else {}
    bodies = {
        "jin": (
            "<ul>"
            + _metric("Type check", f"{typecheck['status']}: {typecheck['message']}", "Pyright")
            + "</ul>"
        ),
        "seon": (
            "<ul>"
            + _metric("Tests", f"{tests['status']}: {_display_message(tests['message'])}", "pytest")
            + _metric("Safety risk", f"{risk}/100", "HyoDo safe", "0")
            + _metric("High-risk findings", str(high), "HyoDo safe", "0")
            + "</ul>"
        ),
        "mi": (
            "<ul>"
            + _metric("Lint and format", f"{lint['status']}: {lint['message']}", "Ruff")
            + "</ul>"
        ),
        "in": _in_body(pillars.get("in")),
        "hyo": _hyo_body(pillars.get("hyo")),
        "yeong": _yeong_body(pillars.get("yeong")),
    }
    cards = "".join(
        _card(key, hanja, korean, english, color, bodies[key])
        for key, hanja, korean, english, color in PILLAR_SPECS
    )
    refresh_mode = (
        f"Auto re-measure every {interval}s" if interval else "Snapshot fixed until measured again"
    )
    refresh_control = (
        '<form class="controls" method="post" action="/api/refresh">'
        + f'<input type="hidden" name="token" value="{escape(refresh_token)}">'
        + (
            '<button type="submit" disabled>Measurement running</button>'
            if refreshing
            else '<button type="submit">Measure again now</button>'
        )
        + "<small>Local only. Records one new history receipt and may take several minutes.</small>"
        + "</form>"
        if refresh_token
        else ""
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>HyoDo Instrument Panel</title><style>
:root {{ color-scheme: light dark; --ink:#182033; --muted:#5b6475; --surface:#fff; --bg:#f5f7fb; --line:#dbe1ed; --line-soft:#edf0f5; --focus:#111827; }}
@media (prefers-color-scheme: dark) {{ :root {{ --ink:#e6eaf3; --muted:#9aa3b5; --surface:#161b28; --bg:#0d1119; --line:#2a3245; --line-soft:#232a3b; --focus:#e6eaf3; }} }}
* {{ box-sizing:border-box }} body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.45 ui-sans-serif,system-ui,sans-serif }}
main {{ max-width:1180px; margin:auto; padding:28px 20px 48px }} header {{ display:flex; justify-content:space-between; gap:24px; align-items:start; margin-bottom:24px }}
h1 {{ margin:0; font-size:clamp(1.7rem,4vw,2.5rem) }} .meta {{ color:var(--muted); margin:.35rem 0 0 }} .legend {{ font-size:.9rem; color:var(--muted); text-align:right }} .legend a {{ color:inherit }} .controls {{ display:grid; gap:6px; margin:0 0 24px }} button {{ width:max-content; border:1px solid var(--accent,#2563eb); border-radius:8px; background:#2563eb; color:white; cursor:pointer; font:inherit; padding:9px 12px }} button:focus-visible {{ outline:3px solid var(--focus); outline-offset:3px }}
.grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px }} .card {{ background:var(--surface); border:1px solid var(--line); border-top:7px solid var(--accent); border-radius:14px; padding:18px; min-height:210px; box-shadow:0 2px 9px #15244a0a }}
.blue {{ --accent:#2563eb }} .green {{ --accent:#059669 }} .purple {{ --accent:#7c3aed }} .orange {{ --accent:#ea580c }} .gold {{ --accent:#ca8a04 }} .indigo {{ --accent:#4f46e5 }}
h2 {{ margin:0 0 14px; font-size:1.1rem }} h2 span {{ color:var(--accent); font-size:1rem; letter-spacing:.02em }} ul {{ list-style:none; padding:0; margin:0 }} li {{ display:grid; grid-template-columns:1fr auto; gap:5px 10px; padding:10px 0; border-top:1px solid var(--line-soft) }} li:first-child {{ border-top:0; padding-top:0 }} small,.reference {{ grid-column:1/-1; color:var(--muted); font-size:.82rem }} .reference {{ color:var(--accent) }} .not-measured {{ font-size:1.2rem; font-weight:700; margin:20px 0 4px }} .reason {{ color:var(--muted); margin:0 }}
*:focus-visible {{ outline:3px solid var(--focus); outline-offset:3px }} @media (prefers-reduced-motion:reduce) {{ * {{ scroll-behavior:auto }} }}
@media (max-width:820px) {{ header {{ display:block }} .legend {{ text-align:left; margin-top:10px }} .grid {{ grid-template-columns:1fr }} .card {{ min-height:0 }} }}
</style></head><body><main><header><div><h1>HyoDo Instrument Panel</h1><p class="meta">Target: {escape(target)} · Measured: {escape(measured_at)}</p></div><p class="legend">Raw evidence only · No composite score<br><a href="/api/evidence">Open current evidence JSON</a></p></header><p class="meta">{escape(refresh_mode)}</p><p id="measurement-status" class="meta" aria-live="polite">{escape(refresh_message)}</p>{refresh_control}<div class="grid">{cards}</div></main><script data-measured="{escape(measured_at)}">{POLL_SCRIPT}</script></body></html>"""
