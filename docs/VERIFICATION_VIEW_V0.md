# Verification View v0

`hyodo.verification-view/v0` is a read-only presentation projection of one
`hyodo.evidence-graph/v1` payload. It answers two questions about a run —
*what is proven* and *what is missing* — and it answers nothing else.

It is a projection, not a measurement. Every field is copied, filtered, or
re-grouped from the graph it is handed. It carries no score, confidence, or
aggregate, its `authority` is the literal `UNOBSERVED`, and it authorizes
nothing. A view is not evidence; evidence is not a decision.

Schema: [`schemas/verification-view-v0.schema.json`](../schemas/verification-view-v0.schema.json),
pinned by [`schemas/verification-view-v0.pin.json`](../schemas/verification-view-v0.pin.json)
and enforced by `tests/test_verification_view.py`.

## Why it exists

`hyodo.report.build_report_graph` already attaches `rows` to every graph
payload, and each row already carries a role derived from causal lineage by
`hyodo.graph_view.build_actor_rows`. Consumers were ignoring that field and
re-deriving participant lanes locally, so the same event could appear in a
different lane on different surfaces, and one surface claimed a role the
producer deliberately declined to claim.

One serialized contract removes the room for that drift instead of asking each
consumer to remember not to guess.

## Reading it

```bash
hyodo dashboard --evidence-root PATH --port 8768
curl -s http://127.0.0.1:8768/api/verification-view
```

`GET /api/verification-view` is a sibling of `/api/graph`, not a query
parameter on it: two payload shapes under one path would make that path's CORS
eligibility and cache meaning ambiguous. It reads the ledger live on every
request, so it never serves a stale case file, and it returns `404` when the
server was started without an evidence root.

## Axes

The horizontal axis is time, which is the Eternity / 永 lens. The vertical axis
is participants. That split is not invented here: `graph_view.VIRTUE_COLUMNS`
already holds five measured columns and treats Eternity as a separate
continuity indicator rather than a sixth column. See
[Canonical Virtue Contract](./VIRTUE_CONTRACT.md).

## Fields

| Field | Source |
| --- | --- |
| `lanes` | `graph["rows"]`, reshaped only |
| `events[].who` … `how` | existing node fields, regrouped only |
| `events[].columns` | `graph_view.assign_columns` |
| `events[].gutter` | `unclassified` or `unmeasured`, kept distinct |
| `events[].hyo_chained` | `graph_view.hyo_chain` |
| `events[].causal_parents` | `graph_parenting.parent_sets` |
| `edges_causal` | edges of type `parent_event_id` |
| `edges_evidence` | edges of type `evidence_ref` |
| `decisions_by_run` | decision nodes, grouped, not judged |
| `missing` | counts already present elsewhere in the graph |
| `coverage` | `graph_view.column_coverage` |
| `topology` | `graph["topology"]` |

## What it refuses to do

- **It does not merge causal and evidence edges.** The producer records them as
  distinct edge types. Drawing them as one line would destroy a distinction it
  took care to keep.
- **It does not synthesize an edge for a citation that resolves to nothing.**
  The dangling reference is reported under `missing.unresolved_refs`.
- **It does not average or supersede disagreeing decisions.** When one run
  records more than one decision, `decisions_by_run` reports all of them in
  recorded order. Reading the disagreement belongs to whoever reads the group.
- **It does not resequence late evidence.** Evidence recorded after the
  decision citing it is flagged in place with `source_after_target`.
- **It does not reconstruct what was known at an earlier time.** The event
  schema records `ts` and no ingestion time, so a second time axis cannot be
  built without inventing a field the ledger never recorded.
- **It does not report `PARTIAL`.** `hyodo.evidence-plate/v1` defines exactly
  `OBSERVED` and `UNOBSERVED`. `PARTIAL` exists in `score_derive` and in
  `continuity`, but those are separate definitions over different subjects;
  adding a third, per-event one here would reproduce in the state vocabulary
  the drift this contract removes from lane
assignment.

## Reading `missing`

`missing` is the point of the view. Against a real local ledger it is
routinely the largest section, and that is the honest result rather than a
defect: most agent ledgers record that something was called, not what it
proved.

| Bucket | Means |
| --- | --- |
| `unresolved_refs` | a citation that points at no recorded event |
| `cross_run_refs` | a parent recorded under a different run |
| `unclassified_events` | evidence was recorded, but the table has no row |
| `unmeasured_events` | the event recorded nothing classification could read |
| `calls_without_result` | a tool call no later event cited as a causal parent |
| `runs_without_intent` | a run with no recorded human intent |

`unclassified` and `unmeasured` stay separate on purpose. The first says fix
the table; the second says fix the recording. Reporting them as one number
invites the one fix that must never be made: a mapping row keyed on a tool's
name, which is what something is called rather than what it did.
