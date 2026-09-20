# HyoDo product boundary

HyoDo is a local verification and evidence layer for AI-assisted work. It helps
people see which checks ran, what they found, and what remains unknown. It does
not become the authority that plans, executes, merges, deploys, or remembers
work on behalf of another system.

## HyoDo owns

- local quality gates and their fail-closed verification status;
- evidence, measurement, validation, ledger, and attestation surfaces;
- local policy evaluation and explicit `ALLOW` / `DENY` / `ASK` /
  `UNOBSERVED` results; and
- observation of execution evidence supplied by an integrating host.

## HyoDo does not own

- task planning, routing, dispatch, or worker lifecycle;
- orchestration, recovery, settlement, merge, or deployment authority;
- the integrating host's current runtime state;
- external memory, knowledge bases, or continuity systems; or
- facts that HyoDo did not observe.

An integrating host may choose to enforce a HyoDo result, but the act of
enforcement belongs to that host.

## Invariants

1. **Execution is not evidence.** Work happening does not prove the claimed
   checks ran.
2. **Evidence is not authority.** A receipt or policy result does not itself
   execute, merge, deploy, or approve anything.
3. **Missing evidence is not a pass.** Unreadable or absent evidence remains
   `UNOBSERVED`.
4. **Recorded history is not current runtime truth.** A memory, report, or
   previous receipt can inform review without proving what is true now.

## External integrations

Agent runtimes, CI systems, editors, and continuity stores may provide evidence
to HyoDo or consume evidence from it. Those integrations do not become HyoDo
state merely because HyoDo can observe or attest them.

`hyodo.orchestration-observation/v1` records an observation supplied by an
external executor. It does not execute the observed work, mutate the host, or
grant execution authority.

## Status vocabulary

Use **HyoDo status** only for HyoDo-owned source, package, gates, evidence,
dashboard, and HyoDo-owned runtime surfaces. Describe an external system's
state as that system's state. If ownership is not established, report it as
`UNATTRIBUTED` rather than assigning it to HyoDo.
