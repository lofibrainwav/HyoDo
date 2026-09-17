---
title: Product boundary
description: The verified ownership boundary across HyoDo, Kingdom, and BB.
---

# HyoDo, Kingdom, and BB product boundary

This is the canonical boundary contract for describing HyoDo, Kingdom, and BB
together. It prevents an external executor's state, or a continuity projection,
from being mistaken for HyoDo product state.

## HyoDo owns

- quality gates, policy decisions, and fail-closed exit contracts;
- evidence, measurement, validation, ledger, and attestation surfaces; and
- observation of externally supplied execution evidence.

HyoDo is a verification and evidence plane. It does not plan tasks, execute
workers, own worker lifecycle, orchestrate dependencies, recover work, or
settle execution.

## Kingdom owns

- task planning and dispatch;
- execution authority and worker lifecycle;
- orchestration, recovery, and settlement.

Kingdom is an execution plane. Its processes, tests, worktrees, branches, and
runtime state are not HyoDo state merely because HyoDo can observe or attest
them.

## BB owns

- human-owned durable memory, provenance, decisions, and lessons; and
- settled evidence that has been deliberately promoted for future reuse.

BB is a continuity plane. It does not own live runtime truth, host execution
authority, HyoDo's event ledger, or HyoDo product status. A BB projection is a
record or memory surface, not proof of current Kingdom or HyoDo state.

## Shared three-plane invariant

`KINGDOM = Agency · HyoDo = Trust · BB = Continuity`. The canonical loop is
`Human Intent → KINGDOM → HyoDo → BB → Skill/Eval/Memory → Better KINGDOM`.
Evidence is not authority, memory is not runtime state, and each plane's current
status must be read from its owning source/runtime.

## Non-equivalence rules

1. A Kingdom process or test is not evidence that HyoDo is open, closed,
   healthy, or unhealthy.
2. A HyoDo dashboard or evidence receipt is not execution authority and does
   not control Kingdom work.
3. `hyodo.orchestration-observation/v1` records a sidecar observation from an
   external executor; it does not mutate the agent event ledger or execute the
   observed work.
4. HyoDo closeout and Kingdom closeout are separate decisions. Report them as
   separate axes even when one system observes the other.

## Status vocabulary

Use **HyoDo status** for HyoDo source, package, gates, evidence, dashboard, and
HyoDo-owned runtime surfaces. Use **Kingdom status** for Kingdom branches,
worktrees, workers, orchestration, tests, and execution runtime. If ownership
is not established, report the item as `UNATTRIBUTED` rather than assigning it
to either product.
