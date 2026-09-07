# HyoDo core engine monitor — design: one graph, fixed virtue axis, agent rings

## Status

Draft for owner review; nothing here is implemented. The current `hyodo
dashboard` (`hyodo/dashboard.py`, six raw-metric cards, no composite score)
and the public `/evidence-graph/` prototype (fixture data,
`site/src/graph/evidence-graph.ts`) are the starting points. The local viewer
this design describes depends on Phase 1-B's `hyodo report --format graph`
output, `.hyodo/reports/hyodo-report.graph.json`
(`hyodo.evidence-graph/v1`, shipped on main).

## 1. Context and honesty rules

`hyodo dashboard` today renders six pillar cards from raw evidence — no
graph, no verdict, no questions (`hyodo/dashboard.py:212-297`). The public
site prototype has a graph renderer but no live data
(`site/src/graph/evidence-graph.ts:63`, fixture `EVENTS`). This design
merges the two into one local viewer: a graph the operator can actually
read, with a fixed virtue axis and per-actor drill-down, fed by the same
JSON `hyodo report --format graph` already writes.

Every rule Phase 1 and Stage 2 established for the CLI applies unchanged to
this viewer, because a prettier renderer must not become a second, looser
truth:

- **Local only, network 0.** The viewer reads only files under `.hyodo/` on
  disk. It makes no outbound request, embeds no analytics, and loads no
  remote script or font.
- **No composite score.** The viewer never computes or prints a HYOGOOK
  number. It renders `observed / expected` coverage ratios and the four
  decisions (`ALLOW`/`ASK`/`DENY`/`UNOBSERVED`) that already exist.
- **`UNOBSERVED` is always visible.** An unclassified event, a missing
  mission, or a broken edge renders as `UNOBSERVED`, never as blank space
  or a silently-skipped tile.
- **No `probability`/`confidence`.** The viewer never invents a field the
  schema does not carry (`hyodo/policy.py:104-106` already forbids this at
  the data layer).
- **Presentation never changes a decision.** Choosing an audience profile
  (section 7) or clicking into a ring (section 5) never re-evaluates
  policy; it only changes which already-computed fields are shown and how
  they are worded.
- **Exit codes unchanged.** `hyodo dashboard` keeps its current process
  behavior; nothing here adds or changes a CLI exit code.
- **a11y and reduced-motion budgets carry over from the site.** The same
  contracts `site/scripts/verify-evidence-graph.mjs` already checks for the
  public prototype (keyboard reachability, focus visibility, static
  rendering under `prefers-reduced-motion`) apply to the local viewer,
  because it reuses the same renderer (section 8).

## 2. Coordinate system

**Columns.** Five virtues, fixed order, fixed colours (SSOT in section 9):
Truth, Goodness, Beauty, Benevolence, Hyo. Eternity is not a column — in
HYOGOOK, Eternity is the geometric mean of the other five over the run, so
it is read as the time axis (depth of the graph, oldest event at the
mission end, latest event at the orb end), not a sixth bucket competing
for events.

**Rows.** Actors, as the public prototype already renders them, generalized
from its four fixed row labels (`human`, `planner`, `executor`, `reviewer`,
`site/src/graph/evidence-graph.ts:39`) to the schema's actual actor space:
`human`, `agent:<label>`, and `hyodo`. The shipped ledger actor field is
coarse (`agent`, `human`, or `hyodo`,
`hyodo/events.py:35 ACTORS`); `<label>` is an illustrative sub-label the
viewer derives from `tool.name`/`policy.rule_id` context the same way the
prototype already labels `agent:planner` versus `agent:executor` — it is
display-only and never a new schema field.

**Sub-agent nesting.** An actor row becomes a child row, collapsible under
its parent, when that actor's earliest event carries a `parent_event_id`
(`hyodo/events.py:297-303`) pointing at a `tool_call` event belonging to a
different actor. No new schema field: nesting is entirely derived from the
edge Phase 1-B already ships. A row with no such pointer stays top-level.

**Mission.** The run's lowest-`step_index` event with `kind == "prompt"`
and `actor == "human"` (Phase 1-B's structural definition,
`docs/superpowers/specs/2026-09-06-hyodo-agent-os-phase1-design.md`,
Package 1-B). It sits at the graph's origin — the zero point both the
column layout and the time axis measure from.

## 3. Event -> virtue mapping table

Mapping is deterministic and rule-based, never a model call. It reuses the
same six-area semantics `README.md:155-165` and `hyodo/dashboard.py:73-82`
already document — this table only adds the event-level match keys needed
to place a *ledger event*, not a *pillar card*, on a column.

| `kind` | `tool.name` pattern | `policy.decision` | `rule_id` | Column(s) |
| --- | --- | --- | --- | --- |
| `decision` | any | `DENY` | any | Goodness |
| `decision` | any | `ASK` | any | Goodness + the column implied by `rule_id` below |
| `tool_call`/`tool_result` | type-check, lint tools | any | any | Truth |
| `tool_call`/`tool_result` | test runner | any | any | Goodness |
| `tool_call`/`tool_result` | formatter | any | any | Beauty |
| `tool_call`/`tool_result` | doc/onboarding tools | any | any | Benevolence |
| any | any | any | `data_boundary`, `data_boundary_undeclared` | Hyo |
| any | any | any | `web_credential_path_denied`, `web_credential_path_unobserved` | Goodness + Hyo |
| `error` | any | any | any | Truth |
| `prompt`/`model_response` | n/a | n/a | n/a | no column (feeds the time axis and mission only) |

An event matching more than one row renders as a bar spanning every
matched column, not a forced single pick — a `data_boundary` `ASK`, for
example, is both a Goodness event (a decision was made) and a Hyo event
(it touched declared-boundary data). An event matching no row goes to an
"unclassified" gutter beneath the five columns and counts as
virtue-`UNOBSERVED` for every column's coverage ratio.

**Hyo's rule is structural, not a table lookup.** An event is filial if its
`parent_event_id` chain (Phase 1-B) resolves, hop by hop, back to the
mission event; an event with no parent, or with a parent chain that
terminates before reaching the mission, is an orphan. The Hyo column's
coverage is `observed / expected` = chained events / all events in the
run — the same ratio shape every other coverage number in this document
uses, never a synthesized score.

## 4. The orb (core engine pulse)

The orb is the Eternity reading — a single element above the five columns,
not a sixth column. It carries three independent signals, each already
computed elsewhere in the schema, never a new synthesized number:

- **Colour** = the latest verdict in the run: `ALLOW` green, `ASK` blue,
  `DENY` red, `UNOBSERVED` grey — the same four decision tokens the site
  already defines (`site/src/styles/tokens.css`,
  `--color-tile-observed`/`--color-ask`/`--color-deny`, plus grey for
  `UNOBSERVED`).
- **Brightness** = `observed / expected` for the whole run (the same ratio
  the verdict line already prints, Phase 1-C).
- **Pulse** = time since the latest event, decaying toward static as the
  run goes idle; under `prefers-reduced-motion` the orb renders at a fixed
  brightness with no animation, per the a11y budget in section 1.

The orb never prints a number that is not already printed elsewhere on the
page (the verdict line, a column's coverage badge, or a ring). It is a
second rendering of existing facts, not a new fact.

## 5. Actor rings

Clicking, or pressing Enter on, a focused actor row opens a concentric
view centred on that actor. Reading inward to outward:

1. **Skills** — lens provenance (Stage 2-A). Empty, with an explicit
   "not available until skill lenses ship" note, until 2-A lands; the ring
   itself is part of this design so the viewer does not need a second
   redesign when 2-A arrives.
2. **Memory** — events this actor cited via `evidence_refs`
   (`hyodo/events.py:305-...`), plus Stage 2-B absorbed-source chunk
   digests once that package ships. Each node is a digest or an event id,
   never raw content.
3. **Routines** — repeated tool-call patterns for this actor (same
   `tool.name` recurring across steps), and Phase 1-D hook/shadow-mode
   records once `connect` ships.
4. **Tools** — one node per distinct `tool.name` the actor called, border
   colour = that call's `policy.decision` (`ALLOW`/`ASK`/`DENY`/
   `UNOBSERVED`).

Each ring's node group collapses by default (a count badge, not the full
list); expanding a group is bounded at 24 nodes shown at once per ring —
past that bound the group stays a collapsed "N more" summary rather than
rendering an unbounded list, so a long-running actor cannot make the ring
view unusable. Every node, in every ring, cites the event id (or gate
reference) it came from — nothing in the ring view is unattributed.
Keyboard: Escape returns focus to the row grid.

## 6. Questions

Each virtue column shows at most one open question at a time: the one tied
to that column's largest coverage gap (the biggest `expected - observed`
term feeding its ratio). This follows the FDE questioning discipline —
observe first, ask only what tooling could not observe, one question per
coverage gap, and a human's answer is a claim, not evidence, until an
`evidence_refs` entry attaches to it. The viewer never runs a 5W1H
interrogation over several fields at once; it surfaces one plain-language
gap per column and lets the operator decide whether to close it.

A recorded answer is written as a `human` `prompt` event
(`hyodo/events.py:35`); it stays a claim, distinguishable from observed
evidence in the UI, until some later event's `evidence_refs` cites it.

## 7. Audience profiles

A `[audience] profile = "vibe" | "engineer" | "professional"` setting (read
from `.hyodo/config.toml`, overridable with `--audience` or
`HYODO_AUDIENCE`, matching the override pattern Phase 1's `[web]`/`[trust]`
fields already use) selects vocabulary only:

- the verdict-line wording and the orb's one-line summary,
- the five column labels,
- the wording of each column's open question (section 6).

The underlying data is identical across all three profiles: decision
values, exit codes, `rule_id`s, and every event/gate id stay byte-identical
regardless of profile. `--json` output ignores the profile entirely —
machine-readable output has exactly one shape. No profile calls a model;
each is a fixed lookup table of wording, the same shape as Phase 1-C's
deterministic explanation table.

## 8. Shared renderer

One TypeScript module renders both the public prototype and the local
viewer. Today it lives at `site/src/graph/evidence-graph.ts` and exports a
pure `mountEvidenceGraph(root)` entry point plus the fixture data this
design's local viewer will replace with live graph JSON
(`site/src/graph/evidence-graph.ts:522, 63`).

**Packaging for the wheel.** The module is compiled to a static JS/CSS
asset as part of the `site/` build and copied into the Python package's
data files at release time (no CDN, no network fetch at runtime,
consistent with section 1). `hyodo dashboard` serves that static asset
alongside its existing HTML response.

**Fallback.** If the built asset is missing from a given install (for
example, a source checkout that never ran the `site/` build), `hyodo
dashboard` falls back to today's six raw-metric cards unchanged, with one
added note: "Graph viewer asset not found — showing raw evidence only
(`UNOBSERVED`)." The dashboard never fails to render because the viewer
asset is absent; it degrades to the older, already-shipped page.

## 9. Data model

**Inputs the viewer reads**, all optional except the first:

- `.hyodo/reports/hyodo-report.graph.json` (`hyodo.evidence-graph/v1`,
  Phase 1-B) — required. Nodes, edges, `missions`, and `summary` as
  documented in Package 1-B of the Phase 1 spec.
- `.hyodo/skills/manifest.json` (Stage 2-A, not yet shipped) — feeds the
  skills ring; absent today, so that ring stays empty per section 5.
- `.hyodo/folder-manifest.json` (Stage 2-B, not yet shipped) — feeds the
  memory ring's absorbed-source digests; absent today, so memory-ring
  entries are limited to `evidence_refs` until 2-B ships.

**Derived structures**, as pure functions over that input — no I/O, no
mutation, so they are trivially unit-testable against fixed fixtures:

```ts
// Places one event on zero or more virtue columns (section 3).
function assignColumns(event: GraphNode, rules: MappingTable): VirtueColumn[]

// Builds the row tree: top-level actors and their collapsible
// sub-agent children (section 2, derived from parent_event_id).
function buildRowTree(nodes: GraphNode[], edges: GraphEdge[]): ActorRow[]

// Builds one actor's four-ring content (section 5) from the graph
// plus the optional Stage-2 manifests.
function buildActorRings(
  actor: ActorRow,
  graph: EvidenceGraph,
  skills: SkillManifest | null,
  folder: FolderManifest | null,
): ActorRings

// Column coverage ratio (observed/expected) feeding the column badge
// and, for Hyo specifically, the structural chain check (section 3).
function columnCoverage(column: VirtueColumn, graph: EvidenceGraph): Ratio
```

**Colour SSOT.** `site/src/styles/tokens.css` carries every colour this
viewer uses, added by this PR: `--color-virtue-truth`, `-goodness`,
`-beauty`, `-benevolence`, `-hyo`, `-eternity` (hex values copied verbatim
from `hyodo/dashboard.py`'s existing CSS block, `hyodo/dashboard.py:293`,
so the six-card dashboard and the graph viewer render the identical
colour for each virtue), plus `--color-ring-skills`, `-memory`,
`-routines`, `-tools` for the four ring layers in section 5. The decision
colours (`--color-tile-observed`, `--color-ask`, `--color-deny`, and grey
for `UNOBSERVED`) already exist in the same file and are reused, not
redefined. `tests/test_virtue_colors_ssot.py` parses both
`hyodo/dashboard.py` and `tokens.css` and fails if the six virtue hex
values ever diverge by name or by column order.

## 10. Rollout

1. **This PR.** This spec, the colour SSOT (`tokens.css` additions +
   `test_virtue_colors_ssot.py`), and the stale-wording fix on the public
   prototype (section 11 of the phase design already shipped 1-B; this fix
   only corrects the page's own comments and banner). No Phase 1 package
   is required beyond 1-B, already on main.
2. **Local viewer, columns + orb.** `hyodo dashboard` renders the shared
   module against live `hyodo-report.graph.json`, fixed five columns, the
   orb, and the fallback in section 8. Needs 1-B (graph JSON) and 1-C (the
   verdict line the orb's summary text quotes).
3. **Actor rings.** Sections 2 and 5's row nesting and ring drill-down.
   Needs nothing beyond what step 2 already reads; the skills and memory
   rings stay empty pending Stage 2-A/2-B.
4. **Audience profiles.** Section 7's wording layer. Independent of steps
   2-3's rendering; needs only the `[audience]` config surface, following
   the same override pattern Phase 1-A's `[web]`/`[trust]` fields use.
5. **Stage 2 feeds.** Skills ring populated by 2-A, memory ring's absorbed-
   source digests by 2-B, and an ephemeral-evidence tile (screenshot
   proof-of-destruction countdown) by 2-D once each package ships. This PR
   changes nothing to make that wiring land — the rings and manifests are
   already optional inputs (section 9).

## 11. Test plan

- `test_virtue_colors_ssot.py`: the six virtue hex values match between
  `hyodo/dashboard.py` and `tokens.css`, by name and column order.
- Column assignment: a fixture event matching two mapping-table rows
  renders on both columns, not one.
- Column assignment: a fixture event matching no row lands in the
  unclassified gutter and counts as `UNOBSERVED` for every column.
- Hyo coverage: an event whose `parent_event_id` chain reaches the mission
  counts as chained; an event whose chain terminates before the mission
  does not.
- Row nesting: an actor whose earliest event's `parent_event_id` points at
  another actor's `tool_call` renders as that actor's child row.
- Orb: colour matches the run's latest verdict; brightness matches the
  run's `observed/expected`; the orb never renders a number absent from
  the verdict line or a column badge.
- Ring expansion: a ring with more than 24 nodes shows a collapsed "N
  more" summary rather than rendering every node.
- Audience profiles: the same fixture run renders byte-identical decision
  values, exit codes, and event/gate ids across all three profiles;
  `--json` output is unaffected by the profile setting.
- Fallback: with the built graph-viewer asset removed, `hyodo dashboard`
  renders the existing six-card page plus the "asset not found"
  `UNOBSERVED` note, and does not error.

## Open questions

- Whether the site's hero should adopt the five-virtue-column palette for
  its pulsing tile regions, and whether that adoption fits the hero's
  existing performance budget — today the hero's six pulsing regions use
  no virtue colour at all (`site/src/hero/scene.ts`).
- Whether the site's hero six-region grid should become, on the
  `/evidence-graph/` landing, the five columns plus orb this design
  defines, or stay a separate decorative element that only docks into the
  graph page on scroll.
- Whether 24 is the right bound for ring expansion, or whether it should
  scale with viewport size once real multi-agent runs are observed.
- Whether column assignment (section 3's mapping table) should become
  overridable in `.hyodo/policy.toml`, the way `ask_tools` already lets an
  operator extend a built-in list, so a project with unusual tool names
  is not stuck in the unclassified gutter.
