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
    UNMEASURED,
    VIRTUE_COLUMNS,
    assign_columns,
    build_actor_rings,
    build_actor_rows,
    column_coverage,
    orb_state,
)
from hyodo.verification_view import build_verification_view
from hyodo.virtues import DOCUMENT_VIRTUE_NAMES, VIRTUE_CONTRACT

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
const DEFAULT_DETAIL = panel ? Array.from(panel.childNodes, (node) => node.cloneNode(true)) : [];
const FIELDS = [
  ["Who", "who"],
  ["What", "what"],
  ["When", "when"],
  ["Where", "where"],
  ["Why", "why"],
  ["How", "how"],
];
const LENS_LABELS = { jin: "眞", seon: "善", mi: "美", in: "仁", hyo: "孝" };
const LENS_ENGLISH = { jin: "Truth", seon: "Goodness", mi: "Beauty", in: "Benevolence", hyo: "Hyo" };
function addText(parent, tag, text, className) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = text;
  parent.appendChild(element);
  return element;
}
function addSection(title, className) {
  const section = document.createElement("section");
  section.className = className;
  addText(section, "h3", title);
  return section;
}
function coverageState(entry) {
  if (!entry || typeof entry !== "object") return "UNOBSERVED";
  const observed = Number(entry.observed);
  const expected = Number(entry.expected);
  if (!Number.isFinite(observed) || !Number.isFinite(expected) || expected <= 0 || observed <= 0) {
    return "UNOBSERVED";
  }
  return observed >= expected ? "OBSERVED" : "PARTIAL";
}
function lensMark(state) {
  return state === "OBSERVED" ? "●" : state === "PARTIAL" ? "◐" : "○";
}
function addIntentReview(panel, data) {
  const section = addSection("WHY / INTENT COMPARISON", "intent-review");
  const review = data.intentReview || {};
  addText(section, "p", "User intent source: " + String(review.intent_ref || "UNOBSERVED"));
  addText(section, "p", "Comparison target: " + String(review.target || "UNOBSERVED") + " · " + String(review.mode || "UNOBSERVED"));
  addText(section, "p", "Host-supplied requirements and values; resolved references do not authenticate intent, verify values, or authorize action.");
  const history = review.history || {};
  addText(section, "p", "Previous comparison: " + String(history.previous_review_ref || "UNOBSERVED") + " · " + String(history.state || "UNOBSERVED"));
  if (history.intent_source_changed === true) addText(section, "p", "Intent source changed. This link does not establish user approval of the change.");
  for (const change of (Array.isArray(history.requirement_changes) ? history.requirement_changes : [])) {
    addText(section, "p", "Recorded requirement change: " + String(change.id) + " · " + String(change.kind) + " · " + JSON.stringify(change.before) + " → " + JSON.stringify(change.after));
  }
  const checks = Array.isArray(review.checks) ? review.checks : [];
  if (!checks.length) addText(section, "p", "UNOBSERVED · no requirement comparison was recorded.");
  for (const check of checks) {
    const item = addSection(String(check.dimension) + " / " + String(check.id), "intent-check");
    addText(item, "p", "Evidence-qualified comparison: " + String(check.state));
    addText(item, "p", "Requirement basis: " + String(check.basis));
    addText(item, "p", "Expected: " + JSON.stringify(check.expected) + " · operator: " + String(check.operator));
    addText(item, "p", "Reported actual: " + (check.actual === null ? "UNOBSERVED" : JSON.stringify(check.actual)) + " · unit: " + String(check.unit || "not specified"));
    addText(item, "p", "Value comparison: " + String(check.comparison) + " · actual minus expected: " + String(check.delta ?? "not applicable"));
    addText(item, "p", "Evidence refs: " + (Array.isArray(check.evidence_refs) ? check.evidence_refs.join(", ") : "UNOBSERVED"));
    if (Array.isArray(check.missing) && check.missing.length) addText(item, "p", "Missing or withheld: " + check.missing.join(", "));
    section.appendChild(item);
  }
  if (Array.isArray(review.missing_dimensions) && review.missing_dimensions.length) {
    addText(section, "p", "Dimensions without checks: " + review.missing_dimensions.join(", "));
  }
  panel.appendChild(section);
}
function addLensAperture(panel, data) {
  const section = addSection("FIVE-LENS APERTURE", "lens-aperture");
  const intro = document.createElement("p");
  intro.className = "lens-aperture-intro";
  intro.textContent = "Selected event · independent evidence coverage, not a virtue verdict";
  section.appendChild(intro);
  const diagram = document.createElement("div");
  diagram.className = "lens-aperture-diagram";
  diagram.setAttribute("role", "group");
  diagram.setAttribute("aria-label", "Five independent lens coverage indicators");
  const center = document.createElement("div");
  center.className = "lens-aperture-center";
  center.textContent = "SELECTED EVENT";
  diagram.appendChild(center);
  const details = document.createElement("div");
  details.className = "lens-aperture-details";
  const columns = Array.isArray(data.columns) ? data.columns : [];
  const runCoverage = data.runCoverage && typeof data.runCoverage === "object" ? data.runCoverage : {};
  for (const key of Object.keys(LENS_LABELS)) {
    const eventState = columns.includes(key) ? "OBSERVED" : "UNOBSERVED";
    const runState = coverageState(runCoverage[key]);
    const button = document.createElement("button");
    button.type = "button";
    button.className = "lens-segment";
    button.dataset.lensKey = key;
    button.dataset.lensState = eventState;
    button.dataset.runLensState = runState;
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-label", `${LENS_ENGLISH[key]}, selected event ${eventState.toLowerCase()}, run coverage ${runState.toLowerCase()}`);
    addText(button, "span", lensMark(eventState), "lens-glyph lens-event-glyph");
    addText(button, "strong", LENS_LABELS[key], "lens-hanja");
    addText(button, "small", lensMark(runState) + " " + runState, "lens-run-state");
    const detail = document.createElement("span");
    detail.className = "lens-segment-detail";
    detail.hidden = true;
    addText(detail, "span", `Selected event: ${eventState}`);
    const coverage = runCoverage[key];
    const coverageText = coverage && typeof coverage === "object"
      ? `${String(coverage.observed ?? 0)} / ${String(coverage.expected ?? 0)}`
      : "UNOBSERVED";
    addText(detail, "span", `Run coverage: ${runState} · ${coverageText}`);
    if (key === "in") {
      addText(detail, "span", String(data.who || "From: UNOBSERVED → To: UNOBSERVED"));
      addText(detail, "span", "A recorded relationship does not establish its impact or grant authority.");
    }
    detail.id = `lens-detail-${key}`;
    button.setAttribute("aria-controls", detail.id);
    details.appendChild(detail);
    button.addEventListener("click", () => {
      const expanded = button.getAttribute("aria-expanded") === "true";
      button.setAttribute("aria-expanded", String(!expanded));
      details.querySelectorAll(".lens-segment-detail").forEach((entry) => { entry.hidden = true; });
      diagram.querySelectorAll(".lens-segment").forEach((entry) => { entry.setAttribute("aria-expanded", "false"); });
      button.setAttribute("aria-expanded", String(!expanded));
      detail.hidden = expanded;
    });
    diagram.appendChild(button);
  }
  section.appendChild(diagram);
  section.appendChild(details);
  const axis = document.createElement("div");
  axis.className = "lens-aperture-axis";
  addText(axis, "span", "TIME", "lens-axis-symbol");
  addText(axis, "span", `step ${String(data.stepIndex ?? "UNOBSERVED")}`, "lens-axis-step");
  addText(axis, "span", "selected moment →", "lens-axis-arrow");
  section.appendChild(axis);
  const continuity = addSection("永 / CONTINUITY", "lens-continuity");
  addText(continuity, "p", "UNOBSERVED · no independent continuity assessment is supplied by this view.");
  addText(continuity, "p", "Chronological placement alone does not establish continuity or long-term value.");
  section.appendChild(continuity);
  panel.appendChild(section);
}
const cells = document.querySelectorAll(".cells button[data-event], .grid-cell button[data-event], .daw-cell button[data-event]");
let lastFocusedCell = null;
function highlightEdges(eventId) {
  document.querySelectorAll("#daw-edge-overlay .edge, #edge-overlay .edge").forEach((edge) => {
    const source = edge.dataset.dawSource || edge.dataset.source;
    const target = edge.dataset.dawTarget || edge.dataset.target;
    const active = eventId && (source === eventId || target === eventId);
    edge.classList.toggle("edge-active", Boolean(active));
  });
  document.querySelectorAll(".daw-cell button[data-event-id]").forEach((tile) => {
    tile.classList.toggle("event-active", Boolean(eventId && tile.dataset.eventId === eventId));
  });
}
function layoutEdges() {
  const svg = document.getElementById("daw-edge-overlay") || document.getElementById("edge-overlay");
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
    const status = document.createElement("div");
    status.className = "detail-status-strip";
    addText(status, "span", "RECORDED " + String(data.recordedDecision || "UNOBSERVED"));
    addText(status, "span", "PRESENTABLE " + String(data.presentableDecision || "UNOBSERVED"));
    panel.appendChild(status);
    for (const [label, key] of FIELDS) {
      const p = document.createElement("p");
      const strong = document.createElement("strong");
      strong.textContent = label + ": ";
      p.appendChild(strong);
      p.appendChild(document.createTextNode(String(data[key] ?? "not recorded")));
      panel.appendChild(p);
    }
    addText(panel, "p", "Recorded actor: " + String(data.recordedActor || "UNOBSERVED"));
    addText(panel, "p", "Policy rationale: " + String(data.policyRationale || "UNOBSERVED"));
    addIntentReview(panel, data);
    addLensAperture(panel, data);
    const proof = addSection("PROOF", "detail-proof");
    addText(proof, "p", "Causal parents: " + String(data.causalParentCount ?? 0));
    addText(proof, "p", "Evidence refs: " + String(data.evidenceRefCount ?? 0));
    addText(proof, "p", "Output digest: " + String(data.outputDigest || "UNOBSERVED"));
    panel.appendChild(proof);
    const missing = addSection("WHAT IS MISSING", "detail-missing");
    const missingItems = Array.isArray(data.missing) ? data.missing : [];
    addText(missing, "p", missingItems.length ? missingItems.join(", ") : "None recorded");
    panel.appendChild(missing);
  };
  button.addEventListener("focus", show);
  button.addEventListener("click", () => {
    show();
    if (panel) panel.scrollIntoView({ block: "nearest" });
  });
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
  if (panel) panel.replaceChildren(...DEFAULT_DETAIL.map((node) => node.cloneNode(true)));
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


# Compatibility presentation tuple derived from the canonical six-virtue
# ontology. The first five fields remain stable for existing renderers.
_VIRTUE_SLUGS = ("jin", "seon", "mi", "in", "hyo", "yeong")
_VIRTUE_COLORS = ("blue", "green", "purple", "orange", "gold", "indigo")
PILLAR_SPECS: tuple[tuple[str, str, str, str, str], ...] = tuple(
    (slug, v.hanja, v.korean, DOCUMENT_VIRTUE_NAMES[v.key], color)
    for slug, v, color in zip(_VIRTUE_SLUGS, VIRTUE_CONTRACT, _VIRTUE_COLORS, strict=True)
)

# PILLAR_SPECS colour name -> (light-surface hex, dark-surface hex), kept
# byte-identical to the literal `.name {{ --accent:L; --accent:light-dark(L,D) }}`
# rules in the CSS blocks below. Two values are required, not stylistic: a
# single hex cannot clear WCAG AA as text on both a near-white card and a
# near-black one. tests/test_virtue_colors_ssot.py parses the CSS literal as
# the SSOT (not this dict) and recomputes the contrast of both values against
# the surfaces it also parses, so a later surface change re-runs the check.
_VIRTUE_ACCENT_HEX: dict[str, tuple[str, str]] = {
    "blue": ("#2563eb", "#4f81ef"),
    "green": ("#04825b", "#059b6c"),
    "purple": ("#7c3aed", "#9e6df2"),
    "orange": ("#c84b0a", "#ea580c"),
    "gold": ("#986803", "#ca8a04"),
    "indigo": ("#4f46e5", "#7e77ec"),
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
# row-label column plus five equal evidence columns, each wide enough for a handful of
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


def _provenance_readout(evidence: dict[str, Any]) -> tuple[str, str]:
    """`(readout value, banner html)` for the measurement's own origin.

    A panel that reports gate results without saying which build produced them
    is asking to be believed. The readout answers that in every state; the
    banner appears only when the answer invalidates the numbers beside it.
    """
    record = evidence.get("provenance")
    if not isinstance(record, dict):
        return "UNOBSERVED", (
            '<p class="provenance-alert">Measurement origin UNOBSERVED — this panel '
            "cannot say which HyoDo produced the readings below.</p>"
        )
    relation = str(record.get("relation", "SOURCE_UNOBSERVED"))
    validity = str(record.get("validity", "UNOBSERVED"))
    commit = str(record.get("target_commit") or "")[:8] or "no commit"
    if validity == "OBSERVED":
        value = "EXTERNAL" if relation == "EXTERNAL_TARGET" else f"SELF {commit}"
        return value, ""
    if validity == "MISMATCH":
        tool = str(record.get("tool_commit") or "")[:8] or "unknown"
        return "MISMATCH", (
            '<p class="provenance-alert">MEASUREMENT MISMATCH — the gate results below '
            f"were produced by HyoDo at commit {escape(tool)}, but the target is at "
            f"{escape(commit)}. Same version string, different code. Run "
            "<code>hyodo check</code> for the measuring checkout&rsquo;s path.</p>"
        )
    return "UNOBSERVED", (
        '<p class="provenance-alert">Measurement origin UNOBSERVED — the measuring '
        "code could not be compared with this checkout, so the readings below are "
        "unproven rather than green.</p>"
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
    provenance_value, provenance_banner = _provenance_readout(evidence)
    typecheck = _gate(evidence, "typecheck")
    tests = _gate(evidence, "tests")
    lint = _gate(evidence, "lint_format")
    safety = evidence.get("safety", {})
    risk = safety.get("risk_score")
    risk_display = f"{risk}/100" if isinstance(risk, int | float) else "Not measured"
    safety_source = str(safety.get("source", "Not recorded"))
    findings = safety.get("findings", [])
    high = sum(1 for finding in findings if finding.get("severity") == "high")
    measured_value = evidence.get("measured_at")
    measured_at = str(measured_value) if measured_value is not None else "Not measured"
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
.instrument-strip {{ display:grid; grid-template-columns:1.5fr repeat(4,1fr); border-bottom:1px solid var(--line); margin:0 0 18px }}
.provenance-alert {{ margin:0 0 18px; padding:12px 14px; border:2px solid var(--line); background:var(--surface); font:700 .82rem/1.45 var(--mono) }}
.provenance-alert code {{ font:inherit }}
.readout {{ min-height:96px; padding:14px 15px 12px; border-left:1px solid var(--line) }} .readout:first-child {{ border-left:0 }}
.readout-label {{ color:var(--muted); display:block; margin-bottom:11px }} .readout-value {{ display:block; font:800 clamp(1.05rem,2vw,1.5rem)/1 var(--mono); letter-spacing:-.06em; overflow-wrap:anywhere }} .readout-value.signal {{ color:var(--signal) }}
.controls {{ display:flex; flex-wrap:wrap; gap:10px 16px; align-items:center; padding:12px 0 18px; border-bottom:1px solid var(--line) }}
button {{ border:2px solid var(--line); border-radius:0; background:var(--signal); color:#121212; cursor:pointer; font:800 .78rem var(--mono); padding:10px 14px; text-transform:uppercase }} button:disabled {{ cursor:wait; opacity:.55 }} .controls small {{ color:var(--muted); font: .72rem var(--mono) }}
.measurement-status {{ display:inline-block; color:var(--ink); font:700 .72rem var(--mono); text-transform:uppercase }}
.grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; padding-top:18px }} .card {{ position:relative; background:var(--surface); border:2px solid var(--line); border-radius:0; padding:18px; min-height:218px; box-shadow:4px 4px 0 var(--line) }}
.card::before {{ content:""; position:absolute; top:0; left:0; width:28px; height:6px; background:var(--accent) }}
.blue {{ --accent:#2563eb }} .green {{ --accent:#04825b }} .purple {{ --accent:#7c3aed }} .orange {{ --accent:#c84b0a }} .gold {{ --accent:#986803 }} .indigo {{ --accent:#4f46e5 }}
@media (prefers-color-scheme: dark) {{ .blue {{ --accent:#4f81ef }} .green {{ --accent:#059b6c }} .purple {{ --accent:#9e6df2 }} .orange {{ --accent:#ea580c }} .gold {{ --accent:#ca8a04 }} .indigo {{ --accent:#7e77ec }} }}
h2 {{ display:flex; justify-content:space-between; gap:12px; align-items:baseline; margin:0 0 18px; font-size:1rem; letter-spacing:-.02em }} h2 span {{ color:var(--accent); font:800 .82rem var(--mono); letter-spacing:.08em }}
ul {{ list-style:none; padding:0; margin:0 }} li {{ display:grid; grid-template-columns:1fr auto; gap:5px 10px; padding:10px 0; border-top:1px solid var(--line-soft) }} li:first-child {{ border-top:0; padding-top:0 }} li strong {{ font:800 .86rem var(--mono); text-align:right; overflow-wrap:anywhere }} .metric-label {{ font-size:.84rem }} small,.reference {{ grid-column:1/-1; color:var(--muted); font: .68rem/1.35 var(--mono) }} .reference {{ color:var(--accent) }} .not-measured {{ font-size:1.2rem; font-weight:800; margin:20px 0 4px }} .reason {{ color:var(--muted); margin:0; font-size:.8rem }}
*:focus-visible {{ outline:3px solid var(--focus); outline-offset:3px }} @media (prefers-reduced-motion:reduce) {{ * {{ scroll-behavior:auto }} }}
@media (max-width:820px) {{ main {{ padding:18px 14px 40px }} header {{ display:block }} .legend {{ text-align:left; margin-top:18px; max-width:none }} .instrument-strip {{ grid-template-columns:1fr 1fr }} .readout {{ border-top:1px solid var(--line); border-left:1px solid var(--line) }} .readout:nth-child(odd) {{ border-left:0 }} .grid {{ grid-template-columns:1fr }} .card {{ min-height:0 }} }}
</style></head><body><main><header><div><p class="eyebrow">HyoDo / Measurement Console</p><h1>Instrument Panel</h1><p class="meta">TARGET // {escape(target)}<br>MEASURED // {escape(measured_at)}</p></div><p class="legend">Raw evidence only<br>No composite score<br><a href="/graph">Open evidence graph</a> · <a href="/api/evidence">Open evidence JSON</a></p></header><section class="instrument-strip" aria-label="measurement summary"><div class="readout"><span class="readout-label">Signal state</span><strong class="readout-value signal">{escape("MEASURED" if measured_gate_count else "UNOBSERVED")}</strong></div><div class="readout"><span class="readout-label">Gates read</span><strong class="readout-value">{measured_gate_count}/3</strong></div><div class="readout"><span class="readout-label">Refresh mode</span><strong class="readout-value">{escape("AUTO " + str(interval) + "S" if interval else "FIXED")}</strong></div><div class="readout"><span class="readout-label">Receipt scope</span><strong class="readout-value">LOCAL ONLY</strong></div><div class="readout"><span class="readout-label">Measured by</span><strong class="readout-value">{escape(provenance_value)}</strong></div></section>{provenance_banner}<p class="meta">{escape(refresh_mode)}</p><p id="measurement-status" class="measurement-status" aria-live="polite">{escape(refresh_status)}</p>{refresh_control}<div class="grid">{cards}</div></main><script data-measured="{escape(measured_at)}">{POLL_SCRIPT}</script></body></html>"""


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


def _event_detail_payload(node: dict[str, Any]) -> dict[str, Any]:
    """5W1H plus canonical proof fields for the detail panel."""
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
    method_parts = [str(tool[key]) for key in ("name", "method") if tool.get(key)]
    how = " · ".join(method_parts) or "UNOBSERVED"
    if rule_id:
        how = f"{how} · policy rule: {rule_id}"
    raw_verification = node.get("verification")
    verification: dict[str, Any] = raw_verification if isinstance(raw_verification, dict) else {}
    raw_what = verification.get("what")
    what: dict[str, Any] = raw_what if isinstance(raw_what, dict) else {}
    raw_how_view = verification.get("how")
    how_view: dict[str, Any] = raw_how_view if isinstance(raw_how_view, dict) else {}
    who_view = verification.get("who")
    who_view = who_view if isinstance(who_view, dict) else {}
    why_view = verification.get("why")
    why_view = why_view if isinstance(why_view, dict) else {}

    def participant(direction: str) -> str:
        """Display a recorded relationship endpoint without inferring its identity."""
        endpoint = who_view.get(direction)
        if not isinstance(endpoint, dict):
            return "UNOBSERVED"
        return (
            " ".join(str(endpoint[key]) for key in ("actor", "actor_id") if endpoint.get(key))
            or "UNOBSERVED"
        )

    return {
        "who": f"From: {participant('from')} → To: {participant('to')}",
        "intentReview": why_view.get("intent_review") or {},
        "recordedActor": " ".join(str(node[key]) for key in ("actor", "actor_id") if node.get(key))
        or "UNOBSERVED",
        "what": _event_title(node),
        "when": str(node.get("ts") or "not recorded"),
        "where": where,
        "why": "UNOBSERVED · actor intent is not recorded by this view",
        "policyRationale": str(policy.get("reason"))
        if isinstance(policy, dict) and policy.get("reason")
        else "not recorded",
        "how": how,
        "recordedDecision": what.get("decision") or node.get("decision") or "UNOBSERVED",
        "presentableDecision": what.get("decision_presentable") or "UNOBSERVED",
        "columns": list(verification.get("columns") or []),
        "runCoverage": dict(verification.get("run_coverage") or {}),
        "stepIndex": verification.get("when", {}).get("step_index")
        if isinstance(verification.get("when"), dict)
        else node.get("step_index"),
        "causalParentCount": len(verification.get("causal_parents") or []),
        "evidenceRefCount": len(verification.get("evidence_refs") or []),
        "outputDigest": how_view.get("output_digest") or "UNOBSERVED",
        "missing": list(verification.get("missing") or []),
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
    light, dark = _VIRTUE_ACCENT_HEX[_PILLAR_FULLNAME_TO_ACCENT[best_pillar]]
    # This tint is inlined into an element's style attribute, where a media
    # query cannot reach it, so the theme choice has to travel with the value.
    return f"light-dark({light},{dark})"


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

    Brief finding 1: one grid whose columns are the five evidence columns and
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
                    f'fill="none" stroke="{EDGE_COLORS["parent"]}" stroke-width="1.5" '
                    'marker-end="url(#daw-arrow-parent)"/>'
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
                    'stroke-dasharray="4 3" marker-end="url(#daw-arrow-evidence)"/>'
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
                'stroke-width="2" marker-end="url(#daw-arrow-broken)"/>'
            )
            broken_count += 1

    return (
        f'<svg id="{escape(overlay_id)}" class="edge-overlay" role="img" aria-hidden="true" '
        f'data-parent-edges="{parent_count}" data-evidence-edges="{evidence_count}" '
        f'data-broken-edges="{broken_count}" data-offgrid-edges="{offgrid_count}">'
        '<defs><marker id="daw-arrow-parent" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" '
        f'fill="{EDGE_COLORS["parent"]}"/></marker><marker id="daw-arrow-evidence" viewBox="0 0 10 10" '
        'refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path '
        f'd="M 0 0 L 10 5 L 0 10 z" fill="{EDGE_COLORS["evidence"]}"/></marker><marker '
        'id="daw-arrow-broken" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" '
        'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" '
        f'fill="{EDGE_COLORS["broken"]}"/></marker></defs>' + "".join(parts) + "</svg>"
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
        f'<h2 id="col-{escape(key)}" class="{escape(color)}">'
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
    """Render one grid row (row-header cell + five evidence-column cells).

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


#: The graph already decides an actor lineage's role. This maps that decided
#: role onto the four display lanes the timeline draws, and it is the only
#: place the two vocabularies are allowed to meet. `orchestrator` lands in the
#: `planner` lane because that lane means "spawned other work", which is
#: exactly what `build_actor_rows` observes to call a row an orchestrator.
_DAW_LANE_BY_ROLE: dict[str, str] = {
    "human": "human",
    "orchestrator": "planner",
    "reviewer": "reviewer",
    "worker": "agent",
}


def _role_by_event(graph: dict[str, Any]) -> dict[str, str]:
    """Index the graph's own per-lineage ``role`` by event id.

    ``build_actor_rows`` already derives each actor lineage's role from the
    graph, and ``build_report_graph`` already attaches the result as ``rows``
    on every payload. Reading it here keeps one decision in one place. An older
    payload without ``rows`` yields an empty index, and the caller falls back
    to the coarse ``actor`` reading rather than inventing a role locally.
    """
    rows = graph.get("rows")
    if not isinstance(rows, dict):
        return {}
    table = rows.get("rows")
    if not isinstance(table, dict):
        return {}
    index: dict[str, str] = {}
    for row in table.values():
        if not isinstance(row, dict):
            continue
        role = row.get("role")
        if not isinstance(role, str):
            continue
        for event_id in row.get("events") or []:
            if isinstance(event_id, str):
                index[event_id] = role
    return index


def _daw_track(node: dict[str, Any], role_by_event: dict[str, str] | None = None) -> str:
    """Choose a display-only DAW lane for one event.

    Prefers the role the graph already decided for this event's actor
    lineage (`build_actor_rows`, surfaced as `graph["rows"]`). That decision
    reads causal lineage and evidence citation; re-deriving it here from the
    coarse ``actor`` field alone would be a second, weaker answer to a question
    already answered, and two answers is how a viewer starts disagreeing with
    its own producer.

    The fallback below runs only when no role was observed for this event —
    an older payload, or a graph assembled without rows. It is deliberately
    coarse: it reports what ``actor`` says and nothing more. It does not read
    the event id or the tool name, because a name is what something is called,
    not what it did.
    """
    role = (role_by_event or {}).get(str(node.get("id") or ""))
    if role is not None:
        return _DAW_LANE_BY_ROLE.get(role, "agent")
    actor = str(node.get("actor") or "").lower()
    if actor == "human":
        return "human"
    if actor == "hyodo":
        return "reviewer"
    if actor == "agent":
        return "agent"
    return "planner"


def _daw_event_label(node: dict[str, Any]) -> str:
    """Compact prototype-style label with measured signal still visible."""
    node_id = str(node.get("id") or "").lower()
    kind = str(node.get("kind") or "event").lower()
    suffix = "call" if kind == "tool_call" else "result"
    if "parallel" in node_id:
        branch = next((branch for branch in ("a", "b") if f"parallel-{branch}" in node_id), "?")
        return f"{branch.upper()} {'call' if suffix == 'call' else 'res'}"
    if "join" in node_id:
        return f"dag join / {suffix}"
    if "serial" in node_id:
        return f"serial / {suffix}"
    if "retry-1" in node_id or "retry-call-1" in node_id or "retry-result-1" in node_id:
        return f"retry 1 / {suffix}"
    if "rework" in node_id or "retry-call-2" in node_id or "retry-result-2" in node_id:
        return f"rework / {suffix}"
    if "wait" in node_id:
        return f"wait / {suffix}"
    if "unresolved" in node_id:
        return "unresolved"
    if "human" in node_id:
        return "approval"
    return _event_label(node)


#: What each `missing` bucket means, in one line, for a reader who has not
#: read the schema. The wording says what to fix, because a gap nobody knows
#: how to close is just a number.
_MISSING_BUCKET_MEANING: tuple[tuple[str, str, str], ...] = (
    (
        "unresolved_refs",
        "Citations pointing at no recorded event",
        "Something was cited as evidence and the ledger has no such event.",
    ),
    (
        "cross_run_refs",
        "Parents recorded under a different run",
        "A causal parent exists, but in another run, so the chain is not local.",
    ),
    (
        "calls_without_result",
        "Tool calls with no recorded effect",
        "The call was recorded. Nothing downstream ever cited it as a parent.",
    ),
    (
        "runs_without_intent",
        "Runs with no recorded human intent",
        "Work was recorded without the request it answers. Fix the recording.",
    ),
    (
        "unmeasured_events",
        "Events that recorded nothing readable",
        "No paths, urls, method, rule, or digest. Fix the recording.",
    ),
    (
        "unclassified_events",
        "Evidence the mapping table has no row for",
        "The event did record evidence. Fix the table, never by tool name.",
    ),
)

#: How many example ids to name per bucket. Enough to start looking, few
#: enough that the panel stays readable when a bucket holds thousands.
_MISSING_SAMPLE_LIMIT = 3


def _missing_sample(entries: list[Any]) -> list[str]:
    """Return up to `_MISSING_SAMPLE_LIMIT` readable ids from one bucket."""
    sample: list[str] = []
    for entry in entries[:_MISSING_SAMPLE_LIMIT]:
        if isinstance(entry, str):
            sample.append(entry)
        elif isinstance(entry, dict):
            label = entry.get("ref") or entry.get("event_id") or entry.get("parent_event_id")
            if isinstance(label, str):
                sample.append(label)
    return sample


def _unique_text(values: list[Any], *, empty: str = "UNOBSERVED") -> str:
    """Display one canonical value without collapsing conflicting values."""
    observed = sorted({value for value in values if isinstance(value, str) and value})
    if not observed:
        return empty
    return observed[0] if len(observed) == 1 else "MULTIPLE"


def _view_run_id(view: dict[str, Any]) -> str:
    """Return the one run id already present in the verification view."""
    run_ids = [
        event.get("why", {}).get("run_id")
        for event in (view.get("events") or {}).values()
        if isinstance(event, dict) and isinstance(event.get("why"), dict)
    ]
    return _unique_text(run_ids)


def _verification_stage_state(view: dict[str, Any], stage: str) -> str:
    """Project one rail label from existing verification-view facts only."""
    events = [event for event in (view.get("events") or {}).values() if isinstance(event, dict)]
    kinds = [
        event.get("what", {}).get("kind") for event in events if isinstance(event.get("what"), dict)
    ]
    raw_missing = view.get("missing")
    missing: dict[str, Any] = raw_missing if isinstance(raw_missing, dict) else {}
    if stage == "intent":
        if "prompt" not in kinds:
            return "UNOBSERVED"
        return "UNOBSERVED" if missing.get("runs_without_intent") else "OBSERVED"
    if stage == "action":
        return "OBSERVED" if "tool_call" in kinds else "UNOBSERVED"
    if stage == "result":
        if "tool_result" not in kinds:
            return "UNOBSERVED"
        return "PARTIAL" if missing.get("calls_without_result") else "OBSERVED"
    if stage == "evidence":
        return "OBSERVED" if view.get("edges_evidence") else "UNOBSERVED"
    if stage == "decision":
        decisions = [
            entry.get("decision_presentable")
            for entries in (view.get("decisions_by_run") or {}).values()
            if isinstance(entries, list)
            for entry in entries
            if isinstance(entry, dict)
        ]
        return _unique_text(decisions)
    return "UNOBSERVED"


def _render_verification_header(view: dict[str, Any]) -> str:
    """Render the canonical case/status strip without inventing authority."""
    events = [event for event in (view.get("events") or {}).values() if isinstance(event, dict)]
    recorded = [
        event.get("what", {}).get("decision")
        for event in events
        if isinstance(event.get("what"), dict) and event.get("what", {}).get("decision") is not None
    ]
    presentable = [
        event.get("what", {}).get("decision_presentable")
        for event in events
        if isinstance(event.get("what"), dict)
        and event.get("what", {}).get("decision_presentable") is not None
    ]
    raw_missing = view.get("missing")
    missing: dict[str, Any] = raw_missing if isinstance(raw_missing, dict) else {}
    gap_count = sum(len(entries) for entries in missing.values() if isinstance(entries, list))
    status = str(view.get("status") or "UNOBSERVED")
    authority = str(view.get("authority") or "UNOBSERVED")
    return (
        '<section class="verification-header" aria-label="verification status">'
        '<div class="verification-case">'
        f'<span class="verification-kicker">CASE</span><strong>{escape(_view_run_id(view))}</strong>'
        f'<span class="verification-status" data-status="{escape(status)}">{escape(status)}</span>'
        f'<span class="verification-gaps">{gap_count} GAP{"S" if gap_count != 1 else ""}</span>'
        "</div>"
        '<div class="verification-facts">'
        f'<span>Recorded: <b data-recorded-decision="{escape(_unique_text(recorded))}">{escape(_unique_text(recorded))}</b></span>'
        f'<span>Presentable: <b data-presentable-decision="{escape(_unique_text(presentable))}">{escape(_unique_text(presentable))}</b></span>'
        f"<span>Authority: <b>{escape(authority)}</b></span>"
        "</div></section>"
    )


def _render_verification_rail(view: dict[str, Any]) -> str:
    """Render the five-stage rail supported by verification-view/v0."""
    stages = (
        ("intent", "INTENT"),
        ("action", "ACTION"),
        ("result", "RESULT"),
        ("evidence", "EVIDENCE"),
        ("decision", "DECISION"),
    )
    items: list[str] = []
    for index, (key, label) in enumerate(stages):
        state = _verification_stage_state(view, key)
        connector = (
            '<span class="verification-rail-link" aria-hidden="true">→</span>' if index else ""
        )
        items.append(
            f'{connector}<div class="verification-rail-stage" data-stage="{key}" data-state="{escape(state)}">'
            f'<span class="verification-rail-mark" aria-hidden="true"></span><b>{label}</b>'
            f"<small>{escape(state)}</small></div>"
        )
    return (
        '<section class="verification-rail" aria-label="verification rail">'
        '<div class="verification-rail-head"><span>VERIFICATION RAIL</span>'
        "<small>canonical facts only</small></div>"
        f'<div class="verification-rail-track">{"".join(items)}</div></section>'
    )


def _render_missing_panel(graph: dict[str, Any], root: Path | None = None) -> str:
    """Render "what is missing" from the verification view's own counts.

    Every number here is already in the graph; this reads
    `build_verification_view(...)["missing"]` rather than recounting, so the
    panel and the JSON route can never disagree about the same ledger.

    The panel states gaps. It does not rank them, score them, or say what they
    block, because the graph records none of that. Naming an unread gap is the
    whole point: a reader should not have to page through the ledger to learn
    that nothing downstream ever cited a call.
    """
    view = build_verification_view(graph, root=root)
    missing = view["missing"]
    rows: list[str] = []
    total = 0
    for key, title, meaning in _MISSING_BUCKET_MEANING:
        entries = missing.get(key) or []
        count = len(entries)
        if not count:
            continue
        total += count
        sample = _missing_sample(entries)
        sample_html = (
            f'<p class="missing-sample">{escape(", ".join(sample))}'
            + (f" and {count - len(sample)} more" if count > len(sample) else "")
            + "</p>"
            if sample
            else ""
        )
        rows.append(
            f'<li class="missing-item" data-missing-bucket="{escape(key)}" '
            f'data-missing-count="{count}">'
            f'<p class="missing-title"><b>{escape(title)}</b> '
            f'<span class="missing-count">{count}</span></p>'
            f'<p class="missing-meaning">{escape(meaning)}</p>{sample_html}</li>'
        )

    if not rows:
        # An empty ledger has no gaps and no evidence either. Saying "nothing
        # is missing" about nothing observed would be the false green this
        # whole surface exists to prevent.
        body = (
            '<p class="missing-none">No recorded events, so nothing is missing '
            "and nothing is proven.</p>"
            if not view["events"]
            else '<p class="missing-none">Every recorded event resolved. This is '
            "not a pass; it is the absence of these particular gaps.</p>"
        )
    else:
        body = f'<ol class="missing-list">{"".join(rows)}</ol>'

    return (
        '<section class="missing-wrap" aria-label="what is missing" '
        f'data-missing-total="{total}">'
        '<div class="missing-head"><p class="missing-kicker">EVIDENCE GAPS</p>'
        "<h2>What is missing</h2></div>"
        f"{body}"
        '<p class="missing-boundary">Observation only. A gap is not a failure, '
        "and closing one authorizes nothing.</p></section>"
    )


def _render_daw_timeline(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    edge_overlay: str = "",
    role_by_event: dict[str, str] | None = None,
    lanes: list[dict[str, Any]] | None = None,
) -> tuple[str, dict[str, tuple[int, int, int]]]:
    """Render the user-facing DAW timeline and return edge anchor membership.

    *role_by_event* is `_role_by_event(graph)`: the role the graph already
    decided for each event's actor lineage. Passing it makes the lanes agree
    with `graph["rows"]` instead of re-deriving a weaker answer here.
    """
    valid_nodes = [node for node in nodes if isinstance(node.get("id"), str)]

    # Per-run step indices reset; they cannot serve as a shared time axis.
    def observed_time(node: dict[str, Any]) -> datetime | None:
        """Normalize timezone-aware event time; leave missing or ambiguous time unknown."""
        raw = node.get("ts")
        if not isinstance(raw, str):
            return None
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None

    times = {str(node["id"]): observed_time(node) for node in valid_nodes}
    observed = sorted({value for value in times.values() if value is not None})
    column_by_time = {value: index for index, value in enumerate(observed)}
    column_by_event: dict[str, int] = {}
    step_timestamps = {
        index: value.strftime("%m-%d %H:%M:%S UTC") for value, index in column_by_time.items()
    }
    next_unknown = len(observed)
    for node in valid_nodes:
        event_id = str(node["id"])
        value = times[event_id]
        if value is None:
            column_by_event[event_id] = next_unknown
            step_timestamps[next_unknown] = "TIME UNOBSERVED"
            next_unknown += 1
        else:
            column_by_event[event_id] = column_by_time[value]
    columns = max(1, next_unknown)
    run_ids = {str(node["run_id"]) for node in valid_nodes if node.get("run_id")}
    run_id = next(iter(run_ids)) if len(run_ids) == 1 else f"{len(run_ids)} recorded runs"
    track_order = ["human", "planner", "agent", "reviewer"]
    # The agent lane no longer claims the role is unobserved when the graph
    # observed one. Saying "unobserved" about something already measured is
    # the same error in the other direction.
    roles_observed = bool(role_by_event)
    track_labels = {
        "human": "Human",
        "planner": "Planner",
        "agent": "Agent / worker" if roles_observed else "Agent / role unobserved",
        "reviewer": "Reviewer",
    }
    participant_by_event: dict[str, str] = {}
    track_styles = {key: key for key in track_order}
    track_roles: dict[str, str] = {}
    if lanes:
        track_order = []
        track_labels = {}
        track_styles = {}
        for lane in lanes:
            key = str(lane["lane_id"])
            track_order.append(key)
            track_labels[key] = _display_row_label(key, str(lane.get("label") or key))
            role = lane.get("role")
            track_roles[key] = str(role) if role else "role unobserved"
            track_styles[key] = _DAW_LANE_BY_ROLE.get(str(role), "agent")
            for event_id in lane.get("events") or []:
                participant_by_event[str(event_id)] = key
        if any(str(node["id"]) not in participant_by_event for node in valid_nodes):
            track_order.append("unattributed")
            track_labels["unattributed"] = "Participant unobserved"
            track_styles["unattributed"] = "agent"
    buckets: dict[tuple[str, int], list[dict[str, Any]]] = {}
    anchors: dict[str, tuple[int, int, int]] = {}
    for node in sorted(
        valid_nodes,
        key=lambda item: (
            item.get("step_index") if isinstance(item.get("step_index"), int) else 0,
            str(item.get("ts", "")),
        ),
    ):
        track = (
            participant_by_event.get(str(node["id"]), "unattributed")
            if lanes
            else _daw_track(node, role_by_event)
        )
        step = column_by_event[str(node["id"])]
        buckets.setdefault((track, step), []).append(node)

    # Canonical participant lanes retain identity even when roles match.
    # The legacy fallback is used only when the producer supplied no lanes.
    visible_tracks = track_order
    parts = [
        '<section class="daw-console" aria-label="Evidence session timeline">',
        f'<div class="daw-sessionbar"><div><span>EVIDENCE CONSOLE</span><strong>SESSION / {escape(run_id)}</strong></div>'
        f'<div><span class="session-state">■ STATIC VIEW</span><span>TIME <b>EARLIER → LATER</b></span>'
        '<span class="session-boundary">LOCAL DATA / NOT SEALED</span></div></div>',
        '<div class="daw-console-head"><div><span class="daw-kicker">EVIDENCE SESSION / LIVE READBACK</span>'
        '<h2>Run timeline</h2></div><div class="daw-legend"><span><i class="legend-call"></i>CALL</span>'
        '<span><i class="legend-result"></i>RESULT</span><span><i class="legend-human"></i>HUMAN</span></div></div>',
        f'<div class="daw-rows" style="--daw-columns:{columns}">',
        '<div class="daw-ruler"><div class="daw-track-label">TRACK / SIGNAL</div>'
        + "".join(
            f'<div class="daw-step">t{index}<small>{escape(step_timestamps.get(index, "UNOBSERVED"))}</small></div>'
            for index in range(columns)
        )
        + "</div>",
    ]
    for row_index, track in enumerate(visible_tracks):
        label = track_labels[track]
        role_label = track_roles.get(track)
        role_html = (
            f'<span class="participant-role">{escape(role_label)}</span>' if role_label else ""
        )
        is_empty_track = not any(buckets.get((track, step)) for step in range(columns))
        row_class = "daw-row daw-row-empty" if is_empty_track else "daw-row"
        empty_state = '<span class="track-empty-state">UNOBSERVED</span>' if is_empty_track else ""
        parts.append(
            f'<div class="{row_class}" data-daw-track="{escape(track)}"><div class="daw-track-label">'
            f'<span class="track-led track-{escape(track_styles[track])}"></span>'
            f'<span class="participant-label">{escape(label)}{role_html}</span>{empty_state}'
            f"<small>{row_index:02d}</small></div>"
        )
        for step in sorted(index for lane, index in buckets if lane == track):
            events = buckets[(track, step)]
            is_parallel_cluster = len(events) > 1 and all(
                "parallel-" in str(node["id"]).lower() for node in events
            )
            cluster_class = " daw-cluster" if len(events) > 1 else ""
            parallel_attr = ' data-parallel-cluster="true"' if is_parallel_cluster else ""
            parts.append(
                f'<div class="daw-cell{cluster_class}" data-event-count="{len(events)}"'
                f' style="grid-column:{step + 2}"{parallel_attr}>'
            )
            if is_parallel_cluster:
                parts.append(
                    '<span class="daw-cluster-label" aria-hidden="true">PARALLEL / A + B</span>'
                )
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
    sections 2-4, 9-10): the five fixed evidence columns in spec order, the
    Eternity continuity indicator, actor rows with collapsible sub-agent nesting, an unclassified
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
    raw_node_list: list[dict[str, Any]] = raw_nodes if isinstance(raw_nodes, list) else []
    edges: list[dict[str, Any]] = raw_edges if isinstance(raw_edges, list) else []
    missions = graph.get("missions") if isinstance(graph.get("missions"), dict) else {}
    effective_root = root
    if effective_root is None:
        graph_root = graph.get("root")
        effective_root = Path(graph_root) if isinstance(graph_root, str) and graph_root else None
    verification_view = build_verification_view(graph, root=effective_root)
    evidence_refs_by_target: dict[str, list[str]] = {}
    for edge in verification_view.get("edges_evidence") or []:
        if isinstance(edge, dict) and isinstance(edge.get("target"), str):
            source = edge.get("source")
            if isinstance(source, str):
                evidence_refs_by_target.setdefault(edge["target"], []).append(source)
    missing_by_event: dict[str, list[str]] = {}
    missing_view = verification_view.get("missing")
    if isinstance(missing_view, dict):
        for bucket, entries in missing_view.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                event_id = (
                    entry
                    if isinstance(entry, str)
                    else entry.get("event_id")
                    if isinstance(entry, dict)
                    else None
                )
                if isinstance(event_id, str):
                    missing_by_event.setdefault(event_id, []).append(str(bucket))
    nodes = []
    for node in raw_node_list:
        node_id = node.get("id")
        verification = (
            verification_view.get("events", {}).get(node_id) if isinstance(node_id, str) else None
        )
        if isinstance(verification, dict):
            verification = dict(verification)
            verification["evidence_refs"] = evidence_refs_by_target.get(str(node_id), [])
            verification["missing"] = missing_by_event.get(str(node_id), [])
            verification["run_coverage"] = verification_view.get("coverage", {})
        nodes.append({**node, "verification": verification or {}})
    node_by_id: dict[str, dict[str, Any]] = {
        node["id"]: node for node in nodes if isinstance(node.get("id"), str)
    }
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

    missing_html = _render_missing_panel(graph, effective_root)
    daw_roles = _role_by_event(graph)
    _daw_preview, daw_anchors = _render_daw_timeline(
        nodes, edges, role_by_event=daw_roles, lanes=verification_view["lanes"]
    )
    daw_edge_overlay = _render_edge_overlay(graph, daw_anchors, overlay_id="daw-edge-overlay")
    daw_html, _ = _render_daw_timeline(
        nodes, edges, daw_edge_overlay, daw_roles, verification_view["lanes"]
    )

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

    # Two gutters, because they are two different problems. `UNCLASSIFIED`
    # means the mapping table had no row for evidence the event really did
    # record -- fix the table. `UNMEASURED` means the event recorded
    # nothing to classify -- fix the recording. Merging them hides which
    # one you are looking at, and makes a recording gap look like an
    # argument for a tool-name row.
    def _gutter(sentinel: str, heading: str, caption: str) -> str:
        node_ids = [node_id for node_id, columns in assignments.items() if columns == [sentinel]]
        if not node_ids:
            return ""
        cells = "".join(_event_button(node_by_id[node_id]) for node_id in node_ids)
        return (
            f'<section class="gutter" data-gutter-count="{len(node_ids)}"'
            f' aria-label="{escape(heading)} events">'
            f'<h2>{escape(heading)} <span class="gutter-count">{len(node_ids)}</span></h2>'
            f'<p class="gutter-note">{escape(caption)}</p>'
            f'<div class="cells">{cells}</div>'
            "</section>"
        )

    gutter_html = _gutter(
        UNCLASSIFIED,
        "Unclassified",
        "Evidence was recorded; no mapping row matched it.",
    ) + _gutter(
        UNMEASURED,
        "Unmeasured",
        "Nothing was recorded on these events to classify.",
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
.blue {{ --accent:#2563eb }} .green {{ --accent:#04825b }} .purple {{ --accent:#7c3aed }} .orange {{ --accent:#c84b0a }} .gold {{ --accent:#986803 }} .indigo {{ --accent:#4f46e5 }}
@media (prefers-color-scheme: dark) {{ .blue {{ --accent:#4f81ef }} .green {{ --accent:#059b6c }} .purple {{ --accent:#9e6df2 }} .orange {{ --accent:#ea580c }} .gold {{ --accent:#ca8a04 }} .indigo {{ --accent:#7e77ec }} }}
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
.edge.edge-active {{ stroke-width:3 }}
.cells {{ display:flex; flex-wrap:wrap; gap:6px }}
.gutter {{ margin-bottom:18px }} .gutter h2 {{ font-size:.95rem; margin-bottom:2px }}
/* Not var(--muted): this viewer's token block is the pre-redesign light
   palette, while `body` below paints a #0f0e12 ground with a literal.
   --muted (#5b6475) lands at 3.23:1 there. #aaa9ab measures 8.22:1 on
   the ground these actually render against. */
.gutter-count {{ font-family:var(--mono); font-weight:400; color:#aaa9ab }}
.gutter-note {{ margin:0 0 8px; color:#aaa9ab; font-size:.76rem }}
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
/* TE hardware deck: flat anodised surfaces, sharp displays, and only the
   status colours that distinguish evidence. No bloom or decorative shadow. */
body {{ background:#0f0e12; color:#f5f5f5; font-family:"Helvetica Neue",Helvetica,Arial,sans-serif; font-weight:300 }}
main {{ max-width:1480px; padding:28px 28px 56px }}
header {{ border-bottom:1px solid #3a393d; padding-bottom:18px; margin-bottom:20px }}
h1 {{ letter-spacing:.035em; text-transform:uppercase; font-size:clamp(1.5rem,3vw,2.5rem); font-weight:300 }}
.meta, .meta a {{ color:#aaa9ab }}
.unobserved-notice {{ border-radius:0; background:#251716; color:#f5b5ad; border:1px solid #f05a24 }}
.verification-header {{ display:flex; justify-content:space-between; gap:22px; align-items:center; border:1px solid #57565a; border-left:3px solid #f05a24; background:#17161a; padding:13px 15px; margin:4px 0 8px; min-width:980px }}
.verification-case, .verification-facts {{ display:flex; align-items:baseline; gap:12px; flex-wrap:wrap }}
.verification-kicker, .verification-rail-head span {{ color:#aaa9ab; font:600 .66rem/1.4 ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.16em }}
.verification-case strong {{ color:#f5f5f5; font-size:1.05rem; font-weight:400; letter-spacing:.08em }}
.verification-status {{ color:#fab413; font:600 .72rem/1.4 ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.1em }}
.verification-gaps {{ color:#aaa9ab; font:600 .64rem/1.4 ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.1em }}
.verification-facts {{ color:#aaa9ab; font-size:.72rem; letter-spacing:.04em }}
.verification-facts b {{ color:#f5f5f5; font-weight:400 }}
.verification-facts b[data-presentable-decision="UNOBSERVED"] {{ color:#aaa9ab }}
.verification-rail {{ overflow:auto; border:1px solid #3a393d; background:#121116; padding:11px 15px 13px; margin:0 0 12px; min-width:980px }}
.verification-rail-head {{ display:flex; justify-content:space-between; margin-bottom:10px }}
.verification-rail-head small {{ color:#747378; font-size:.64rem; letter-spacing:.08em }}
.verification-rail-track {{ display:flex; align-items:stretch; min-width:760px }}
.verification-rail-stage {{ display:grid; grid-template-columns:auto 1fr; grid-template-rows:auto auto; column-gap:8px; align-items:center; min-width:128px; color:#aaa9ab }}
.verification-rail-stage b {{ color:#f5f5f5; font-size:.66rem; font-weight:400; letter-spacing:.09em }}
.verification-rail-stage small {{ grid-column:2; color:#747378; font:600 .58rem/1.3 ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.08em }}
.verification-rail-mark {{ grid-row:1 / span 2; width:11px; height:11px; border:1px solid #747378; border-radius:50%; background:transparent }}
.verification-rail-stage[data-state="OBSERVED"] .verification-rail-mark {{ border-color:#7fc86a; background:#7fc86a }}
.verification-rail-stage[data-state="PARTIAL"] .verification-rail-mark {{ border-color:#fab413; background:linear-gradient(90deg,#fab413 50%,transparent 50%) }}
.verification-rail-stage[data-state="ALLOW"] .verification-rail-mark {{ border-color:#7fc86a; background:#7fc86a }}
.verification-rail-stage[data-state="DENY"] .verification-rail-mark {{ border-color:#f05a24; background:#f05a24 }}
.verification-rail-link {{ align-self:center; color:#57565a; padding:0 7px; font-size:1.1rem }}
.daw-console {{ position:relative; overflow:auto; border:1px solid #57565a; background:#17161a; padding:14px; margin:4px 0 16px }}
.daw-sessionbar {{ display:flex; justify-content:space-between; gap:20px; border:1px solid #3a393d; border-left:3px solid #f05a24; padding:11px 12px; margin-bottom:14px; min-width:980px; color:#d1d0d2; font-size:.68rem; letter-spacing:.1em }}
.daw-sessionbar div {{ display:flex; gap:18px; align-items:center }} .daw-sessionbar span {{ color:#969598 }} .daw-sessionbar strong {{ color:#f5f5f5; letter-spacing:.12em; font-weight:300 }}
.daw-sessionbar b, .session-boundary {{ color:#fab413 !important }} .session-state {{ color:#f05a24 !important }}
.daw-console-head {{ display:flex; justify-content:space-between; align-items:end; gap:20px; border-bottom:1px solid #3a393d; padding:2px 0 14px; min-width:980px }}
.daw-kicker {{ color:#7fc86a; font-size:.68rem; letter-spacing:.18em }}
.daw-console h2 {{ margin:5px 0 0; font-size:1.25rem; letter-spacing:.08em; text-transform:uppercase; font-weight:300 }}
.daw-legend {{ display:flex; gap:14px; color:#aaa9ab; font-size:.68rem; letter-spacing:.1em }}
.daw-legend i {{ display:inline-block; width:7px; height:7px; margin-right:5px; background:#7fc86a }}
.daw-legend .legend-result {{ background:#fab413 }}
.daw-legend .legend-human {{ background:#f05a24 }}
.missing-wrap {{ margin:28px 0 0; padding:18px 20px; border:1px solid #2b3238; border-radius:10px; background:#12161b }}
.missing-head {{ display:flex; align-items:baseline; gap:12px; flex-wrap:wrap }}
.missing-kicker {{ margin:0; font:600 11px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.14em; color:#8b929a }}
.missing-head h2 {{ margin:0; font-size:18px }}
.missing-list {{ margin:14px 0 0; padding-left:22px }}
.missing-item {{ margin:0 0 14px }}
.missing-title {{ margin:0; font-size:14px }}
.missing-count {{ display:inline-block; min-width:2.2em; margin-left:8px; padding:1px 7px; border-radius:999px; background:#1f262d; font:600 12px/1.6 ui-monospace,SFMono-Regular,Consolas,monospace; text-align:center }}
.missing-meaning {{ margin:3px 0 0; color:#b9c0c7; font-size:13px }}
.missing-sample {{ margin:3px 0 0; color:#8b929a; font:12px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace; overflow-wrap:anywhere }}
.missing-none {{ margin:12px 0 0; color:#b9c0c7; font-size:13px }}
.missing-boundary {{ margin:14px 0 0; padding-top:12px; border-top:1px solid #232a31; color:#8b929a; font-size:12px }}
.daw-rows {{ position:relative; min-width:1060px; padding-top:14px }}
.daw-ruler, .daw-row {{ display:grid; grid-template-columns:190px repeat(var(--daw-columns), minmax(104px,1fr)); min-width:1060px }}
.daw-ruler {{ color:#aaa9ab; font-size:.68rem; letter-spacing:.1em; border-bottom:1px solid #57565a }}
.daw-step {{ padding:0 8px 8px; border-left:1px solid #302f33; font-variant-numeric:tabular-nums }}
.daw-step small {{ display:block; color:#747378; margin-top:3px }}
.daw-track-label {{ position:sticky; left:0; z-index:4; display:flex; align-items:center; gap:7px; padding:0 10px; color:#f5f5f5; font-size:.69rem; letter-spacing:.1em; border-right:1px solid #57565a; background:#121116 }}
.daw-track-label small {{ margin-left:auto; color:#747378 }}
.participant-label {{ overflow-wrap:anywhere }}
.participant-role {{ display:block; color:#8b929a; font-size:.6rem; margin-top:4px }}
.track-empty-state {{ color:#747378; font-size:.54rem; letter-spacing:.12em }}
.daw-row {{ min-height:78px; margin:8px 0; border:1px solid #3a393d; border-radius:0; background:#121116; overflow:visible }}
.daw-row.daw-row-empty {{ min-height:36px; margin:4px 0; border-color:#302f33; background:#101015 }}
.daw-row.daw-row-empty .daw-cell {{ min-height:34px; padding:0; background:#101015 }}
.daw-row.daw-row-empty .daw-track-label {{ color:#aaa9ab }}
.daw-cell {{ min-height:78px; padding:7px 5px; border-left:1px solid #302f33; display:flex; flex-direction:column; gap:4px; justify-content:center }}
.daw-cell.daw-cluster {{ display:grid; grid-template-columns:minmax(0,1fr); align-content:center; gap:7px; padding:9px 7px; background:#0f0e12; box-shadow:inset 0 0 0 1px #3a393d }}
.daw-cell.daw-cluster[data-event-count="4"] {{ grid-template-columns:repeat(2,minmax(0,1fr)) }}
.daw-cell.daw-cluster[data-parallel-cluster="true"] {{ position:relative; padding-top:23px; border:1px solid #0071bb; background:#15151a }}
.daw-cluster-label {{ position:absolute; top:5px; left:7px; color:#72bfe9; font-size:.52rem; letter-spacing:.14em; line-height:1 }}
.daw-empty {{ background:#121116 }}
.daw-cell button {{ width:100%; min-width:0; border-radius:0; border:1px solid #68676a; border-top-color:#929195; background:#202025; color:#f5f5f5; padding:8px 7px; font-family:inherit; font-weight:300; font-size:.66rem; letter-spacing:.035em; text-align:left; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; cursor:pointer }}
.daw-cell.daw-cluster button {{ padding:6px 5px; min-height:24px; border-radius:0; font-size:.59rem; box-shadow:inset 0 -1px 0 #0f0e12 }}
.daw-cell.daw-cluster button[data-event-id*="parallel-a"] {{ border-color:#0071bb }}
.daw-cell.daw-cluster button[data-event-id*="parallel-b"] {{ border-color:#fab413 }}
.daw-cell button:hover {{ border-color:#f5f5f5; background:#2c2b30 }}
.daw-cell button:focus-visible {{ outline:2px solid #f05a24; outline-offset:2px; border-color:#f05a24; background:#2c2b30 }}
.daw-cell button.event-active {{ border-color:#f05a24; background:#f5f5f5; color:#0f0e12; font-weight:500 }}
.daw-cell button[data-event-kind="tool_call"] {{ border-left:3px solid #7fc86a }}
.daw-cell button[data-event-kind="tool_result"] {{ border-left:3px solid #fab413 }}
.daw-cell button[data-event-kind="prompt"] {{ border-left:3px solid #f05a24 }}
.daw-cell button[data-event-kind="decision"] {{ border-left:3px solid #0071bb }}
.track-led {{ width:7px; height:7px; flex:0 0 auto; background:#7fc86a }}
.track-human {{ background:#f05a24 }}
.track-planner {{ background:#0071bb }}
.track-agent {{ background:#7fc86a }}
.track-reviewer {{ background:#fab413 }}
.daw-rows .edge-overlay {{ z-index:3 }}
.daw-rows .edge {{ stroke:#7fc86a; opacity:.82 }}
.daw-rows .edge-evidence {{ stroke:#fab413; stroke-dasharray:4 3 }}
.daw-rows .edge-broken {{ stroke:#f05a24 }}
.daw-rows .edge.edge-active {{ stroke-width:3; opacity:1 }}
.detail {{ border-radius:0; background:#17161a; border-color:#57565a; color:#f5f5f5; font-size:.75rem; min-height:86px }}
.detail h3 {{ margin:.75rem 0 .35rem; color:#aaa9ab; font:600 .62rem/1.4 ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.14em }}
.detail-status-strip {{ display:flex; gap:14px; flex-wrap:wrap; padding-bottom:8px; border-bottom:1px solid #3a393d; color:#f5f5f5; font:600 .66rem/1.4 ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.08em }}
.detail-status-strip span:nth-child(2) {{ color:#aaa9ab }}
.lens-aperture {{ margin-top:.78rem; padding-top:.72rem; border-top:1px solid #3a393d }}
.lens-aperture h3 {{ margin-top:0 }}
.lens-aperture-intro {{ margin:.1rem 0 .65rem; color:#8b929a; font-size:.66rem; letter-spacing:.04em }}
.lens-aperture-diagram {{ position:relative; width:min(100%,430px); aspect-ratio:1; margin:8px auto; border:1px solid #3a393d; border-radius:50% }}
.lens-aperture-center {{ position:absolute; inset:38%; display:grid; place-items:center; border:1px solid #57565a; border-radius:50%; color:#aaa9ab; text-align:center; font-size:.6rem }}
.lens-aperture-diagram .lens-segment {{ position:absolute; width:100px; min-height:70px; transform:translate(-50%,-50%) }}
.lens-segment[data-lens-key="jin"] {{ left:50%; top:12% }}
.lens-segment[data-lens-key="seon"] {{ left:85%; top:39% }}
.lens-segment[data-lens-key="mi"] {{ left:72%; top:80% }}
.lens-segment[data-lens-key="in"] {{ left:28%; top:80% }}
.lens-segment[data-lens-key="hyo"] {{ left:15%; top:39% }}
.lens-segment-detail[hidden] {{ display:none }}
.lens-segment {{ display:grid; grid-template-columns:auto 1fr; grid-template-rows:auto auto; column-gap:5px; align-items:center; min-width:0; padding:7px 6px; border:1px solid #3a393d; border-radius:0; background:#121116; color:#f5f5f5; text-align:left; transition:background 200ms ease,border-color 200ms ease }}
.lens-segment:hover,.lens-segment:focus-visible,.lens-segment[aria-expanded="true"] {{ border-color:#f05a24; background:#1d1a1d }}
.lens-glyph {{ grid-row:1 / span 2; font-size:1.15rem; line-height:1 }}
.lens-event-glyph {{ color:#747378 }}
.lens-segment[data-lens-state="OBSERVED"] .lens-event-glyph {{ color:#7fc86a }}
.lens-hanja {{ font-size:.86rem; font-weight:400 }}
.lens-run-state {{ color:#8b929a; font:600 .54rem/1.2 ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.04em }}
.lens-segment[data-run-lens-state="OBSERVED"] .lens-run-state {{ color:#7fc86a }}
.lens-segment[data-run-lens-state="PARTIAL"] .lens-run-state {{ color:#fab413 }}
.lens-segment-detail {{ grid-column:1 / -1; display:grid; gap:3px; margin-top:5px; padding-top:5px; border-top:1px solid #3a393d; color:#b9c0c7; font:500 .58rem/1.35 ui-monospace,SFMono-Regular,Consolas,monospace }}
.lens-aperture-axis {{ display:flex; align-items:center; gap:7px; margin-top:8px; color:#8b929a; font:600 .58rem/1.3 ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.08em }}
.lens-axis-symbol {{ color:#fab413; font-size:.9rem }}
.lens-axis-arrow {{ flex:1; border-bottom:1px solid #57565a; padding-bottom:3px; text-align:right }}
.detail-proof, .detail-missing {{ color:#aaa9ab }}
.detail-proof p, .detail-missing p {{ margin:.18rem 0 }}
.detail-missing p {{ color:#fab413 }}
@media (max-width:820px) {{ main {{ padding:18px 14px 40px }} .daw-console {{ margin-inline:-14px; border-inline:0 }} .daw-console-head {{ padding-inline:14px }} .detail {{ border-radius:0 }} .lens-aperture-diagram .lens-segment {{ width:82px; min-width:0 }} }}
@media (prefers-reduced-motion:reduce) {{ .daw-cell button,.lens-segment {{ transition:none }} }}
</style></head><body><main><header><div><h1>HyoDo Evidence Graph</h1><p class="meta">Local only · No composite score · <a href="/">Back to instrument panel</a></p></div></header>
{notice_html}
{_render_verification_header(verification_view)}
{_render_verification_rail(verification_view)}
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
{missing_html}
<section id="event-detail" class="detail" aria-live="polite"><p class="detail-kicker">RUN #3 / READING GUIDE</p><p>Select a timeline pad to inspect its recorded 5W1H evidence.</p><p><strong>SOLID</strong> execution route · <strong>DASHED</strong> evidence relation · <strong>ORANGE</strong> human or unresolved signal.</p></section>
</main><script>{GRAPH_SCRIPT}</script></body></html>"""
