# KINGDOM integration contract audit

Snapshot: 2026-09-13 PT. This is an observation-boundary audit, not a KINGDOM
runtime report. HyoDo does not mutate KINGDOM state, launchd, thresholds, or
ledgers.

## Expected contract

An external producer that submits an admission observation should bind it to an
external mutable-state root and admission ledger, then provide the following
identities and freshness fields:

| Field | Expected meaning | HyoDo authority |
| --- | --- | --- |
| mutable-state root | producer-owned canonical state root | reference only |
| admission ledger path | producer-owned admission record source | reference only |
| cursor / salt / tracker | producer lineage and replay/freshness controls | validate when supplied |
| runtime identity | serving process/runtime identity | separate observation |
| execution identity | worker/execution identity | separate observation |
| snapshot_id | immutable state snapshot binding | reference only |
| run_id / execution_id / attempt_id | causal run and attempt identifiers | preserve as opaque IDs |
| source SHA | producer/source revision | provenance binding |
| freshness | measured-at and readback time | fail closed when unverifiable |

## Observed evidence

- HyoDo source `af028c62b075580830ad418614cb172af5e5e7a2` validates and records
  `hyodo.admission-observation/v1`.
- The local package tests and neutral-cwd CLI smoke exercise admission records
  with `execution_attempted=false` and `execution_observed=false`.
- HyoDo's product boundary explicitly assigns execution authority, worker
  lifecycle, orchestration, and settlement to KINGDOM/host policy.

## Missing evidence

No fresh authenticated KINGDOM producer readback was available in this HyoDo
candidate audit for the external mutable-state root, admission ledger path,
cursor, salt, tracker, runtime identity, execution identity, snapshot binding,
execution/attempt lineage, source SHA, or freshness. The HyoDo local ledger and
receipt therefore do not prove KINGDOM live state or execution success.

The integration status is `UNOBSERVED`. A KINGDOM runtime-d or historical
receipt, if supplied later, must remain historical evidence until it is matched
to the current runtime-e source, identities, snapshot, and fresh readback.
