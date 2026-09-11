# Sensor coverage matrix

Phase 0 asks for a per-signal matrix that marks each desired signal
`OBSERVED`, `PARTIAL` or `UNOBSERVED`, and that keeps a **missing producer
vocabulary** apart from a **deliberately excluded channel**. That distinction
is what this table is for.

Read from code, not from what a roadmap wishes existed. Sources are the
KINGDOM contract, its trace producer and the bridge that carries events across:

```text
agent/team/coder.js                       publishes execution:trace:*
agent/core/hyodo-observation-contract.js  allowlist + canonical mapping
scripts/kingdom-hyodo-trace-bridge.js     stream reader, run filter
```

## What this table measures

The **producer layer**: what a real KINGDOM run emits and how much of it
survives into a canonical `hyodo.agent-event/v1`.

It is not a table of what the schema *can express*. Those are different
questions and answering them in one table would give `MEASURED` two meanings.
See "Two layers" below.

## Channels

The producer publishes six trace channels. The contract allowlists four.

| native channel | allowlisted | canonical kind | state |
| --- | --- | --- | --- |
| `execution:trace:run-started` | yes | `prompt` | OBSERVED |
| `execution:trace:stage-started` | **no** | — | **MISSING** |
| `execution:trace:task-started` | yes | `tool_call` | OBSERVED |
| `execution:trace:task-finished` | yes | `tool_result` or `error` | OBSERVED |
| `execution:trace:stage-finished` | **no** | — | **MISSING** |
| `execution:trace:run-finished` | yes | `model_response` or `error` | OBSERVED |

The two stage channels are the excluded-channel case. The producer emits stage
boundaries; the allowlist drops them before mapping, so stage structure never
reaches a canonical event even though it exists upstream.

## Signals

| signal | producer sends | canonical field | privacy | run filter | state |
| --- | --- | --- | --- | --- | --- |
| run identity | `runId` | `run_id` | salted hash | applies | OBSERVED |
| actor identity | `author` | `actor_id` | salted hash | applies | OBSERVED |
| step order | derived from `stageIndex` | `step_index` | n/a | applies | OBSERVED |
| causal parent | derived | `parent_event_id` | n/a | applies | OBSERVED |
| terminal outcome | `ok`, `status` | `kind: error` + `verification_failure` tag | coarse marker only | applies | OBSERVED |
| evidence references | `evidenceRefs` | `evidence_refs` | gate-ref pattern filter | applies | PARTIAL |
| stage boundary | `stageIndex`, `stageCount` | none | n/a | n/a | MISSING |
| model / provider | not sent | `meta.model` stays null | n/a | n/a | UNSUPPORTED |
| io digests, byte counts | not sent | `io.*` stays null / 0 | n/a | n/a | UNSUPPORTED |
| tool args, paths, urls, method | not sent | null / empty | n/a | n/a | UNSUPPORTED |
| policy decision | not sent | `policy.reason: unevaluated` | n/a | n/a | UNSUPPORTED |
| retry, rework, resource conflict | not sent | reads removed | n/a | n/a | MISSING |
| reviewer verdict | on its own channels | none | n/a | n/a | MISSING |
| iteration detail | internal only | none | n/a | n/a | MISSING |

`PARTIAL` on evidence references is literal: the producer may send any string,
and only those matching `gate:<name>@<sha>` survive. Everything else is
dropped without a record that it was dropped.

`UNSUPPORTED` means the producer does not emit the signal at all. It is not a
HyoDo defect and not repairable in HyoDo; wiring it would be producer work.

### Three causes behind `MISSING`

Phase 0 asks to separate a missing producer vocabulary from a deliberately
excluded channel. Reading the code, there are three causes, not two, and they
need different work to close:

| cause | signals | what would close it |
| --- | --- | --- |
| **excluded channel** — emitted, dropped by the allowlist | stage boundaries (`execution:trace:stage-started` / `stage-finished`), reviewer verdict (`governance:review:approved` / `rejected` / `converged`, `work:review:*`) | a contract decision about which channels may map, plus canonical semantics for each |
| **not on the observed channels** — exists in the producer, absent from its trace payload | iteration detail (`maxIterations`, `iterationFn({iteration, prevResult})` drive real retries inside a task) | the producer adding the field to `execution:trace:task-*` |
| **no vocabulary** — the producer has no such concept | retry, rework, resource conflict | upstream design, not a mapping change |

The middle row is the one most easily misread. A task really does iterate up
to three times, and none of that reaches an event: `task-finished` carries
`taskId`, `stageIndex`, `stageCount`, `ok`, `status` and a timestamp, and
nothing about attempts. A ledger reader sees one attempt per task because that
is all the channel says, not because that is what happened.

The contract once read `data.retry` and `data.rework`. Those reads were
deleted rather than left as a permanently false value -- the right call, and
the reason the bottom row reads `no vocabulary` rather than `unobserved`.

## Two layers

Run receipts do not all come from the same place, and the difference matters
more than any single row above.

| layer | what produced it | receipts |
| --- | --- | --- |
| producer | `coder.js` → bridge → canonical mapping | Run #1, #2, #2b |
| harness | a harness constructing events directly | Run #3, Run #3 corrected-v2 |

Run #1 recorded a real KINGDOM readback and observed only sequential topology,
no evidence completeness, and an unknown outcome. Run #3 corrected-v2 records
`serial`, `parallel`, `DAG join`, `retry`, `wait` and `rework` as `MEASURED` --
but its own text says the *corrected harness* recorded those relationships, and
the producer publishes no retry or rework field at all.

Both statements are true about different things. Run #3 shows what the event
schema can express; it does not show that a KINGDOM run emits those signals.
Merging the two into one coverage number would report an observation capability
this system does not have.

## Two drifts found while reading

**The contract's own comments are stale.** They state that `coder.js` never
sets `ok` or `status`, so failure mapping "is presently inert". The current
producer sends both, on `task-finished` and `run-finished`. Failure mapping is
live; the comment describes a repo that has moved.

**`meta.model` is null for the opposite reason it was null in Codex.** The
Codex adapter had the field available and did not read it, which was repairable
and was repaired. KINGDOM's producer never sends a model or provider field, so
here it is `UNSUPPORTED` rather than a gap to close.

## What this table does not do

It records what was read. No run was executed to fill a cell, no signal was
inferred from an adjacent one, and no row was marked observed because a
capability exists somewhere that could have produced it.
