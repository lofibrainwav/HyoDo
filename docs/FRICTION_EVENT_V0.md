# FrictionEvent v0 and orchestration observation

Status: **experimental contract included in the HyoDo 4.18.0 candidate**.
It is measured evidence, not a calibrated score and not execution authority.

This layer observes execution. It does not schedule agents, grant authority,
change policy decisions, or define a calibrated friction score.

## Boundary

HyoDo remains a gate and evidence spine, not an agent runtime.

An external orchestrator such as KINGDOM may execute a serial/parallel DAG.
HyoDo receives a local sidecar record with schema
`hyodo.orchestration-observation/v1`. The existing
`hyodo.agent-event/v1` ledger is unchanged.

The sidecar records only the minimum topology and raw counters needed for
measurement:

- event/node identity and run identity
- serial or parallel execution
- dependency event ids and optional `all` / `any` join policy
- node state and attempt number
- approval wait duration
- explicit human-intervention, clarification, context-loss, duplicate-work,
  unobserved-claim, policy-conflict, rework, and verification-failure counts
- evidence references

It does not add prompt text, response text, model strings, tool arguments,
paths, or execution credentials.

Invalid sidecar observations are returned as explicit adapter issues. They are
never silently treated as an empty or successfully observed dependency set.

## Graph v2 adapter

`join_adapter_events()` returns copies of observed ledger events and adds a
transient `parent_event_ids` adapter field from the sidecar dependencies. The
ledger rows are not mutated or rewritten.

The Graph v2 SCC oracle introduced by the parent PR can therefore inspect a
multi-parent join such as:

```text
A --\
     J
B --/
```

without promoting Graph v2 into an execution scheduler.

## Generic FrictionEvent v0

`derive_friction_events()` deterministically maps explicit sidecar observations
to `hyodo.friction-event/v0` records.

Current event types are:

- `human_intervention`
- `agent_retry`
- `clarification_needed`
- `context_loss`
- `approval_wait`
- `blocked_action`
- `rollback`
- `duplicate_work`
- `unobserved_claim`
- `policy_conflict`
- `rework`
- `verification_failure`

Each event retains a raw magnitude (`count` or `duration_ms`), source event,
evidence references, and deterministic derivation rule.

## No judgement in v0

Every derived event is initially:

```json
{"friction": {"type": "agent_retry", "class": "unknown"}}
```

The allowed future classes are `avoidable`, `protective`, `chosen_growth`,
`structural`, and `unknown`, but v0 does not guess among them. Protective safety
friction and user-chosen growth must not be silently penalized as waste.

A future classification or calibrated score needs separate provenance and
before/after evidence.

## Authority

A FrictionEvent is measurement evidence only. Every v0 record states that it:

- does not grant execution,
- does not override policy,
- does not override an evidence gate.

This keeps ACL research authority, HyoDo policy authority, and friction
measurement separate.
