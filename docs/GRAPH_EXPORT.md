# Graph export bridge (`hyodo graph export`)

Stage 2 package 2-C adopts the *structure* of a Zettelkasten (atomic
notes with ids, parent chains, explicit links, one claim per note,
clusters, hub pages) over the agent-event ledger — not the notes
themselves. `hyodo graph export` writes that structure out as one file
an external note system can turn into permanent notes.

Bodies, chunk text, and embeddings never cross this bridge. Only ids,
parents, refs, claims, and clusters do — the same boundary the rest of
HyoDo's evidence pipeline holds everywhere else (BYOM: bring your own
model, HyoDo ships none).

## What it writes

```
hyodo graph export [--out .hyodo/graph.json] [--yes] [--root .]
```

The output is one JSON object, schema `hyodo.graph-export/v1`:

```json
{
  "schema": "hyodo.graph-export/v1",
  "generated_at": "2026-09-06T12:00:00+00:00",
  "nodes": [],
  "edges": [],
  "backlinks": {},
  "clusters": {
    "truth": [], "goodness": [], "beauty": [],
    "benevolence": [], "hyo": [], "eternity": [], "unclassified": []
  }
}
```

## Timed events

An event may include `io.duration_ms`, a non-negative integer supplied by the
observing harness. HyoDo validates and preserves this value in the report
graph; it does not infer duration from timestamps or claim that an absent
value was zero. `duration_ms` is therefore a measurement annotation, not a
scheduler or performance verdict.

The local dashboard can inspect a sealed ledger without running project gates:

```
hyodo dashboard --evidence-root /path/to/evidence-pack
```

The path must contain `.hyodo/agent-events.jsonl`. This mode is graph-only:
gate, safety, and history surfaces are explicitly `UNOBSERVED`, and no receipt
is written. It is suitable for Evidence Pack review, not for certifying a
checkout or replacing the KINGDOM execution authority.

- `nodes` / `edges` mirror `hyodo report --format graph`'s own
  `hyodo.evidence-graph/v1` shape (`hyodo/event_graph.py`) verbatim,
  including each node's `actor_id` (`null` when the event did not carry
  one) — an optional, opaque label (session id, seat name, model alias)
  the harness chose, letting two agents in one run keep separate rows
  instead of collapsing into one. HyoDo never derives identity from it.
- `backlinks` is the reverse index of every non-broken `evidence_refs`
  entry in the ledger: `{cited_event_id: [citing_event_id, ...]}`, values
  sorted, keys only for events cited at least once. `hyodo report
  --format graph`'s own JSON output gains this same additive field —
  the command's exit contract (0 clean graph / 1 `unresolved_refs`
  non-empty / 2 write failure) is unchanged by it.
- `clusters` groups `kind == "decision"` event ids by the pillar
  `hyodo/graph_view.py`'s `assign_columns` mapping table places them on.
  The six spec-fixed pillar keys are always present, plus an additive
  seventh `"unclassified"` key for a decision the mapping table places
  nowhere. `eternity` is always empty — Eternity is read off the local
  graph viewer's orb, never a column, so no decision is ever assigned to
  it.

A dangling `evidence_refs` entry (only possible in a hand-edited or
truncated ledger; `hyodo/events.py`'s own recording path rejects one at
write time) is excluded from `backlinks` exactly as
`hyodo/event_graph.py`'s edge validation already excludes it from
`edges` — reported there, not silently dropped, and the export still
succeeds. A decision with no `evidence_refs` at all (a claim with no
backing evidence) is advisory, the same way `hyodo report --format
graph`'s own orphaned-decision handling is: it still lands in its
pillar's `clusters` entry, it is simply never a `backlinks` value.

## Confirmation

Mirrors `hyodo connect`'s consent pattern: by default the command asks
before writing. `--yes` skips the prompt for scripted/non-interactive
callers, which must say so explicitly — a non-interactive caller with no
`--yes` is refused (`confirmation_required`, exit 1), never silently
written.

## Exit codes

| Outcome | Exit |
| --- | --- |
| Export written | 0 |
| Confirmation declined without `--yes` | 1 |
| Ledger unreadable, or the write itself failed | 2 |

A ledger file that does not exist yet is an honest empty ledger, not
"unreadable" — the export still succeeds with empty `nodes`/`edges`.
Likewise, a pre-1-B ledger (no `parent_event_id`/`evidence_refs` fields
anywhere) exports successfully with empty `edges`/`backlinks` — an
honestly empty graph is a valid graph, not an error.

## Actor rings

Stage 2 package 2-C also fills in the local evidence-graph viewer's
per-actor "rings" drill-down
(`docs/superpowers/specs/2026-09-06-hyodo-core-engine-monitor-design.md`,
section 5), built by `hyodo.graph_view.build_actor_rings(graph, root)`
from ledger and local-manifest data only — never the network:

- **Skills** (innermost): one entry per skill in
  `.hyodo/skills/manifest.json` (Stage 2-A), if present — name, compiled
  rule ids, and a six-slot `pillar_profile` count re-derived live from
  the skill's own source text. Absent manifest -> empty, `"unobserved"`.
- **Memory**: the events a row's own `decision`-kind events cited via
  `evidence_refs`, plus absorbed-source chunk *digests* from
  `.hyodo/chunks-manifest.json` (Stage 2-B) if present — digests only,
  never chunk text.
- **Routines**: tool names this row called two or more times, with
  counts (never a percentage), plus the harness targets already wired
  via `.hyodo/connect.json` (Phase 1-D) if present.
- **Tools** (outermost): one entry per distinct tool name this row
  called, with the latest recorded policy decision
  (`ALLOW`/`ASK`/`DENY`/`UNOBSERVED`) for that tool.

`GET /api/actor?key=<row key>` (`hyodo dashboard`) serves one row's four
rings as JSON; an unknown key returns `404 {"error": "unknown_actor"}`.
The `/graph` page itself renders every row's rings server-side as a
hidden panel a click on the row's label toggles open (Escape closes it),
using the same fixed row key `build_actor_rows` already keys its `rows`
dict with.

## The `/graph` grid (local viewer second pass)

`/graph` renders one grid — five virtue columns by actor row, per
`docs/superpowers/specs/2026-09-06-hyodo-core-engine-monitor-design.md`
section 2 — not two separate lists. A few rendering details worth calling
out for anyone reading the page's markup or extending it:

- **Row labels.** A row identified by the optional `actor_id` field
  (`hyodo.graph_view.build_actor_rows`) renders exactly `agent
  <actor_id>`. A row with no `actor_id` renders `agent ` followed by the
  first eight characters of its earliest event's id — a short, stable
  lineage id — rather than whichever tool that lineage happened to call
  first.
- **Nesting.** A child row (`parent_row`/`depth`) renders indented
  (`depth * 18px`) under its parent, with a collapse toggle that hides
  every descendant row.
- **Edges.** An SVG overlay draws `parent_event_id` as a solid elbow and
  `evidence_refs` as a dashed arc between tiles; a dangling ref or an edge
  whose other end has no column at all (e.g. a `model_response` with no
  observed output digest) draws as a short red stub instead. Coordinates
  are schematic (the grid's own column/row/tile-index geometry), not a
  measured pixel read.
- **The orb** is a 9x9 pixel grid, not a circle: the lit square count is
  the run's raw `observed` count (capped at 81), never a ratio or a
  percentage.

## What this is not

- Not a sync target: nothing here reads a note system back into HyoDo.
- Not a recommendation or a score: no field here is a probability, a
  confidence value, or a composite score.
- Not a replacement for `hyodo report --format graph`: that command's
  own shape and exit contract are unchanged beyond the additive
  `backlinks` field.
