# HyoDo and Kingdom product boundary

This is the canonical boundary contract for describing HyoDo and Kingdom
together. It prevents an external executor's state from being mistaken for
HyoDo product state.

## HyoDo owns

- quality gates, policy decisions, and fail-closed exit contracts;
- evidence, measurement, validation, ledger, and attestation surfaces; and
- observation of externally supplied execution evidence.

HyoDo is a verification and evidence plane. It does not plan tasks, execute
workers, own worker lifecycle, orchestrate dependencies, recover work, or
settle execution.

HyoDo policy decisions and gates apply within HyoDo's declared product scope.
They validate evidence and report HyoDo outcomes; they do not authorize a
user's action in an integrating host. The host owns action-specific
authorization under its own delegated policy. A host's virtue lens or a HyoDo
receipt may inform that policy only through an explicit, versioned contract;
neither silently grants or expands authority.

## Kingdom owns

- task planning and dispatch;
- execution authority and worker lifecycle;
- orchestration, recovery, and settlement.

Kingdom is an execution plane. Its processes, tests, worktrees, branches, and
runtime state are not HyoDo state merely because HyoDo can observe or attest
them.

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
