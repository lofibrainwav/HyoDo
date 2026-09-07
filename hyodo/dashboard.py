"""Dependency-free local dashboard rendering for HyoDo measurement evidence."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from html import escape
from typing import Any

from hyodo.graph_view import (
    UNCLASSIFIED,
    assign_columns,
    build_actor_rows,
    column_coverage,
    orb_state,
)

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
      if (statusNode) {
        const startedAt = Date.parse(status.started_at || "");
        const elapsed = Number.isNaN(startedAt) ? 0 : Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
        statusNode.textContent = status.refreshing
          ? `Measurement running for ${elapsed}s. Gates can take several minutes.`
          : status.message;
      }
      if (measureButton) measureButton.disabled = status.refreshing;
      if (evidence.measured_at && evidence.measured_at !== seen) location.reload();
    })
    .catch(() => {});
}, 2000);"""

POLL_SCRIPT_SHA256 = base64.b64encode(hashlib.sha256(POLL_SCRIPT.encode("utf-8")).digest()).decode(
    "ascii"
)

# Inline keyboard-focus + detail-panel enhancement for the /graph page
# (spec section 10 rollout step (b): server-rendered MVP, shared TS renderer
# pending). Builds the panel with textContent/createElement, never innerHTML,
# because event fields (tool names, paths) come from the local ledger and a
# compromised agent could have written adversarial text into them. Escape
# clears the panel and returns focus to whichever cell last had it (or the
# first cell in the grid, if none has been focused yet), so the keyboard
# path never strands focus after the panel is dismissed.
GRAPH_SCRIPT = """\
const panel = document.getElementById("event-detail");
const DEFAULT_DETAIL = "Select an event to see its 5W1H detail.";
const FIELDS = [
  ["Who", "who"],
  ["What", "what"],
  ["When", "when"],
  ["Where", "where"],
  ["Why", "why"],
  ["How", "how"],
];
const cells = document.querySelectorAll(".cells button[data-event]");
let lastFocusedCell = null;
cells.forEach((button) => {
  const show = () => {
    lastFocusedCell = button;
    if (!panel) return;
    let data;
    try {
      data = JSON.parse(button.dataset.event);
    } catch (err) {
      return;
    }
    panel.textContent = "";
    for (const [label, key] of FIELDS) {
      const p = document.createElement("p");
      const strong = document.createElement("strong");
      strong.textContent = label + ": ";
      p.appendChild(strong);
      p.appendChild(document.createTextNode(String(data[key] ?? "not recorded")));
      panel.appendChild(p);
    }
  };
  button.addEventListener("focus", show);
  button.addEventListener("click", show);
});
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  if (panel) panel.textContent = DEFAULT_DETAIL;
  const target = lastFocusedCell || cells[0];
  if (target) target.focus();
});"""

GRAPH_SCRIPT_SHA256 = base64.b64encode(
    hashlib.sha256(GRAPH_SCRIPT.encode("utf-8")).digest()
).decode("ascii")


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

# PILLAR_SPECS colour name -> hex, kept byte-identical to the literal
# `.name {{ --accent:#hex }}` rules in the CSS block inside
# render_dashboard_html below. tests/test_virtue_colors_ssot.py parses that
# CSS block's literal text as the SSOT (not this dict), so this is a second,
# hand-kept-in-sync copy the graph viewer (render_graph_html) can look up by
# name without re-parsing CSS text.
_VIRTUE_ACCENT_HEX: dict[str, str] = {
    "blue": "#2563eb",
    "green": "#059669",
    "purple": "#7c3aed",
    "orange": "#ea580c",
    "gold": "#ca8a04",
    "indigo": "#4f46e5",
}

# hyodo/dashboard.py had no existing ALLOW/ASK/DENY/UNOBSERVED colours to
# reuse, so this PR defines them once here (per the implementer brief).
# Deliberately distinct from every _VIRTUE_ACCENT_HEX value above so a
# decision pill is never mistaken for a virtue column. The public site
# prototype's `site/src/styles/tokens.css` defines analogous
# --color-ask/-deny/-tile-observed tokens for its own renderer — out of
# scope for this PR (design spec section 8's shared-renderer packaging).
DECISION_COLORS: dict[str, str] = {
    "ALLOW": "#16a34a",
    "ASK": "#0ea5e9",
    "DENY": "#dc2626",
    "UNOBSERVED": "#6b7280",
}


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
    skipped_runs = int(metrics.get("runs_with_skipped_gates", 0))
    skipped_item = (
        _metric("Runs with skipped (unmeasured) gates", str(skipped_runs), source)
        if skipped_runs
        else ""
    )
    return (
        "<ul>"
        + _metric("Recorded measurement runs", str(metrics.get("recorded_runs", 0)), source)
        + _metric("All-PASS run rate (executed gates)", pass_rate, source)
        + _metric(
            "Consecutive all-PASS runs",
            str(metrics.get("consecutive_all_pass_runs", 0)),
            source,
        )
        + skipped_item
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
    refresh_started_at: str = "",
) -> str:
    """Render raw evidence without creating a composite score or fake values."""
    typecheck = _gate(evidence, "typecheck")
    tests = _gate(evidence, "tests")
    lint = _gate(evidence, "lint_format")
    safety = evidence.get("safety", {})
    risk = safety.get("risk_score")
    risk_display = f"{risk}/100" if isinstance(risk, int | float) else "Not measured"
    safety_source = str(safety.get("source", "Not recorded"))
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
            + _metric("Change safety risk", risk_display, "HyoDo safe", "0")
            + _metric("Safety scan scope", safety_source, "HyoDo safe")
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
    refresh_status = refresh_message
    if refreshing and refresh_started_at:
        refresh_status = (
            f"Measurement running since {refresh_started_at}. Gates can take several minutes."
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
</style></head><body><main><header><div><h1>HyoDo Instrument Panel</h1><p class="meta">Target: {escape(target)} · Measured: {escape(measured_at)}</p></div><p class="legend">Raw evidence only · No composite score<br><a href="/graph">Open evidence graph</a> · <a href="/api/evidence">Open current evidence JSON</a></p></header><p class="meta">{escape(refresh_mode)}</p><p id="measurement-status" class="meta" aria-live="polite">{escape(refresh_status)}</p>{refresh_control}<div class="grid">{cards}</div></main><script data-measured="{escape(measured_at)}">{POLL_SCRIPT}</script></body></html>"""


def _parse_iso_ts(value: Any) -> datetime | None:
    """Parse a schema `ts` string leniently; ``None`` when absent/unparseable."""
    if not isinstance(value, str) or not value:
        return None
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _event_label(node: dict[str, Any]) -> str:
    """Short visible label for one node's cell button; accessible name = this text."""
    tool = node.get("tool") if isinstance(node.get("tool"), dict) else {}
    name = tool.get("name") if isinstance(tool, dict) else None
    kind = str(node.get("kind") or "event")
    return f"{kind}: {name}" if isinstance(name, str) and name else kind


def _event_detail_payload(node: dict[str, Any]) -> dict[str, str]:
    """5W1H fields for the detail panel (spec section 3's event fields only)."""
    raw_tool = node.get("tool")
    tool: dict[str, Any] = raw_tool if isinstance(raw_tool, dict) else {}
    raw_policy = node.get("policy")
    policy: dict[str, Any] = raw_policy if isinstance(raw_policy, dict) else {}
    raw_paths = tool.get("paths")
    raw_urls = tool.get("urls")
    paths: list[Any] = raw_paths if isinstance(raw_paths, list) else []
    urls: list[Any] = raw_urls if isinstance(raw_urls, list) else []
    domains = [
        str(entry.get("domain"))
        for entry in urls
        if isinstance(entry, dict) and entry.get("domain")
    ]
    where = ", ".join([*(str(p) for p in paths), *domains]) or "not recorded"
    rule_id = policy.get("rule_id") if isinstance(policy, dict) else None
    decision = node.get("decision")
    how = str(decision) if decision else "not recorded"
    if rule_id:
        how = f"{how} ({rule_id})"
    return {
        "who": str(node.get("actor") or "not recorded"),
        "what": _event_label(node),
        "when": str(node.get("ts") or "not recorded"),
        "where": where,
        "why": str(policy.get("reason"))
        if isinstance(policy, dict) and policy.get("reason")
        else "not recorded",
        "how": how,
    }


def _event_button(node: dict[str, Any]) -> str:
    label = _event_label(node)
    detail = escape(json.dumps(_event_detail_payload(node)), quote=True)
    node_id = escape(str(node.get("id") or ""))
    decision = node.get("decision")
    cell_class = (
        f"cell-{str(decision).lower()}" if isinstance(decision, str) and decision else "cell-plain"
    )
    return (
        f'<button type="button" class="{cell_class}" data-event-id="{node_id}" '
        f'data-event="{detail}">{escape(label)}</button>'
    )


def _render_actor_rows(
    rows_tree: dict[str, Any],
    node_by_id: dict[str, dict[str, Any]],
) -> str:
    """Render collapsible actor rows (spec section 2) from `build_actor_rows`."""
    rows = rows_tree.get("rows", {})
    order = rows_tree.get("order", [])
    children: dict[str | None, list[str]] = {}
    for key in order:
        parent = rows[key].get("parent_row")
        children.setdefault(parent, []).append(key)

    def _render_row(key: str) -> str:
        """Render one row (and its nested sub-agent rows) as HTML."""
        row = rows[key]
        label = str(row.get("label", key))
        cells = "".join(
            _event_button(node_by_id[node_id])
            for node_id in row.get("events", [])
            if node_id in node_by_id
        )
        nested = "".join(_render_row(child_key) for child_key in children.get(key, []))
        if nested:
            return (
                f'<details class="row" open><summary>{escape(label)}</summary>'
                f'<div class="row-cells">{cells}</div>{nested}</details>'
            )
        return (
            f'<div class="row"><h3>{escape(label)}</h3><div class="row-cells">{cells}</div></div>'
        )

    return "".join(_render_row(key) for key in children.get(None, []))


def render_graph_html(graph: dict[str, Any], *, now: datetime | None = None) -> str:
    """Render the local evidence-graph viewer.

    Rollout step (b)
    (`docs/superpowers/specs/2026-09-06-hyodo-core-engine-monitor-design.md`,
    sections 2-4, 9-10): the five fixed virtue columns in spec order, the
    orb, actor rows with collapsible sub-agent nesting, an unclassified
    gutter, and a 5W1H detail panel. `graph` is a full
    `hyodo.evidence-graph/v1` dict (`hyodo.report.build_report_graph`).

    Ruling for this PR (spec section 8): the shared TypeScript renderer
    needs a build-and-package step for the wheel that is a separate
    infrastructure change, so this renders server-side in Python with a
    small inline vanilla-JS enhancement (keyboard focus + detail panel).
    Step (b) shipped server-rendered; renderer sharing is pending.
    """
    now = now or datetime.now(timezone.utc)
    status = str(graph.get("status") or "UNOBSERVED")
    reason = graph.get("reason")
    raw_nodes = graph.get("nodes")
    raw_edges = graph.get("edges")
    nodes: list[dict[str, Any]] = raw_nodes if isinstance(raw_nodes, list) else []
    edges: list[dict[str, Any]] = raw_edges if isinstance(raw_edges, list) else []
    missions = graph.get("missions") if isinstance(graph.get("missions"), dict) else {}
    node_by_id: dict[str, dict[str, Any]] = {
        node["id"]: node for node in nodes if isinstance(node.get("id"), str)
    }

    assignments = {node_id: assign_columns(node) for node_id, node in node_by_id.items()}
    coverage = column_coverage(nodes, assignments, edges)
    orb = orb_state(graph)
    rows_tree = build_actor_rows(nodes, edges)

    notice_html = ""
    if status != "READY":
        reason_text = f" — {escape(str(reason))}" if reason else ""
        notice_html = (
            '<p class="unobserved-notice" role="status">UNOBSERVED'
            + reason_text
            + ": the graph area reflects what could be measured, not a clean run.</p>"
        )

    has_mission = bool(missions) and any(mission for mission in missions.values())
    mission_note = (
        '<p class="column-note">No mission observed for this run — every event is unattributed.</p>'
        if nodes and not has_mission
        else ""
    )

    column_sections: list[str] = []
    for key, hanja, korean, english, color in PILLAR_SPECS[:5]:
        cov = coverage.get(key, {"observed": 0, "expected": 0})
        cell_ids = [node_id for node_id, columns in assignments.items() if key in columns]
        cells_html = "".join(_event_button(node_by_id[node_id]) for node_id in cell_ids)
        note = mission_note if key == "hyo" else ""
        column_sections.append(
            f'<section class="column" aria-labelledby="col-{escape(key)}">'
            f'<h2 id="col-{escape(key)}" style="--accent:{_VIRTUE_ACCENT_HEX[color]}">'
            f'<span lang="ko">{escape(hanja)} {escape(korean)}</span> {escape(english)}</h2>'
            f'<p class="coverage">{cov["observed"]}/{cov["expected"]} observed</p>'
            f"{note}"
            f'<div class="cells">{cells_html}</div>'
            "</section>"
        )
    columns_html = "".join(column_sections)

    unclassified_ids = [
        node_id for node_id, columns in assignments.items() if columns == [UNCLASSIFIED]
    ]
    gutter_html = ""
    if unclassified_ids:
        gutter_cells = "".join(_event_button(node_by_id[node_id]) for node_id in unclassified_ids)
        gutter_html = (
            '<section class="gutter" aria-label="Unclassified events">'
            "<h2>Unclassified</h2>"
            f'<div class="cells">{gutter_cells}</div>'
            "</section>"
        )

    rows_html = _render_actor_rows(rows_tree, node_by_id)

    latest_ts = _parse_iso_ts(orb.get("latest_ts"))
    pulse_eligible = latest_ts is not None and (now - latest_ts).total_seconds() < 60
    orb_decision = str(orb.get("decision") or "UNOBSERVED")
    orb_cov = orb.get("coverage") or {"observed": 0, "expected": 0}
    ratio = orb_cov["observed"] / orb_cov["expected"] if orb_cov["expected"] else 0.0
    brightness = 0.25 + 0.75 * min(max(ratio, 0.0), 1.0)
    orb_classes = "orb orb-" + orb_decision.lower() + (" orb-pulse" if pulse_eligible else "")
    orb_color = DECISION_COLORS.get(orb_decision, DECISION_COLORS["UNOBSERVED"])
    # The orb caption's total is the sum of the five column badges below —
    # never a new number — so the breakdown line spells out those exact
    # addends next to the total, per column, in the same fixed order.
    breakdown = " · ".join(
        f"{english} {coverage.get(key, {'observed': 0, 'expected': 0})['observed']}/"
        f"{coverage.get(key, {'observed': 0, 'expected': 0})['expected']}"
        for key, _hanja, _korean, english, _color in PILLAR_SPECS[:5]
    )
    orb_html = (
        f'<div class="{orb_classes}" role="img" '
        f'aria-label="Core engine pulse: latest decision {escape(orb_decision)}, '
        f'{orb_cov["observed"]}/{orb_cov["expected"]} observed" '
        f'style="--decision-color:{orb_color}; --brightness:{brightness:.3f}"></div>'
        f'<p class="orb-caption" title="{escape(breakdown)}">{escape(orb_decision)} · '
        f"{orb_cov['observed']}/{orb_cov['expected']} observed"
        + (" · recent activity" if pulse_eligible else "")
        + "</p>"
        f'<p class="orb-breakdown">{escape(breakdown)}</p>'
    )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>HyoDo Evidence Graph</title><style>
:root {{ color-scheme: light dark; --ink:#182033; --muted:#5b6475; --surface:#fff; --bg:#f5f7fb; --line:#dbe1ed; --line-soft:#edf0f5; --focus:#111827; }}
@media (prefers-color-scheme: dark) {{ :root {{ --ink:#e6eaf3; --muted:#9aa3b5; --surface:#161b28; --bg:#0d1119; --line:#2a3245; --line-soft:#232a3b; --focus:#e6eaf3; }} }}
* {{ box-sizing:border-box }} body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.45 ui-sans-serif,system-ui,sans-serif }}
main {{ max-width:1180px; margin:auto; padding:28px 20px 48px }} h1 {{ margin:0; font-size:clamp(1.5rem,4vw,2.2rem) }} .meta {{ color:var(--muted); margin:.35rem 0 0 }} .meta a {{ color:inherit }}
.unobserved-notice {{ background:#fdeaea; color:#7a1f1f; border:1px solid #f0b8b8; border-radius:10px; padding:10px 14px; font-weight:600; margin:18px 0 }}
@media (prefers-color-scheme: dark) {{ .unobserved-notice {{ background:#3f2626; color:#f5c9c9; border-color:#7a3b3b }} }}
.orb-wrap {{ display:flex; flex-direction:column; align-items:center; gap:6px; margin:22px 0 28px }}
.orb {{ width:72px; height:72px; border-radius:50%; background:var(--decision-color,#6b7280); opacity:var(--brightness,0.4); box-shadow:0 0 24px var(--decision-color,#6b7280) }}
.orb-pulse {{ animation:hyodo-orb-pulse 2.4s ease-in-out infinite }}
@keyframes hyodo-orb-pulse {{ 0%,100% {{ transform:scale(1) }} 50% {{ transform:scale(1.14) }} }}
@media (prefers-reduced-motion:reduce) {{ .orb-pulse {{ animation:none }} }}
.orb-caption {{ color:var(--muted); font-size:.9rem; margin:0 }}
.orb-breakdown {{ color:var(--muted); font-size:.78rem; margin:.2rem 0 0; text-align:center }}
.columns {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:14px; margin-bottom:18px }}
.column {{ background:var(--surface); border:1px solid var(--line); border-top:6px solid var(--accent,#888); border-radius:12px; padding:12px; min-height:120px }}
.column h2 {{ margin:0 0 4px; font-size:.95rem }} .column h2 span {{ color:var(--accent); font-size:.85rem }}
.coverage {{ margin:0 0 8px; color:var(--muted); font-size:.85rem }} .column-note {{ font-size:.8rem; color:var(--muted) }}
.cells, .row-cells {{ display:flex; flex-wrap:wrap; gap:6px }}
.gutter {{ margin-bottom:18px }} .gutter h2 {{ font-size:.95rem }}
.rows .row {{ border-top:1px solid var(--line-soft); padding:10px 0 }} .rows details.row > summary {{ cursor:pointer; font-weight:600 }} .rows h3 {{ margin:0 0 6px; font-size:.95rem }}
button {{ font:inherit; border:1px solid var(--line); background:var(--surface); color:var(--ink); border-radius:8px; padding:6px 9px; cursor:pointer }}
*:focus-visible {{ outline:3px solid var(--focus); outline-offset:2px }}
.cell-deny {{ border-color:{DECISION_COLORS["DENY"]} }} .cell-ask {{ border-color:{DECISION_COLORS["ASK"]} }} .cell-allow {{ border-color:{DECISION_COLORS["ALLOW"]} }} .cell-unobserved {{ border-color:{DECISION_COLORS["UNOBSERVED"]} }}
.detail {{ margin-top:20px; border:1px solid var(--line); border-radius:12px; padding:14px; background:var(--surface); min-height:80px }} .detail p {{ margin:.25rem 0 }}
@media (max-width:900px) {{ .columns {{ grid-template-columns:1fr 1fr }} }}
</style></head><body><main><header><div><h1>HyoDo Evidence Graph</h1><p class="meta">Local only · No composite score · <a href="/">Back to instrument panel</a></p></div></header>
{notice_html}
<section class="orb-wrap">{orb_html}</section>
<div class="columns">{columns_html}</div>
{gutter_html}
<div class="rows">{rows_html}</div>
<section id="event-detail" class="detail" aria-live="polite"><p>Select an event to see its 5W1H detail.</p></section>
</main><script>{GRAPH_SCRIPT}</script></body></html>"""
