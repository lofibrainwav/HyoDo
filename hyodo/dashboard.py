"""Dependency-free local dashboard rendering for HyoDo measurement evidence."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

from hyodo.audience import resolve_audience
from hyodo.graph_view import (
    UNCLASSIFIED,
    VIRTUE_COLUMNS,
    assign_columns,
    build_actor_rings,
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
#
# Fix round 2 (coordinator, live-screenshot review): `layoutEdges()` is
# also responsible for the edge overlay's actual geometry.
# `hyodo/dashboard.py`'s `_render_edge_overlay` renders each edge as a
# `<path data-source data-target data-kind="parent|evidence|broken"
# d="">` with an empty `d` — only the browser, after real layout (which
# depends on tile text length, wrapped actor labels, and other things the
# server cannot predict), knows where a tile's edges actually are.
# `layoutEdges()` measures every tile with `getBoundingClientRect()`
# relative to the `.grid-rows` container and fills `d` in: cross-column
# anchors at source right-middle/target left-middle (mirrored when the
# target sits to the left) with one bend at the midpoint x; same-column
# anchors at bottom-middle/top-middle; an evidence edge draws the same
# anchor pair as one quadratic curve; a broken edge draws a fixed 24px
# stub from its one anchor. It reruns on load, on resize, and after a row
# collapse toggle (row visibility changes what is measurable).
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
const cells = document.querySelectorAll(".cells button[data-event], .grid-cell button[data-event], .daw-cell button[data-event]");
let lastFocusedCell = null;
function highlightEdges(eventId) {
  document.querySelectorAll("#daw-edge-overlay .edge, #edge-overlay .edge").forEach((edge) => {
    const source = edge.dataset.dawSource || edge.dataset.source;
    const target = edge.dataset.dawTarget || edge.dataset.target;
    const active = eventId && (source === eventId || target === eventId);
    edge.classList.toggle("edge-active", Boolean(active));
  });
}
function layoutEdges() {
  const svg = document.getElementById("edge-overlay");
  const container = document.querySelector(".daw-rows, .grid-rows");
  if (!svg || !container) return;
  const containerRect = container.getBoundingClientRect();
  const tiles = new Map();
  container.querySelectorAll("button[data-event-id]").forEach((el) => {
    if (el.offsetParent === null) return;
    const r = el.getBoundingClientRect();
    tiles.set(el.dataset.eventId, {
      left: r.left - containerRect.left,
      right: r.right - containerRect.left,
      top: r.top - containerRect.top,
      bottom: r.bottom - containerRect.top,
      midX: (r.left + r.right) / 2 - containerRect.left,
      midY: (r.top + r.bottom) / 2 - containerRect.top,
    });
  });
  svg.querySelectorAll("path[data-source], path[data-daw-source]").forEach((path) => {
    const kind = path.dataset.kind;
    const sourceId = path.dataset.dawSource || path.dataset.source;
    const targetId = path.dataset.dawTarget || path.dataset.target;
    const source = tiles.get(sourceId);
    if (!source) {
      path.setAttribute("d", "");
      return;
    }
    if (kind === "broken") {
      const x1 = source.midX;
      const y1 = source.midY;
      path.setAttribute("d", "M" + x1 + "," + y1 + " L" + (x1 + 24) + "," + y1);
      return;
    }
    const target = tiles.get(targetId);
    if (!target) {
      path.setAttribute("d", "");
      return;
    }
    let x1, y1, x2, y2;
    if (Math.abs(source.midX - target.midX) < 1) {
      const goingDown = target.midY >= source.midY;
      x1 = source.midX;
      y1 = goingDown ? source.bottom : source.top;
      x2 = target.midX;
      y2 = goingDown ? target.top : target.bottom;
    } else {
      const goingRight = target.midX >= source.midX;
      x1 = goingRight ? source.right : source.left;
      y1 = source.midY;
      x2 = goingRight ? target.left : target.right;
      y2 = target.midY;
    }
    const midX = (x1 + x2) / 2;
    if (kind === "evidence") {
      const midY = (y1 + y2) / 2 - 18;
      path.setAttribute("d", "M" + x1 + "," + y1 + " Q" + midX + "," + midY + " " + x2 + "," + y2);
    } else {
      path.setAttribute(
        "d",
        "M" + x1 + "," + y1 + " L" + midX + "," + y1 + " L" + midX + "," + y2 + " L" + x2 + "," + y2
      );
    }
  });
}
cells.forEach((button) => {
  const show = () => {
    lastFocusedCell = button;
    highlightEdges(button.dataset.eventId || null);
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
const rowToggles = document.querySelectorAll(".row-toggle[data-row-toggle]");
function descendantRows(key) {
  const allRows = Array.from(document.querySelectorAll(".grid-row[data-row-key]"));
  const result = [];
  const stack = [key];
  while (stack.length) {
    const current = stack.pop();
    allRows.forEach((row) => {
      if (row.dataset.parentRow === current) {
        result.push(row);
        stack.push(row.dataset.rowKey);
      }
    });
  }
  return result;
}
rowToggles.forEach((button) => {
  button.addEventListener("click", () => {
    const key = button.dataset.rowToggle;
    const expanded = button.getAttribute("aria-expanded") !== "false";
    const next = !expanded;
    button.setAttribute("aria-expanded", String(next));
    button.textContent = next ? "-" : "+";
    descendantRows(key).forEach((row) => {
      row.hidden = !next;
    });
    layoutEdges();
  });
});
const ringButtons = document.querySelectorAll(".actor-label[data-actor-key]");
let lastRingButton = null;
function closeRingPanels() {
  document.querySelectorAll(".actor-rings").forEach((p) => {
    p.hidden = true;
  });
  ringButtons.forEach((b) => b.setAttribute("aria-expanded", "false"));
}
ringButtons.forEach((button) => {
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const key = button.dataset.actorKey;
    const target = document.getElementById("rings-" + key);
    if (!target) return;
    const wasOpen = !target.hidden;
    closeRingPanels();
    if (!wasOpen) {
      target.hidden = false;
      button.setAttribute("aria-expanded", "true");
      lastRingButton = button;
    } else {
      lastRingButton = null;
    }
  });
});
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  if (panel) panel.textContent = DEFAULT_DETAIL;
  highlightEdges(null);
  const target = lastFocusedCell || cells[0];
  if (target) target.focus();
  closeRingPanels();
  if (lastRingButton) lastRingButton.focus();
});
layoutEdges();
window.addEventListener("load", layoutEdges);
window.addEventListener("resize", layoutEdges);"""

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


def _status_line(status: str, message: str) -> str:
    """`"STATUS: message"`, or bare `"STATUS"` when *message* is empty.

    A gate that ran but produced no message text (e.g. NOT MEASURED with
    nothing further to say) must never render as `"NOT MEASURED: "` with a
    trailing colon and nothing after it.
    """
    return f"{status}: {message}" if message else status


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

# Package 2-C, Ruling 5 (colour SSOT): the four actor-ring layer colours,
# taken verbatim from `site/src/styles/tokens.css`'s `--color-ring-*`
# custom properties. `tests/test_virtue_colors_ssot.py` guards this dict
# the same way it already guards `_VIRTUE_ACCENT_HEX` above. Reading order
# (spec section 5, inward to outward): skills, memory, routines, tools;
# rendered outer-to-inner in `_render_actor_ring_panel` below.
RING_COLORS: dict[str, str] = {
    "skills": "#14b8a6",
    "memory": "#d946ef",
    "routines": "#84cc16",
    "tools": "#64748b",
}

# Local viewer second pass, brief finding 2: the SVG edge overlay's three
# line kinds. No `--color-edge-*` token existed in `site/src/styles/
# tokens.css` before this PR added it there; `tests/test_virtue_colors_ssot.py`
# guards this dict the same way it already guards `RING_COLORS` above.
EDGE_COLORS: dict[str, str] = {
    "parent": "#64748b",
    "evidence": "#0ea5e9",
    "broken": "#ff5c5c",
}

# Grid layout constants (brief finding 1): the SVG edge overlay
# (`_render_edge_overlay`) and the CSS grid it sits on top of share these
# same numbers, so a tile's schematic SVG anchor lines up with its actual
# `.grid-cell` position. Not measured pixels (the shared TypeScript
# renderer, spec section 8, is the pending home for that); a row-label
# column plus five equal virtue columns, each wide enough for a handful of
# fixed-width tiles before a cell's own horizontal scrollbar takes over.
GRID_LABEL_WIDTH = 180
GRID_COLUMN_WIDTH = 200
GRID_ROW_HEIGHT = 44
GRID_TILE_WIDTH = 76
GRID_TILE_GAP = 6
GRID_TILE_PAD = 8

#: The orb's pixel-grid pulse (brief finding 5): a fixed 9x9 field, ported
#: from the site hero's unlit-tile-field idea (`site/src/hero/scene.ts`) in
#: plain CSS/SVG rather than three.js/WebGPU.
ORB_GRID_SIZE = 9
ORB_GRID_TOTAL = ORB_GRID_SIZE * ORB_GRID_SIZE

#: Slow default pulse period, and the shortened period used when the
#: latest event is under 60s old (brief finding 5) — both in CSS seconds.
ORB_PULSE_PERIOD_IDLE = 4.0
ORB_PULSE_PERIOD_RECENT = 1.4

#: Brief finding 6: one fixed-wording open question per virtue column,
#: shown only when that column has zero events (`expected == 0`).
#: `engineer` is always present and is the fallback for a profile this
#: table has no entry for; `vibe`/`professional` reuse the wording
#: `hyodo.verdict`'s own profile tables already establish for the same
#: three-profile split (`hyodo.audience.VALID_PROFILES`).
_COLUMN_QUESTIONS: dict[str, dict[str, str]] = {
    "jin": {
        "engineer": "Which test run proves this change?",
        "vibe": "What proof do we have that this actually works?",
        "professional": "Which test evidence supports this control?",
    },
    "seon": {
        "engineer": "Which policy decision governed this action?",
        "vibe": "What kept this safe?",
        "professional": "Which control decision authorizes this action?",
    },
    "mi": {
        "engineer": "What confirms the output was reviewed for clarity?",
        "vibe": "Did anyone actually look at the result?",
        "professional": "What review evidence exists for this output?",
    },
    "in": {
        "engineer": "What shows this serves the people using it?",
        "vibe": "Who does this actually help?",
        "professional": "What documented benefit exists for the end user?",
    },
    "hyo": {
        "engineer": "What ties this event back to the original request?",
        "vibe": "Does this trace back to what was actually asked?",
        "professional": "What lineage evidence connects this to the engagement scope?",
    },
}

#: Full pillar name (`hyodo.skills.PILLARS`) -> `_VIRTUE_ACCENT_HEX` colour
#: name, so a skill's dominant-pillar tint reuses the already-guarded
#: virtue hex values rather than introducing a third copy.
_PILLAR_FULLNAME_TO_ACCENT: dict[str, str] = {
    "truth": "blue",
    "goodness": "green",
    "beauty": "purple",
    "benevolence": "orange",
    "hyo": "gold",
    "eternity": "indigo",
}

#: Fixed pillar order for dominant-pillar tie-breaking (matches
#: `hyodo.skills.PILLARS`).
_PILLAR_FULLNAME_ORDER: tuple[str, ...] = (
    "truth",
    "goodness",
    "beauty",
    "benevolence",
    "hyo",
    "eternity",
)

#: A skill with no observed pillar count at all (every slot zero) has no
#: dominant pillar; this muted grey — distinct from every virtue/decision
#: hex above — marks that case rather than picking pillar order's first
#: entry by default.
_NO_DOMINANT_PILLAR_HEX = "#9aa3b5"


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
    # Counts only - no percentages anywhere in HyoDo output.
    pass_rate = f"{all_pass_runs}/{total_runs} runs all-PASS" if total_runs else "n/a"
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
    gate_values = (typecheck, tests, lint)
    measured_gate_count = sum(
        1 for gate in gate_values if gate["status"].upper() not in {"NOT MEASURED", "UNOBSERVED"}
    )

    pillars = evidence.get("pillars")
    pillars = pillars if isinstance(pillars, dict) else {}
    bodies = {
        "jin": (
            "<ul>"
            + _metric(
                "Type check", _status_line(typecheck["status"], typecheck["message"]), "Pyright"
            )
            + "</ul>"
        ),
        "seon": (
            "<ul>"
            + _metric(
                "Tests", _status_line(tests["status"], _display_message(tests["message"])), "pytest"
            )
            + _metric("Change safety risk", risk_display, "HyoDo safe", "0")
            + _metric("Safety scan scope", safety_source, "HyoDo safe")
            + _metric("High-risk findings", str(high), "HyoDo safe", "0")
            + "</ul>"
        ),
        "mi": (
            "<ul>"
            + _metric("Lint and format", _status_line(lint["status"], lint["message"]), "Ruff")
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
:root {{ color-scheme: light dark; --ink:#121212; --muted:#68645d; --surface:#fffdf7; --bg:#ebe9e1; --line:#121212; --line-soft:#d8d5cc; --focus:#ff5a36; --signal:#ff5a36; --mono:"SFMono-Regular",Consolas,"Liberation Mono",monospace; }}
@media (prefers-color-scheme: dark) {{ :root {{ --ink:#f5f1e7; --muted:#aaa59a; --surface:#1d1d1a; --bg:#11110f; --line:#f5f1e7; --line-soft:#46443e; --focus:#ff7153; --signal:#ff7153; }} }}
* {{ box-sizing:border-box }} body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.45 "Helvetica Neue",Helvetica,Arial,sans-serif }}
main {{ max-width:1220px; margin:auto; padding:24px 22px 56px }}
header {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:28px; align-items:end; padding:0 0 20px; border-bottom:2px solid var(--line) }}
.eyebrow,.kicker,.readout-label,.status-label {{ font:700 .7rem/1.2 var(--mono); letter-spacing:.12em; text-transform:uppercase }}
.eyebrow {{ color:var(--signal); margin:0 0 8px }} h1 {{ margin:0; font-size:clamp(2.1rem,6vw,4.8rem); line-height:.92; letter-spacing:-.075em; font-weight:800 }}
.meta {{ color:var(--muted); margin:.6rem 0 0; font-family:var(--mono); font-size:.78rem; overflow-wrap:anywhere }}
.legend {{ max-width:260px; margin:0; color:var(--muted); font:700 .72rem/1.5 var(--mono); text-align:right; text-transform:uppercase }} .legend a {{ color:var(--ink); text-decoration-thickness:2px; text-underline-offset:3px }}
.instrument-strip {{ display:grid; grid-template-columns:1.5fr repeat(3,1fr); border-bottom:1px solid var(--line); margin:0 0 18px }}
.readout {{ min-height:96px; padding:14px 15px 12px; border-left:1px solid var(--line) }} .readout:first-child {{ border-left:0 }}
.readout-label {{ color:var(--muted); display:block; margin-bottom:11px }} .readout-value {{ display:block; font:800 clamp(1.05rem,2vw,1.5rem)/1 var(--mono); letter-spacing:-.06em; overflow-wrap:anywhere }} .readout-value.signal {{ color:var(--signal) }}
.controls {{ display:flex; flex-wrap:wrap; gap:10px 16px; align-items:center; padding:12px 0 18px; border-bottom:1px solid var(--line) }}
button {{ border:2px solid var(--line); border-radius:0; background:var(--signal); color:#121212; cursor:pointer; font:800 .78rem var(--mono); padding:10px 14px; text-transform:uppercase }} button:disabled {{ cursor:wait; opacity:.55 }} .controls small {{ color:var(--muted); font: .72rem var(--mono) }}
.measurement-status {{ display:inline-block; color:var(--ink); font:700 .72rem var(--mono); text-transform:uppercase }}
.grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; padding-top:18px }} .card {{ position:relative; background:var(--surface); border:2px solid var(--line); border-radius:0; padding:18px; min-height:218px; box-shadow:4px 4px 0 var(--line) }}
.card::before {{ content:""; position:absolute; top:0; left:0; width:28px; height:6px; background:var(--accent) }}
.blue {{ --accent:#2563eb }} .green {{ --accent:#059669 }} .purple {{ --accent:#7c3aed }} .orange {{ --accent:#ea580c }} .gold {{ --accent:#ca8a04 }} .indigo {{ --accent:#4f46e5 }}
h2 {{ display:flex; justify-content:space-between; gap:12px; align-items:baseline; margin:0 0 18px; font-size:1rem; letter-spacing:-.02em }} h2 span {{ color:var(--accent); font:800 .82rem var(--mono); letter-spacing:.08em }}
ul {{ list-style:none; padding:0; margin:0 }} li {{ display:grid; grid-template-columns:1fr auto; gap:5px 10px; padding:10px 0; border-top:1px solid var(--line-soft) }} li:first-child {{ border-top:0; padding-top:0 }} li strong {{ font:800 .86rem var(--mono); text-align:right; overflow-wrap:anywhere }} .metric-label {{ font-size:.84rem }} small,.reference {{ grid-column:1/-1; color:var(--muted); font: .68rem/1.35 var(--mono) }} .reference {{ color:var(--accent) }} .not-measured {{ font-size:1.2rem; font-weight:800; margin:20px 0 4px }} .reason {{ color:var(--muted); margin:0; font-size:.8rem }}
*:focus-visible {{ outline:3px solid var(--focus); outline-offset:3px }} @media (prefers-reduced-motion:reduce) {{ * {{ scroll-behavior:auto }} }}
@media (max-width:820px) {{ main {{ padding:18px 14px 40px }} header {{ display:block }} .legend {{ text-align:left; margin-top:18px; max-width:none }} .instrument-strip {{ grid-template-columns:1fr 1fr }} .readout {{ border-top:1px solid var(--line); border-left:1px solid var(--line) }} .readout:nth-child(odd) {{ border-left:0 }} .grid {{ grid-template-columns:1fr }} .card {{ min-height:0 }} }}
</style></head><body><main><header><div><p class="eyebrow">HyoDo / Measurement Console</p><h1>Instrument Panel</h1><p class="meta">TARGET // {escape(target)}<br>MEASURED // {escape(measured_at)}</p></div><p class="legend">Raw evidence only<br>No composite score<br><a href="/graph">Open evidence graph</a> · <a href="/api/evidence">Open evidence JSON</a></p></header><section class="instrument-strip" aria-label="measurement summary"><div class="readout"><span class="readout-label">Signal state</span><strong class="readout-value signal">{escape("MEASURED" if measured_gate_count else "UNOBSERVED")}</strong></div><div class="readout"><span class="readout-label">Gates read</span><strong class="readout-value">{measured_gate_count}/3</strong></div><div class="readout"><span class="readout-label">Refresh mode</span><strong class="readout-value">{escape("AUTO " + str(interval) + "S" if interval else "FIXED")}</strong></div><div class="readout"><span class="readout-label">Receipt scope</span><strong class="readout-value">LOCAL ONLY</strong></div></section><p class="meta">{escape(refresh_mode)}</p><p id="measurement-status" class="measurement-status" aria-live="polite">{escape(refresh_status)}</p>{refresh_control}<div class="grid">{cards}</div></main><script data-measured="{escape(measured_at)}">{POLL_SCRIPT}</script></body></html>"""


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
    """Short visible label for one node's grid tile; accessible name = this text.

    Fix round 1 (coordinator, live-screenshot review): the old `"kind:
    name"` label (e.g. `"tool_call: pytest"`) was wider than the tile's
    fixed CSS width and rendered as `"tool_call..."` for every tool call,
    telling the operator nothing. The tile now shows the tool name alone
    when present (`write_file`, `run_tests`, `web_fetch`) and the bare
    kind otherwise (`prompt`, `decision`, `model_response`) — short enough
    to read without truncation. The fuller `"kind: name"` pairing moves to
    `_event_title` (the tile's `title` attribute and the 5W1H panel's
    "What" field), so nothing is lost, only relocated off the tile face.
    """
    tool = node.get("tool") if isinstance(node.get("tool"), dict) else {}
    name = tool.get("name") if isinstance(tool, dict) else None
    if isinstance(name, str) and name:
        return name
    return str(node.get("kind") or "event")


def _event_title(node: dict[str, Any]) -> str:
    """Full `"kind: name"` text (or bare kind) — see `_event_label`."""
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
        "what": _event_title(node),
        "when": str(node.get("ts") or "not recorded"),
        "where": where,
        "why": str(policy.get("reason"))
        if isinstance(policy, dict) and policy.get("reason")
        else "not recorded",
        "how": how,
    }


def _event_button(node: dict[str, Any], *, label: str | None = None) -> str:
    label = label or _event_label(node)
    title = escape(_event_title(node), quote=True)
    detail = escape(json.dumps(_event_detail_payload(node)), quote=True)
    node_id = escape(str(node.get("id") or ""))
    decision = node.get("decision")
    cell_class = (
        f"cell-{str(decision).lower()}" if isinstance(decision, str) and decision else "cell-plain"
    )
    return (
        f'<button type="button" class="{cell_class}" data-event-id="{node_id}" data-event-kind="{escape(str(node.get("kind") or "event"))}" '
        f'data-event="{detail}" title="{title}">{escape(label)}</button>'
    )


#: Outer-to-inner draw order for the actor-ring SVG (spec section 5 reads
#: skills->memory->routines->tools inward to outward; this list is that
#: order reversed, so the outermost circle is drawn first).
_RING_LAYERS: tuple[tuple[str, int], ...] = (
    ("tools", 62),
    ("routines", 46),
    ("memory", 30),
    ("skills", 14),
)

#: Section 5's bound: a ring's node group past this count collapses to a
#: single "N more" summary rather than rendering an unbounded list.
_RING_MAX_ITEMS = 24


def _dominant_pillar_hex(profile: Any) -> str:
    """Hex for a skill's dominant pillar in its `pillar_profile`, ties broken by fixed order."""
    profile = profile if isinstance(profile, dict) else {}
    best_pillar: str | None = None
    best_count = 0
    for pillar in _PILLAR_FULLNAME_ORDER:
        count = profile.get(pillar)
        count = count if isinstance(count, int) and not isinstance(count, bool) else 0
        if count > best_count:
            best_count = count
            best_pillar = pillar
    if best_pillar is None:
        return _NO_DOMINANT_PILLAR_HEX
    return _VIRTUE_ACCENT_HEX[_PILLAR_FULLNAME_TO_ACCENT[best_pillar]]


def _ring_items(ring: Any, layer: str) -> list[tuple[str, str]]:
    """`(label, tint_hex)` pairs for one ring layer's entries (spec section 5).

    Every label cites the event id, gate reference, digest, or tool/skill
    name it came from — nothing here is unattributed text. `tint_hex` is
    the ring's own colour except for `skills` (tinted by dominant pillar,
    Ruling 5) and `tools` (tinted by the cited decision colour).
    """
    ring = ring if isinstance(ring, dict) else {}
    ring_color = RING_COLORS[layer]
    items: list[tuple[str, str]] = []
    if layer == "skills":
        for skill in ring.get("skills") or []:
            if not isinstance(skill, dict):
                continue
            name = str(skill.get("name") or "unknown")
            rule_count = len(skill.get("rule_ids") or [])
            items.append(
                (f"{name} ({rule_count} rules)", _dominant_pillar_hex(skill.get("pillar_profile")))
            )
    elif layer == "memory":
        for event_id in ring.get("events") or []:
            items.append((str(event_id), ring_color))
        for digest in ring.get("chunk_digests") or []:
            items.append((f"chunk:{digest}", ring_color))
    elif layer == "routines":
        tool_counts = ring.get("tool_counts") if isinstance(ring.get("tool_counts"), dict) else {}
        for name, count in tool_counts.items():
            items.append((f"{name} ×{count}", ring_color))
        for target in ring.get("connect_targets") or []:
            items.append((f"connect:{target}", ring_color))
    elif layer == "tools":
        for tool in ring.get("tools") or []:
            if not isinstance(tool, dict):
                continue
            name = str(tool.get("name") or "unknown")
            decision = str(tool.get("decision") or "UNOBSERVED")
            items.append(
                (
                    f"{name}: {decision}",
                    DECISION_COLORS.get(decision, DECISION_COLORS["UNOBSERVED"]),
                )
            )
    return items


def _render_actor_ring_panel(key: str, rings_for_row: Any) -> str:
    """Render one actor's four-ring concentric SVG + detail lists (spec section 5).

    Hidden by default (`hidden` attribute); `GRAPH_SCRIPT` toggles it on
    the matching `.actor-label` button click and clears it on Escape.
    """
    rings_for_row = rings_for_row if isinstance(rings_for_row, dict) else {}
    circles: list[str] = []
    sections: list[str] = []
    for layer, radius in _RING_LAYERS:
        color = RING_COLORS[layer]
        circles.append(
            f'<circle cx="70" cy="70" r="{radius}" fill="none" stroke="{color}" stroke-width="6"/>'
        )
        ring = rings_for_row.get(layer)
        entries = _ring_items(ring, layer)
        shown = entries[:_RING_MAX_ITEMS]
        overflow = len(entries) - len(shown)
        items_html = "".join(
            f'<li style="--tint:{tint}">{escape(label)}</li>' for label, tint in shown
        )
        if overflow > 0:
            items_html += f'<li class="ring-more">{overflow} more</li>'
        status = ring.get("status") if isinstance(ring, dict) else "unobserved"
        note_html = (
            '<p class="ring-note">No skill manifest in this project (run hyodo skills ingest).</p>'
            if layer == "skills" and status == "unobserved"
            else ""
        )
        sections.append(
            f'<section class="ring-layer" style="--ring-color:{color}">'
            f"<h4>{escape(layer)}</h4>{note_html}<ul>{items_html}</ul></section>"
        )
    svg = (
        '<svg viewBox="0 0 140 140" width="140" height="140" role="img" '
        f'aria-label="Actor rings for {escape(key)}">{"".join(circles)}</svg>'
    )
    return (
        f'<div class="actor-rings" id="rings-{escape(key)}" hidden>'
        f'<div class="rings-visual">{svg}</div>'
        f'<div class="rings-detail">{"".join(sections)}</div>'
        "</div>"
    )


def _display_row_label(key: str, label: str) -> str:
    """Redisplay an `agent:<lineage>` row's label as short text (brief finding 4).

    `build_actor_rows` (`hyodo/graph_view.py`, row identity — not touched
    by this PR) already renders an `actor_id`-identified row's label as
    exactly `agent <actor_id>`; that case is left byte-identical here (its
    label already equals `f"agent {key.removeprefix('agent:')}"`, so the
    equality check below is a no-op for it). A lineage-identified row (no
    `actor_id`) has key `agent:<lineage event id>` and label
    `agent:<tool.name>` or bare `agent` — neither shows *which* lineage
    the row is, so this redisplays it as `agent ` + the lineage id's first
    eight characters instead. Every other row's label (human, hyodo)
    passes through unchanged.
    """
    if not key.startswith("agent:"):
        return label
    lineage_id = key[len("agent:") :]
    if label == f"agent {lineage_id}":
        return label
    return f"agent {lineage_id[:8]}"


def _flatten_row_order(
    rows_tree: dict[str, Any],
) -> tuple[list[str], dict[str | None, list[str]]]:
    """Depth-first row render order (parent immediately before its children).

    Returns the flattened key list (this order *is* the grid's row index,
    `_build_grid_cells` below) and the `{parent_key: [child_key, ...]}`
    map the recursive row renderer also needs to know which rows nest.
    """
    rows = rows_tree.get("rows", {})
    order = rows_tree.get("order", [])
    children: dict[str | None, list[str]] = {}
    for key in order:
        parent = rows.get(key, {}).get("parent_row")
        children.setdefault(parent, []).append(key)
    flat: list[str] = []

    def _walk(key: str) -> None:
        flat.append(key)
        for child_key in children.get(key, []):
            _walk(child_key)

    for key in children.get(None, []):
        _walk(key)
    return flat, children


def _build_grid_cells(
    rows_tree: dict[str, Any], assignments: dict[str, list[str]]
) -> tuple[list[str], dict[str, dict[str, list[str]]], dict[str, tuple[int, int, int]]]:
    """Place every column-assigned node at (row index, column index, cell position).

    Brief finding 1: one grid whose columns are the five virtue columns and
    whose rows are actors, each event a tile at (its column, its row),
    ordered left-to-right within a cell by time. A row's own `events` list
    (`build_actor_rows`) is already earliest-first, so filtering it by
    column membership preserves that order with no extra sort.

    Returns the flattened row order (`_flatten_row_order`), `{row_key:
    {column: [node_id, ...]}}`, and `{node_id: (row_index, col_index,
    tile_index)}` — a node spanning more than one column (brief finding 3
    keeps spans, e.g. a data_boundary ASK) anchors at its first match in
    `VIRTUE_COLUMNS` fixed order. Fix round 2: `_render_edge_overlay` only
    uses this dict's *keys* now (on-grid vs off-grid membership) — the
    row/column/tile-index values themselves stopped feeding edge geometry
    once that moved client-side (`GRAPH_SCRIPT`'s `layoutEdges()`).
    """
    flat_keys, _children = _flatten_row_order(rows_tree)
    rows = rows_tree.get("rows", {})
    cells: dict[str, dict[str, list[str]]] = {}
    anchors: dict[str, tuple[int, int, int]] = {}
    for row_index, key in enumerate(flat_keys):
        row = rows.get(key, {})
        row_cells: dict[str, list[str]] = {}
        for col_index, column in enumerate(VIRTUE_COLUMNS):
            bucket = [
                node_id
                for node_id in row.get("events", [])
                if column in assignments.get(node_id, [])
            ]
            row_cells[column] = bucket
            for tile_index, node_id in enumerate(bucket):
                anchors.setdefault(node_id, (row_index, col_index, tile_index))
        cells[key] = row_cells
    return flat_keys, cells, anchors


def _render_edge_overlay(
    graph: dict[str, Any], anchored_ids: dict[str, Any], *, overlay_id: str = "edge-overlay"
) -> str:
    """SVG overlay skeleton (brief finding 2; fix round 2, coordinator
    live-screenshot review): the server only classifies and counts edges;
    real tile-to-tile geometry is measured client-side.

    Round 1 computed schematic server-side pixel coordinates from a fixed
    `GRID_ROW_HEIGHT` — that drifted the moment a real row's rendered
    height differed from the assumed constant (e.g. a two-line actor
    label made that row taller), so an evidence arc from one row could
    land near an unrelated row two lines away. There is no server-side
    fix for "the server does not know the real layout" other than not
    computing geometry server-side at all: this renders one `<path
    data-source data-target data-kind="parent|evidence" d="">` per
    on-grid edge, and `GRAPH_SCRIPT`'s `layoutEdges()` fills in `d` from
    `getBoundingClientRect()` after the browser has actually laid the
    page out (on load, on resize, and after a row-collapse toggle).

    `graph["edges"]` only ever carries ids that already resolve to a real
    node (`hyodo.event_graph.validate_event_edges` excludes a dangling
    ref from it, into `graph["unresolved_refs"]` instead) — so within
    that list, an endpoint not in `anchored_ids` is a real event with no
    virtue column (e.g. a digest-less `model_response`), not a broken
    ref: that case renders nothing at all (no edge, no stub) and counts
    under `data-offgrid-edges`. A genuinely dangling ref
    (`graph["unresolved_refs"]`) renders `<path data-source
    data-kind="broken" d="">` (no `data-target` — there is nothing to
    target) and counts under `data-broken-edges`; `layoutEdges()` draws
    its short stub from the one anchor it has. Every edge kind's colour
    reads from `EDGE_COLORS` (`--color-edge-*` in
    `site/src/styles/tokens.css`, guarded by
    `tests/test_virtue_colors_ssot.py` the same way `RING_COLORS` is).
    """
    raw_edges = graph.get("edges")
    edges = raw_edges if isinstance(raw_edges, list) else []
    parts: list[str] = []
    parent_count = evidence_count = broken_count = offgrid_count = 0

    for edge in edges:
        source, target = edge.get("source"), edge.get("target")
        source_ok = isinstance(source, str) and source in anchored_ids
        target_ok = isinstance(target, str) and target in anchored_ids
        if edge.get("type") == "parent_event_id":
            if source_ok and target_ok:
                source_attr = (
                    "data-daw-source" if overlay_id == "daw-edge-overlay" else "data-source"
                )
                target_attr = (
                    "data-daw-target" if overlay_id == "daw-edge-overlay" else "data-target"
                )
                parts.append(
                    f'<path class="edge edge-parent" {source_attr}="{escape(str(source))}" '
                    f'{target_attr}="{escape(str(target))}" data-kind="parent" d="" '
                    f'fill="none" stroke="{EDGE_COLORS["parent"]}" stroke-width="1.5"/>'
                )
                parent_count += 1
            else:
                offgrid_count += 1
        elif edge.get("type") == "evidence_ref":
            if source_ok and target_ok:
                source_attr = (
                    "data-daw-source" if overlay_id == "daw-edge-overlay" else "data-source"
                )
                target_attr = (
                    "data-daw-target" if overlay_id == "daw-edge-overlay" else "data-target"
                )
                parts.append(
                    f'<path class="edge edge-evidence" {source_attr}="{escape(str(source))}" '
                    f'{target_attr}="{escape(str(target))}" data-kind="evidence" d="" '
                    f'fill="none" stroke="{EDGE_COLORS["evidence"]}" stroke-width="1.5" '
                    'stroke-dasharray="4 3"/>'
                )
                evidence_count += 1
            else:
                offgrid_count += 1

    for issue in graph.get("unresolved_refs") or []:
        event_id = issue.get("event_id") if isinstance(issue, dict) else None
        if isinstance(event_id, str) and event_id in anchored_ids:
            source_attr = "data-daw-source" if overlay_id == "daw-edge-overlay" else "data-source"
            parts.append(
                f'<path class="edge edge-broken" {source_attr}="{escape(event_id)}" '
                f'data-kind="broken" d="" fill="none" stroke="{EDGE_COLORS["broken"]}" '
                'stroke-width="2"/>'
            )
            broken_count += 1

    return (
        f'<svg id="{escape(overlay_id)}" class="edge-overlay" role="img" aria-hidden="true" '
        f'data-parent-edges="{parent_count}" data-evidence-edges="{evidence_count}" '
        f'data-broken-edges="{broken_count}" data-offgrid-edges="{offgrid_count}">'
        + "".join(parts)
        + "</svg>"
    )


def _orb_grid_html(
    lit_count: int, color: str, pulse_period: float, decision: str, observed: int, expected: int
) -> str:
    """The orb's 9x9 pixel-grid pulse (brief finding 5), ported from the site
    hero's unlit-tile-field idea (`site/src/hero/scene.ts`) in plain
    CSS/SVG — no three.js, no external script. `lit_count` is the run's
    raw `observed` count, capped at the grid's 81 cells: a second
    rendering of the same number the verdict line/column badges already
    print (never a synthesized ratio, never a percentage). The pulse
    period is a CSS custom property so `prefers-reduced-motion` can
    disable the animation outright in CSS alone.
    """
    total = ORB_GRID_TOTAL
    lit_count = max(0, min(total, lit_count))
    cells = "".join(
        f'<span class="orb-cell orb-cell-lit" style="--tint:{color}"></span>'
        if index < lit_count
        else '<span class="orb-cell"></span>'
        for index in range(total)
    )
    return (
        f'<div class="orb-grid" role="img" data-decision="{escape(decision)}" '
        f'data-lit-count="{lit_count}" style="--pulse-period:{pulse_period}s" '
        f'aria-label="Core engine pulse: latest decision {escape(decision)}, '
        f'{observed}/{expected} observed">{cells}</div>'
    )


def _render_column_header(
    key: str,
    hanja: str,
    korean: str,
    english: str,
    color: str,
    cov: dict[str, int],
    audience: str,
    extra_note_html: str = "",
) -> str:
    """One virtue column's header cell (brief finding 6 adds the empty-column question)."""
    question_html = ""
    if cov["expected"] == 0:
        table = _COLUMN_QUESTIONS[key]
        question = table.get(audience, table["engineer"])
        question_html = f'<p class="column-question">{escape(question)}</p>'
    return (
        f'<div class="grid-colhead" data-column="{escape(key)}">'
        f'<h2 id="col-{escape(key)}" style="--accent:{_VIRTUE_ACCENT_HEX[color]}">'
        f'<span lang="ko">{escape(hanja)} {escape(korean)}</span> {escape(english)}</h2>'
        f'<p class="coverage">{cov["observed"]}/{cov["expected"]} observed</p>'
        f"{extra_note_html}{question_html}</div>"
    )


def _render_grid_row(
    key: str,
    rows_tree: dict[str, Any],
    cells: dict[str, dict[str, list[str]]],
    node_by_id: dict[str, dict[str, Any]],
    rings: dict[str, dict[str, Any]],
    children: dict[str | None, list[str]],
) -> str:
    """Render one grid row (row-header cell + five virtue-column cells).

    Indented by `depth * 18px` (brief addendum item 8: nested child rows
    render indented); a row with children gets a `row-toggle` disclosure
    button `GRAPH_SCRIPT` wires to hide/show its descendants (collapsible,
    same requirement). The row's own ring-panel affordance
    (`_render_actor_ring_panel`) is unchanged from before this PR.
    """
    row = rows_tree.get("rows", {}).get(key, {})
    depth = row.get("depth", 0)
    label = _display_row_label(key, str(row.get("label", key)))
    role = row.get("role")
    role_html = f' <span class="row-role">{escape(str(role))}</span>' if role else ""
    has_rings = key in rings
    label_html = (
        f'<button type="button" class="actor-label" data-actor-key="{escape(key)}" '
        f'aria-expanded="false" aria-controls="rings-{escape(key)}">{escape(label)}</button>'
        if has_rings
        else escape(label)
    )
    has_children = bool(children.get(key))
    toggle_html = (
        f'<button type="button" class="row-toggle" data-row-toggle="{escape(key)}" '
        'aria-expanded="true" aria-label="Collapse child rows">-</button>'
        if has_children
        else ""
    )
    rowhead = (
        f'<div class="grid-rowhead" style="padding-left:{depth * 18}px">'
        f'{toggle_html}<span class="row-header">{label_html}{role_html}</span></div>'
    )
    row_cells = cells.get(key, {})
    cell_html = "".join(
        f'<div class="grid-cell" data-row-key="{escape(key)}" data-column="{escape(column)}">'
        + "".join(
            _event_button(node_by_id[node_id])
            for node_id in row_cells.get(column, [])
            if node_id in node_by_id
        )
        + "</div>"
        for column in VIRTUE_COLUMNS
    )
    panel_html = _render_actor_ring_panel(key, rings[key]) if has_rings else ""
    parent_row = row.get("parent_row") or ""
    return (
        f'<div class="grid-row" data-row-key="{escape(key)}" '
        f'data-parent-row="{escape(str(parent_row))}" data-depth="{depth}">'
        f"{rowhead}{cell_html}</div>{panel_html}"
    )


def _render_grid_rows(
    rows_tree: dict[str, Any],
    cells: dict[str, dict[str, list[str]]],
    node_by_id: dict[str, dict[str, Any]],
    rings: dict[str, dict[str, Any]] | None,
    flat_keys: list[str],
) -> str:
    """Render every grid row in flattened (depth-first) display order."""
    rings = rings or {}
    _flat, children = _flatten_row_order(rows_tree)
    return "".join(
        _render_grid_row(key, rows_tree, cells, node_by_id, rings, children) for key in flat_keys
    )


def _daw_track(node: dict[str, Any]) -> tuple[str, str]:
    """Choose a display-only DAW lane from observed event identity.

    This is intentionally not added to the event schema. A graph viewer needs
    a readable arrangement even when the producer only supplies the coarse
    ``actor`` field; the event id/tool name are already recorded evidence and
    are sufficient for a stable local presentation lane.
    """
    actor = str(node.get("actor") or "").lower()
    if actor == "human":
        return "human", "Human"
    if actor == "hyodo":
        return "reviewer", "Reviewer"
    if actor == "agent":
        return "executor", "Executor"
    return "planner", "Planner"


def _daw_event_label(node: dict[str, Any]) -> str:
    """Compact prototype-style label with measured signal still visible."""
    node_id = str(node.get("id") or "").lower()
    kind = str(node.get("kind") or "event").lower()
    suffix = "call" if kind == "tool_call" else "result"
    if "parallel" in node_id:
        return f"parallel / {suffix}"
    if "join" in node_id:
        return f"dag join / {suffix}"
    if "retry-call-1" in node_id or "retry-result-1" in node_id:
        return f"retry 1 / {suffix}"
    if "retry-call-2" in node_id or "retry-result-2" in node_id:
        return f"rework / {suffix}"
    if "wait" in node_id:
        return f"wait / {suffix}"
    if "unresolved" in node_id:
        return "unresolved"
    if "human" in node_id:
        return "approval"
    return _event_label(node)


def _render_daw_timeline(
    nodes: list[dict[str, Any]], edges: list[dict[str, Any]], edge_overlay: str = ""
) -> tuple[str, dict[str, tuple[int, int, int]]]:
    """Render the user-facing DAW timeline and return edge anchor membership."""
    valid_nodes = [node for node in nodes if isinstance(node.get("id"), str)]
    max_step = max(
        (node.get("step_index") for node in valid_nodes if isinstance(node.get("step_index"), int)),
        default=0,
    )
    columns = max_step + 1
    run_id = next(
        (str(node.get("run_id")) for node in valid_nodes if node.get("run_id")), "unobserved"
    )
    track_order = ["human", "planner", "executor", "reviewer"]
    track_labels = {
        "human": "Human",
        "planner": "Planner",
        "executor": "Executor",
        "reviewer": "Reviewer",
    }
    buckets: dict[tuple[str, int], list[dict[str, Any]]] = {}
    track_seen: set[str] = set()
    anchors: dict[str, tuple[int, int, int]] = {}
    for node in sorted(
        valid_nodes, key=lambda item: (item.get("step_index", 0), str(item.get("ts", "")))
    ):
        track, _label = _daw_track(node)
        track_seen.add(track)
        step = node.get("step_index") if isinstance(node.get("step_index"), int) else 0
        buckets.setdefault((track, step), []).append(node)

    visible_tracks = [track for track in track_order if track in track_seen]
    parts = [
        '<section class="daw-console" aria-label="Evidence session timeline">',
        f'<div class="daw-sessionbar"><div><span>EVIDENCE CONSOLE</span><strong>SESSION / {escape(run_id)}</strong></div>'
        f'<div><span class="session-state">■ STATIC VIEW</span><span>STEP INDEX <b>t0 — t{max_step}</b></span>'
        '<span class="session-boundary">LOCAL DATA / NOT SEALED</span></div></div>',
        '<div class="daw-console-head"><div><span class="daw-kicker">EVIDENCE SESSION / LIVE READBACK</span>'
        '<h2>Run timeline</h2></div><div class="daw-legend"><span><i class="legend-call"></i>CALL</span>'
        '<span><i class="legend-result"></i>RESULT</span><span><i class="legend-human"></i>HUMAN</span></div></div>',
        f'<div class="daw-rows" style="--daw-columns:{columns}">',
        '<div class="daw-ruler"><div class="daw-track-label">TRACK / SIGNAL</div>'
        + "".join(
            f'<div class="daw-step">t{index}<small>{index:02d}</small></div>'
            for index in range(columns)
        )
        + "</div>",
    ]
    for row_index, track in enumerate(visible_tracks):
        label = track_labels[track]
        parts.append(
            f'<div class="daw-row" data-daw-track="{escape(track)}"><div class="daw-track-label">'
            f'<span class="track-led track-{escape(track)}"></span>{escape(label)}<small>{row_index:02d}</small></div>'
        )
        for step in range(columns):
            events = buckets.get((track, step), [])
            if not events:
                parts.append('<div class="daw-cell daw-empty"></div>')
                continue
            parts.append('<div class="daw-cell">')
            for tile_index, node in enumerate(events):
                node_id = str(node["id"])
                anchors[node_id] = (row_index, step, tile_index)
                parts.append(_event_button(node, label=_daw_event_label(node)))
            parts.append("</div>")
        parts.append("</div>")
    parts.extend([edge_overlay, "</div>", "</section>"])
    return "".join(parts), anchors


def render_graph_html(
    graph: dict[str, Any], *, now: datetime | None = None, root: Path | None = None
) -> str:
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

    `root` (Package 2-C, step (c)) is the checkout `build_actor_rings`
    reads local manifests from; omitting it (as `hyodo report` never
    calls this function, and a caller with no checkout on disk might not
    either) degrades to rows with no rings affordance rather than
    failing, the same "still renders, less to show" pattern as section
    8's missing-asset fallback. It is also passed to `assign_columns`/
    `orb_state` so the file-tool Hyo/Goodness split resolves paths against
    the real checkout boundary (falling back to `graph["root"]` when this
    parameter is omitted but the graph payload carries one).
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

    effective_root = root
    if effective_root is None:
        graph_root = graph.get("root")
        effective_root = Path(graph_root) if isinstance(graph_root, str) and graph_root else None
    assignments = {
        node_id: assign_columns(node, effective_root) for node_id, node in node_by_id.items()
    }
    coverage = column_coverage(nodes, assignments, edges)
    orb = orb_state(graph, effective_root)
    rows_tree = build_actor_rows(nodes, edges)
    rings = build_actor_rings(graph, root) if root is not None else {}
    audience = resolve_audience(root).profile if root is not None else "engineer"

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

    _daw_preview, daw_anchors = _render_daw_timeline(nodes, edges)
    daw_edge_overlay = _render_edge_overlay(graph, daw_anchors, overlay_id="daw-edge-overlay")
    daw_html, _ = _render_daw_timeline(nodes, edges, daw_edge_overlay)

    # Brief finding 1: one grid, columns x actor rows, each event a tile at
    # (its column, its row) — replaces the old two-separate-lists layout
    # (five pooled column sections plus a disconnected row listing).
    flat_keys, grid_cells, anchors = _build_grid_cells(rows_tree, assignments)
    column_headers = "".join(
        _render_column_header(
            key,
            hanja,
            korean,
            english,
            color,
            coverage.get(key, {"observed": 0, "expected": 0}),
            audience,
            mission_note if key == "hyo" else "",
        )
        for key, hanja, korean, english, color in PILLAR_SPECS[:5]
    )
    grid_rows_html = _render_grid_rows(rows_tree, grid_cells, node_by_id, rings, flat_keys)
    edge_overlay_html = _render_edge_overlay(graph, anchors)

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

    all_ts = [_parse_iso_ts(node.get("ts")) for node in nodes]
    known_ts = sorted(ts for ts in all_ts if ts is not None)
    time_ruler_html = (
        '<div class="time-ruler" aria-hidden="true">'
        f'<span class="time-ruler-start">{escape(known_ts[0].isoformat())}</span>'
        '<span class="time-ruler-line"></span>'
        f'<span class="time-ruler-end">{escape(known_ts[-1].isoformat())} (oldest → newest)</span>'
        "</div>"
        if known_ts
        else ""
    )

    latest_ts = _parse_iso_ts(orb.get("latest_ts"))
    pulse_eligible = latest_ts is not None and (now - latest_ts).total_seconds() < 60
    orb_decision = str(orb.get("decision") or "UNOBSERVED")
    orb_cov = orb.get("coverage") or {"observed": 0, "expected": 0}
    orb_color = DECISION_COLORS.get(orb_decision, DECISION_COLORS["UNOBSERVED"])
    pulse_period = ORB_PULSE_PERIOD_RECENT if pulse_eligible else ORB_PULSE_PERIOD_IDLE
    # The orb caption's total is the sum of the five column badges below —
    # never a new number — so the breakdown line spells out those exact
    # addends next to the total, per column, in the same fixed order.
    breakdown = " · ".join(
        f"{english} {coverage.get(key, {'observed': 0, 'expected': 0})['observed']}/"
        f"{coverage.get(key, {'observed': 0, 'expected': 0})['expected']}"
        for key, _hanja, _korean, english, _color in PILLAR_SPECS[:5]
    )
    orb_html = (
        _orb_grid_html(
            orb_cov["observed"],
            orb_color,
            pulse_period,
            orb_decision,
            orb_cov["observed"],
            orb_cov["expected"],
        )
        + f'<p class="orb-caption" title="{escape(breakdown)}">{escape(orb_decision)} · '
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
.orb-grid {{ display:grid; grid-template-columns:repeat({ORB_GRID_SIZE},1fr); gap:2px; width:96px; height:96px; animation:hyodo-orb-grid-pulse var(--pulse-period,4s) ease-in-out infinite }}
.orb-cell {{ background:var(--line-soft); border-radius:2px }} .orb-cell-lit {{ background:var(--tint,#6b7280) }}
@keyframes hyodo-orb-grid-pulse {{ 0%,100% {{ opacity:1 }} 50% {{ opacity:.5 }} }}
@media (prefers-reduced-motion:reduce) {{ .orb-grid {{ animation:none }} }}
.orb-caption {{ color:var(--muted); font-size:.9rem; margin:0 }}
.orb-breakdown {{ color:var(--muted); font-size:.78rem; margin:.2rem 0 0; text-align:center }}
.grid-wrap {{ overflow-x:auto; margin-bottom:18px }}
.grid-graph {{ display:inline-block; min-width:{GRID_LABEL_WIDTH + 5 * GRID_COLUMN_WIDTH}px; border:1px solid var(--line); border-radius:12px; background:var(--surface) }}
.grid-headrow, .grid-row {{ display:flex }}
.grid-corner {{ width:{GRID_LABEL_WIDTH}px; flex:0 0 auto; border-bottom:1px solid var(--line) }}
.grid-colhead {{ width:{GRID_COLUMN_WIDTH}px; flex:0 0 auto; border-bottom:1px solid var(--line); border-left:1px solid var(--line-soft); padding:10px; border-top:6px solid var(--accent,#888) }}
.grid-colhead h2 {{ margin:0 0 4px; font-size:.95rem }} .grid-colhead h2 span {{ color:var(--accent); font-size:.85rem }}
.coverage {{ margin:0 0 6px; color:var(--muted); font-size:.85rem }} .column-note, .column-question {{ font-size:.78rem; color:var(--muted); margin:2px 0 0 }}
.grid-rows {{ position:relative }}
.grid-rowhead {{ width:{GRID_LABEL_WIDTH}px; flex:0 0 auto; min-height:{GRID_ROW_HEIGHT}px; box-sizing:border-box; border-top:1px solid var(--line-soft); padding:8px 10px; display:flex; align-items:center; gap:6px }}
.grid-cell {{ width:{GRID_COLUMN_WIDTH}px; flex:0 0 auto; min-height:{GRID_ROW_HEIGHT}px; box-sizing:border-box; border-top:1px solid var(--line-soft); border-left:1px solid var(--line-soft); padding:6px; display:flex; flex-wrap:nowrap; align-items:center; gap:{GRID_TILE_GAP}px; overflow-x:auto }}
.row-header {{ display:inline-flex; align-items:baseline; gap:6px; font-weight:600 }}
.row-role {{ font-weight:400; font-size:.78rem; color:var(--muted) }}
.row-toggle {{ border:none; background:none; color:var(--muted); cursor:pointer; padding:0 2px; font-size:.8rem }}
.actor-label {{ font:inherit; font-weight:600 }}
.grid-cell button {{ width:{GRID_TILE_WIDTH}px; flex:0 0 auto; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:.72rem }}
button {{ font:inherit; border:1px solid var(--line); background:var(--surface); color:var(--ink); border-radius:8px; padding:6px 9px; cursor:pointer }}
*:focus-visible {{ outline:3px solid var(--focus); outline-offset:2px }}
.cell-deny {{ border-color:{DECISION_COLORS["DENY"]} }} .cell-ask {{ border-color:{DECISION_COLORS["ASK"]} }} .cell-allow {{ border-color:{DECISION_COLORS["ALLOW"]} }} .cell-unobserved {{ border-color:{DECISION_COLORS["UNOBSERVED"]} }}
.time-ruler {{ display:flex; justify-content:space-between; align-items:center; gap:8px; color:var(--muted); font-size:.72rem; margin:6px 0 18px }}
.time-ruler-line {{ flex:1; height:1px; background:var(--line) }}
.edge-overlay {{ position:absolute; inset:0; width:100%; height:100%; pointer-events:none; overflow:visible }}
.edge.edge-active {{ stroke-width:3; filter:drop-shadow(0 0 2px currentColor) }}
.cells {{ display:flex; flex-wrap:wrap; gap:6px }}
.gutter {{ margin-bottom:18px }} .gutter h2 {{ font-size:.95rem }}
button[hidden], .grid-row[hidden] {{ display:none }}
.detail {{ margin-top:20px; border:1px solid var(--line); border-radius:12px; padding:14px; background:var(--surface); min-height:80px }} .detail p {{ margin:.25rem 0 }}
.actor-rings[hidden] {{ display:none }}
.actor-rings {{ display:flex; flex-wrap:wrap; gap:16px; margin:10px 0 4px; padding:12px; border:1px solid var(--line); border-radius:12px; background:var(--surface) }}
.rings-visual {{ flex:0 0 auto }}
.rings-detail {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; flex:1 1 260px }}
.ring-layer h4 {{ margin:0 0 4px; font-size:.8rem; color:var(--ring-color); text-transform:capitalize }}
.ring-layer ul {{ list-style:none; margin:0; padding:0; font-size:.78rem; color:var(--ink) }}
.ring-layer li {{ border-left:3px solid var(--tint,var(--ring-color)); padding:1px 0 1px 6px; margin:2px 0 }}
.ring-layer li.ring-more {{ color:var(--muted); border-left-color:var(--line) }}
.ring-note {{ font-size:.75rem; color:var(--muted); margin:0 0 4px }}

/* DAW / instrument-console presentation. The legacy virtue grid stays in
   the DOM for contract compatibility, but the operator-facing graph is the
   measured event timeline below. */
.legacy-orb, .legacy-proof-grid, .legacy-proof-gutter {{ display:none }}
body {{ background:#0b0d0e; color:#e8ece9; font-family:"SFMono-Regular",Consolas,"Liberation Mono",monospace }}
main {{ max-width:1480px; padding:28px 28px 56px }}
header {{ border-bottom:1px solid #343a38; padding-bottom:18px; margin-bottom:20px }}
h1 {{ letter-spacing:-.04em; text-transform:uppercase; font-size:clamp(1.5rem,3vw,2.5rem) }}
.meta, .meta a {{ color:#8d9792 }}
.unobserved-notice {{ border-radius:0; background:#321d1d; color:#ffb5a9; border:1px solid #9d4d43 }}
.daw-console {{ position:relative; overflow:auto; border:1px solid #3b4440; background:#111514; box-shadow:0 18px 50px #0008; padding:18px; margin:4px 0 16px }}
.daw-sessionbar {{ display:flex; justify-content:space-between; gap:20px; border:1px solid #343c38; padding:11px 12px; margin-bottom:16px; min-width:980px; color:#aab4ae; font-size:.68rem; letter-spacing:.08em }}
.daw-sessionbar div {{ display:flex; gap:18px; align-items:center }} .daw-sessionbar span {{ color:#738078 }} .daw-sessionbar strong {{ color:#e4ebe5; letter-spacing:.1em }}
.daw-sessionbar b, .session-boundary {{ color:#e4ba58 !important }} .session-state {{ color:#de7868 !important }}
.daw-console-head {{ display:flex; justify-content:space-between; align-items:end; gap:20px; border-bottom:1px solid #303734; padding:2px 0 14px; min-width:980px }}
.daw-kicker {{ color:#8fbd73; font-size:.68rem; letter-spacing:.16em }}
.daw-console h2 {{ margin:5px 0 0; font-size:1.25rem; letter-spacing:.05em; text-transform:uppercase }}
.daw-legend {{ display:flex; gap:14px; color:#929c96; font-size:.68rem; letter-spacing:.08em }}
.daw-legend i {{ display:inline-block; width:8px; height:8px; margin-right:5px; background:#82bd69 }}
.daw-legend .legend-result {{ background:#d5a04c }}
.daw-legend .legend-human {{ background:#de7868 }}
.daw-rows {{ position:relative; min-width:1060px; padding-top:14px }}
.daw-ruler, .daw-row {{ display:grid; grid-template-columns:190px repeat(var(--daw-columns), minmax(104px,1fr)); min-width:1060px }}
.daw-ruler {{ color:#7c8881; font-size:.68rem; letter-spacing:.09em; border-bottom:1px solid #3b4440 }}
.daw-step {{ padding:0 8px 8px; border-left:1px solid #2c3431; font-variant-numeric:tabular-nums }}
.daw-step small {{ display:block; color:#4f5b55; margin-top:3px }}
.daw-track-label {{ display:flex; align-items:center; gap:7px; padding:0 10px; color:#aab4ae; font-size:.69rem; letter-spacing:.08em; border-right:1px solid #343c38 }}
.daw-track-label small {{ margin-left:auto; color:#4d5852 }}
.daw-row {{ min-height:78px; border-bottom:1px solid #2a312e }}
.daw-cell {{ min-height:78px; padding:7px 5px; border-left:1px solid #252d29; display:flex; flex-direction:column; gap:4px; justify-content:center }}
.daw-empty {{ background:repeating-linear-gradient(135deg,transparent 0 8px,#ffffff03 8px 9px) }}
.daw-cell button {{ width:100%; min-width:0; border-radius:0; border:1px solid #4b5750; background:#1a211e; color:#dce5df; padding:8px 7px; font-size:.66rem; letter-spacing:.02em; text-align:left; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; cursor:pointer }}
.daw-cell button:hover, .daw-cell button:focus-visible {{ border-color:#d9ead7; background:#26332c }}
.daw-cell button[data-event-kind="tool_call"] {{ border-left:3px solid #82bd69 }}
.daw-cell button[data-event-kind="tool_result"] {{ border-left:3px solid #d5a04c }}
.daw-cell button[data-event-kind="prompt"] {{ border-left:3px solid #de7868 }}
.daw-cell button[data-event-kind="decision"] {{ border-left:3px solid #b8a5eb }}
.track-led {{ width:7px; height:7px; flex:0 0 auto; background:#82bd69; box-shadow:0 0 8px #82bd69 }}
.track-human {{ background:#f0b36c; box-shadow:0 0 8px #f0b36c }}
.track-planner {{ background:#72a9d5; box-shadow:0 0 8px #72a9d5 }}
.track-executor {{ background:#82bd69; box-shadow:0 0 8px #82bd69 }}
.track-reviewer {{ background:#b8a5eb; box-shadow:0 0 8px #b8a5eb }}
.daw-rows .edge-overlay {{ z-index:3 }}
.daw-rows .edge {{ stroke:#82bd69; opacity:.68 }}
.daw-rows .edge-evidence {{ stroke:#d5a04c; stroke-dasharray:4 3 }}
.daw-rows .edge-broken {{ stroke:#de7868 }}
.daw-rows .edge.edge-active {{ stroke-width:3; opacity:1; filter:drop-shadow(0 0 4px currentColor) }}
.detail {{ border-radius:0; background:#111514; border-color:#3b4440; color:#cdd8d1; font-size:.75rem; min-height:86px }}
@media (max-width:820px) {{ main {{ padding:18px 14px 40px }} .daw-console {{ margin-inline:-14px; border-inline:0 }} .daw-console-head {{ padding-inline:14px }} .detail {{ border-radius:0 }} }}
@media (prefers-reduced-motion:reduce) {{ .daw-cell button {{ transition:none }} }}
</style></head><body><main><header><div><h1>HyoDo Evidence Graph</h1><p class="meta">Local only · No composite score · <a href="/">Back to instrument panel</a></p></div></header>
{notice_html}
<section class="orb-wrap legacy-orb">{orb_html}</section>
{daw_html}
<div class="grid-wrap legacy-proof-grid">
<div class="grid-graph">
<div class="grid-headrow"><div class="grid-corner"></div>{column_headers}</div>
<div class="grid-rows">{grid_rows_html}{edge_overlay_html}</div>
</div>
{time_ruler_html}
</div>
<div class="legacy-proof-gutter">{gutter_html}</div>
<section id="event-detail" class="detail" aria-live="polite"><p>Select an event to see its 5W1H detail.</p></section>
</main><script>{GRAPH_SCRIPT}</script></body></html>"""
