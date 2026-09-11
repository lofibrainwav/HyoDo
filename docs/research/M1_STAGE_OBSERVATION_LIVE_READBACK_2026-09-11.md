# M1 stage observation — live producer readback

**Date measured**: 2026-09-11
**Status**: OBSERVED on both canonical mains

Until this run, the stage-execution lane had one axis nobody had looked at: a
real producer emitting the declaration. Fixtures and a producer-shaped harness
had both passed, and neither is evidence that the running agent says anything.

## What was measured against

| Repo | main | Contains |
|---|---|---|
| HyoDo | `bb104d783e559ac78de7e437b42fec045d64dce6` | #254 sidecar ingest |
| KINGDOM | `886de858909a89757fee55716c30cec90389de3b` | #824 stage declaration |

Both checkouts were moved to those commits before measuring. The `hyodo` on
`PATH` was an editable install of the HyoDo checkout, so the CLI the bridge
spawned was main's code, not a published wheel.

The producer is the real `CoderAgent`, reached the way the runtime reaches it —
a `work:planning:decomposed` message on a Blackboard. It ran against an isolated
Redis so the deployed runtime, which subscribes to the same channel, would not
wake up and start building.

## The declaration

Four stage signals, each carrying the mode the producer chose:

```
run-started
stage-started    stage 0/2   execution=parallel
stage-finished   stage 0/2   execution=parallel
stage-started    stage 1/2   execution=serial
stage-finished   stage 1/2   execution=serial
run-finished     ok=false  status=failed
```

The producer's own log line for stage 0 reads `2 tasks, concurrency 2`, and for
stage 1 `1 task, concurrency 1`. The declaration matches what the batch actually
ran with.

### The declaration is not a task count wearing a different name

A stage with two tasks is not automatically parallel, and this is the difference
an observer cannot see. A control run with `stageConcurrency: 1` put two
independent tasks in one stage:

```
stage 0/1   execution=serial      # two tasks, run one at a time
```

An observer reading "more than one task means parallel" would have called that
stage parallel and been wrong. `effectiveConcurrency` lives in the producer;
nothing in the event stream exposes it.

### join_policy: all

`join_policy` is recorded only where two or more dependencies exist. Its basis
is that the producer awaits the whole previous stage before opening the next
one. That claim was checked against the clock rather than read off the source:

```
stage 0 finished   ts = …100103
stage 1 started    ts = …100104
```

The barrier is real.

## What reached HyoDo

```
bridge   seen=21  recorded=8  skipped=13
ledger   8 rows — prompt, tool_call x3, error x4
sidecar  3 observations
           execution=parallel  depends_on=0
           execution=parallel  depends_on=0
           execution=serial    depends_on=2  join_policy=all
```

No stage signal produced a ledger row. `hyodo.agent-event/v1` gained no new kind.

`join_adapter_events` resolved the shape into a graph of two roots and one node
with two parents, `issues: []`.

### Privacy

Every raw identifier from the run was searched for in both files. All absent:

```
run id, project id, author, goal text, task ids, task descriptions
```

Only salted digests are stored.

## Two properties worth stating plainly

**The ledger is idempotent under re-collection; the sidecar is not.** Running
the bridge a second time over the same stream re-attempted all 8 events and left
the ledger's sha256 unchanged. The same second pass appended 3 more observation
rows, so the file held 6 rows for 3 distinct `observation_id`s.

This does not corrupt the graph. `join_adapter_events` reports each repeat as
`duplicate_observation_event_id` and the first occurrence wins. But a consumer
reading the file directly must dedupe by `observation_id`; row count is not a
count of observations.

**An unresolved dependency is kept, not erased.** Removing the two predecessor
events a join node cites produces:

```
unresolved_dependency:kingdom-event-af98efb2…
unresolved_dependency:kingdom-event-b6ba2fc4…
```

and the node still carries its `parent_event_ids`. Dropping them would make a
dangling reference indistinguishable from a task that never had a dependency.

## Environment, stated rather than hidden

The run used `dryRun: true`, so no files were written. Every model in the chain
was unavailable — the configured local model was not installed and the hosted
provider was over its weekly quota — so all three tasks failed and the run
aggregated to `ok=false, status=failed`.

That is a different axis from the one under test. Stage boundaries publish from
a `finally`, so they are emitted whether tasks succeed or fail, and both
`stage-finished` signals were observed. **Task success on a live producer run
remains UNOBSERVED**; nothing here should be read as evidence for it.

## Measurement hygiene

The first attempt at this run isolated its Redis on port 6399. Seven test files
in KINGDOM assume that port is dead, and KINGDOM CI runs on a self-hosted
runner, so the occupied port reached CI and failed a test in an unrelated
subsystem with a plausible-looking value mismatch rather than a connection
error. The port was released, the same commit re-run, and the test passed.

That fragility is recorded separately as KINGDOM issue #825. It is not a defect
in this lane and was not repaired here. The sealing run used a port with no
references anywhere in the repository.
