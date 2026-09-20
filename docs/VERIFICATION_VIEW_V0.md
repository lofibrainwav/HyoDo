# Verification View v0

`hyodo.verification-view/v0` is a read-only presentation projection of one
`hyodo.evidence-graph/v1` payload. It answers two questions about a run —
*what is proven* and *what is missing* — and it answers nothing else.

It is a projection, not a new observation. Evidence fields are copied, filtered,
or re-grouped. Optional intent reviews compare explicitly supplied scalar
values under the [intent review contract](./INTENT_REVIEW_V1.md); they do not
infer semantic intent or verify those values. It carries no score, confidence, or
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

The six questions preserve the recorded event, temporal projections interpret
its position and context, and independent virtue lenses evaluate it. These
layers reference each other without owning or rewriting each other's content.

The horizontal axis is time; the vertical axis is participants. Eternity / 永
is an independent continuity lens, not time itself. The current graph exposes
five measured columns and no independent event-level Eternity assessment, so
that assessment remains `UNOBSERVED`. The legacy `time_axis.continuity_lens`
field names the related lens for compatibility; it does not measure it. See
[Canonical Virtue Contract](./VIRTUE_CONTRACT.md).

## Participants and Who

Timeline rows preserve each producer-provided participant lane. A role is a
separate annotation, not a bucket that merges people or agents. A child agent
with an observed parent lane may be a worker; an unrelated tool-calling session
has an unobserved role (`null`), not an assumed worker role. Review citations
can cross distinct agent identities even when both have `actor: agent`.

`who.actor` and `who.actor_id` retain the event's recorded actor. `who.from`
and `who.to` retain explicit `meta.participants` endpoints from the ledger:

```json
{"meta": {"participants": {
  "from": {"actor": "human", "actor_id": "requester"},
  "to": {"actor": "agent", "actor_id": "recipient"}
}}}
```

An endpoint uses the existing actor vocabulary (`human`, `agent`, `hyodo`) and
an optional opaque actor ID. Missing endpoints remain `null`. An existing actor
is not silently reinterpreted as a message sender; causal parents and tool names
do not manufacture a recipient. A reply records its own reversed endpoints.
These are host-declared relationships, not authenticated identities or authority.
The Benevolence / 仁 lens can inspect this relationship evidence without treating
its presence as a measured impact, a virtue score, or approval. Tools remain
part of how the work was carried out, not invented people in this relation.

The local dashboard places timezone-aware event timestamps from earlier to later
on the horizontal time axis. Per-run step indices remain in event
details because they reset across runs. Missing or ambiguous timestamps are
explicitly marked `TIME UNOBSERVED`; their placement does not assert chronology.
Selecting an event exposes six questions and five independent radial lenses
(Truth, Goodness, Beauty, Benevolence, and Hyo). Eternity is shown separately
from time navigation.
This layout does not change lens evidence status or decision authority.

## Temporal contract target (not implemented)

The following is a design target, not a claim that the current event schema or
storage enforces it. The current view exposes `ts`, not separate occurrence,
observation, and recording timestamps. Its `why.reason` comes from
`policy.reason`; it is policy rationale, not an observed actor motive.

Use one host-owned event history with three read projections: historical record,
fresh observation, and hypothetical projection. HyoDo can validate and present
evidence contracts; the host retains storage, planning, execution, and authority.

- Preserve the original claim and its provenance, including claims later found
  false. A correction is a new event referencing the old event. A derived
  `superseded_by` lookup must not require rewriting the original envelope.
- Give observations, corrections, predictions, and execution results distinct
  event IDs. Link their subject and evidence explicitly; sharing a subject does
  not mean reusing an event ID. A prediction can be recorded now while its
  predicted outcome remains hypothetical indefinitely.
- Keep occurrence time, observation time, and recording time distinct. Absent
  times remain unknown. Freshness is assessed for a specific source identity,
  surface, and question; a recent timestamp alone cannot establish current code.
- Separate declared intent, inferred motive, and policy rationale. A proposed
  WHY claim carries a value, provenance kind, attributable source reference,
  and evidence references. Missing WHY remains `UNOBSERVED`. Observing someone
  declare a motive does not independently verify that motive. Later supporting
  evidence is a new record, not an in-place promotion of an inferred claim.
- Keep provenance kind, evidence status, freshness, and authorization separate.
  A digest checks content consistency against a trusted expected digest; by
  itself it establishes neither truth, authorship, nor append-only enforcement.
- A current observation may contradict an older claim without erasing it. An
  unobserved current surface does not automatically refute historical evidence.
  A hypothetical projection never becomes an executed result without a separate
  actual execution observation, and a dry-run's own side effects remain actual
  events even when the modeled outcome is hypothetical.

In the graph, recorded events and predictions must remain visually distinct.
The time axis provides temporal navigation, while the independent
five-lens aperture inspects the selected record. Eternity / 永 assesses
continuity only when separate supporting evidence is available. Who's From / To relationship
can inform Benevolence / 仁; it does not establish recipient impact. None of
these projections promotes evidence into action authority.

## WHY and distance from user intent

An intent comparison is a separate, attributable evaluation referencing the
original event. It must not rewrite the event's WHY. The viewer supports
[bounded host-supplied comparisons](./INTENT_REVIEW_V1.md). Natural-language
intent extraction and general semantic alignment remain host responsibilities;
absent intent and comparison evidence remain `UNOBSERVED`.

Keep four records distinguishable: the user's declared request, the agent's
interpretation of that request, the agent's declared action rationale, and a
comparison with observed actions or outcomes. An interpretation is not a
user-confirmed requirement, and policy rationale is not actor intent.

Compare explicit requirements along four dimensions:

| Dimension | Comparison question |
| --- | --- |
| Goal | Does the observed outcome satisfy the requested outcome? |
| Scope | Was requested work omitted, or unrequested work added? |
| Constraints | Were stated prohibitions, resource limits, and boundaries respected? |
| Completion | Were the user's acceptance conditions actually observed? |

Each comparison needs an intent event reference, a requirement reference,
action/result evidence references, an attributable evaluator, an observation
time, and an assessment such as `SATISFIED`, `DEVIATES`, or `UNOBSERVED`.
Assessment states are distinct from evidence observation and action authority.
Conflicting intent sources require clarification; the viewer must not silently
choose the latest or most convenient wording.

Distance is a per-requirement difference: for example, an observed cost exceeds
an explicit budget by an amount in the same currency. Such differences require
compatible units and an explicit comparison basis. Counts of satisfied,
deviating, and unobserved requirements are descriptive; they do not constitute
a semantic alignment percentage. An unknown requirement is neither satisfied
nor a measured deviation, and one violated prohibition cannot be averaged away
by many satisfied preferences.
Execution progress is separate: unfinished work is not automatically an intent
violation, and a completed action is not automatically a satisfied requirement.

Compare the agent's interpretation with declared intent separately from
comparing actual results with that intent. A correctly executed misunderstood
plan is still misaligned with the request. Predicted deviation stays hypothetical
until supported by actual observations. A user-approved change references its
own source and creates a new intent version; it does not erase the original
request or retroactively authorize earlier actions. Resolving apparent alignment
never supplies execution permission.

## Fields

| Field | Source |
| --- | --- |
| `lanes` | `graph["rows"]`, reshaped only |
| `events[].who` … `how` | recorded fields plus the explicit intent-review comparison |
| `events[].columns` | `graph_view.assign_columns` |
| `events[].gutter` | `unclassified` or `unmeasured`, kept distinct |
| `events[].hyo_chained` | `graph_view.hyo_chain` |
| `events[].causal_parents` | `graph_parenting.parent_sets` |
| `edges_causal` | edges of type `parent_event_id` |
| `edges_evidence` | edges of type `evidence_ref` |
| `decisions_by_run` | decision nodes, grouped, not judged |
| `presentation.allow_withheld` | true when the graph status is not `READY` |
| `missing` | counts already present elsewhere in the graph |
| `coverage` | `graph_view.column_coverage` |
| `topology` | `graph["topology"]` |

## Withholding an unearned ALLOW

A graph that could not resolve its own citations has not earned an `ALLOW`.
When `status` is not `READY`, `presentation.allow_withheld` is true and every
recorded `ALLOW` is reported twice:

- `what.decision` keeps the value the ledger recorded;
- `what.decision_presentable` reports `UNOBSERVED`.

Only `ALLOW` is withheld. Withholding a `DENY` or an `ASK` would hide a
problem rather than avoid a false one.

Both fields ship together on purpose. Presentation may compress toward
unknown; it may not erase what the ledger holds. A consumer renders
`decision_presentable` and can still show the recorded value beside it.

This rule lives here, in one place, so that each surface reads the same answer
instead of re-deciding it in its own language.

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
