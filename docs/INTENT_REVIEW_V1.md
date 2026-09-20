# Intent review v1

An optional `meta.intent_review` block records bounded comparisons supplied by
an integrating host. HyoDo validates the block and compares its scalar values;
it does not extract intent from natural language, retrieve personal history,
verify that a value matches cited content, or authorize actions.

The source implementation supports this contract. Its presence on a branch or
main does not establish availability in an already published package.

## One verification loop, separate responsibilities

The host carries one loop: declared intent → interpretation and plan → action →
observed result → comparison with intent → correction or the next action.
Closure requires evidence for the applicable acceptance conditions. Missing
observations remain open. A changed requirement needs its own attributable
source; a comparison does not manufacture that authorization.

The six questions preserve the event record. Temporal projections distinguish
historical records, current observations, and hypothetical outcomes. Independent
virtue lenses inspect the evidence without owning those records or replacing
human and host authority. Comparison results do not set virtue scores, policy
decisions, or a global loop-closed flag.

## Discovering and preserving intent

The host first identifies the explicit goal, scope, constraints, and acceptance
conditions in the user's request. Relevant historical requests can provide
context; a repeated past preference is not automatically a current requirement.
The host retains source references and labels its interpretation `INFERRED`.
It asks only about uncertainty that would change the action, scope, or risk.
Confirmation or a changed request becomes a new source event, not a rewrite of
an older request. HyoDo does not authenticate a host-declared human actor.

Separate comparisons of `interpretation`, `action`, and `outcome` make it
possible to distinguish a misunderstood request from a poorly executed plan.
The host explicitly chooses the intent baseline; HyoDo does not select a newer
or more convenient request automatically.

## Record shape

The block is opt-in on the existing agent event. The event's actor and timestamp
attribute when and by whom the comparison was recorded. Requirement IDs are
stable labels within the host's chosen baseline.

```json
{
  "schema_version": "hyodo.intent-review/v1",
  "intent_ref": "human-request-1",
  "previous_review_ref": null,
  "mode": "OBSERVED",
  "target": "outcome",
  "checks": [
    {
      "id": "budget-limit",
      "dimension": "constraints",
      "basis": "DECLARED",
      "operator": "lte",
      "expected": 100,
      "actual": 130,
      "unit": "USD",
      "evidence_refs": ["observed-result-1"]
    }
  ]
}
```

- `mode`: `OBSERVED` or `PROJECTED`. Recorded predictions never become actual
  observations merely because time passes.
- `target`: `interpretation`, `action`, or `outcome`.
- `dimension`: `goal`, `scope`, `constraints`, or `completion`.
- `basis`: `DECLARED` or `INFERRED`, as reported by the host. This is not an
  authenticated user-confirmation receipt.
- `operator`: exact `eq`, numeric `lte`, or numeric `gte`. There is no fuzzy
  semantic comparison. Boolean values are distinct from numbers.
- `expected` and `actual`: finite numbers with absolute value at most `1e100`,
  nonempty strings up to 160 characters, or booleans. `actual` may be `null`.
  Numeric values must use the one declared `unit`; no unit conversion is done.
- `checks`: 1–32 entries, with unique IDs and at most 32 event evidence references
  each. Unknown fields, incompatible value types, and nonfinite numbers fail
  event validation.
- `previous_review_ref`: optional, explicit link to an earlier comparison event.
  The view reports changed requirement fields and changed intent source IDs.
  Such a change is not automatically a violation or an approved change.

**Storage:** opting into this block stores its requirement IDs, scalar values,
units, and references in the local ledger. Digest-only body handling does not
redact these explicit metadata values. Use non-sensitive labels and references;
do not copy full prompts or secrets into these fields. Existing ledgers are not
rewritten and no comparison is invented for them.

## Reading the result

`events[id].why.intent_review` in the verification view contains the comparison.
The local dashboard and the public local-file viewer render it separately from
policy rationale. Neither viewer uploads a ledger to obtain this comparison.

The raw value `comparison` is `SATISFIED`, `DEVIATES`, or `UNOBSERVED`. Numeric
`delta` is `actual - expected` in the declared unit. In the example it is `30`;
it is not a semantic distance, percentage, or moral score.

The evidence-qualified `state` remains `UNOBSERVED` when the human prompt source
is missing, the requirement is inferred, the mode is projected, the graph is not
ready, or result evidence is missing, self-referential, lacks an output digest,
or is later than the comparison. Equal timestamps require a recorded earlier
step in the same run. A changed requirement under the same intent source is
also withheld until a new attributable source is provided. Ambiguous or missing timestamps also withhold
the result. Values and references remain visible with the withholding reasons.
A resolved digest reference does not independently verify the supplied value.

`state: RECORDED` on the review means that a valid comparison block exists. It
is not an overall alignment verdict. Missing dimensions are listed separately;
there is no aggregate, ranking, or automatic approval. Unfinished work is not
necessarily a deviation, and one violated prohibition cannot be averaged away
by many satisfied preferences.

A historical comparison remains a historical snapshot. Fresh current state
requires a new observation. An unavailable, self-referential, or later
`previous_review_ref` stays unlinked. Recording a new review preserves the
previous requirement values so the user can inspect where interpretation or
scope changed.
