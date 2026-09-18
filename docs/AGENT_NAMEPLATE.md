# Agent Nameplate v1

`hyodo.agent-nameplate/v1` is a provenance-only receipt for one
harness-assigned agent activity. It answers who was observed in which role,
where and when the activity occurred, and which exact artifact it refers to.

It does not authenticate an actor and does not grant authority, approval, or
merge permission.

## Contract

The public schema is:

- [`agent-nameplate-v1.schema.json`](../schemas/agent-nameplate-v1.schema.json)
- [`agent-nameplate-v1.pin.json`](../schemas/agent-nameplate-v1.pin.json)

Required fields are:

```text
actor_id
role
host
provider
model
mode
session_id
github_actor
observed_at
repo
exact_artifact_sha
```

`role` is assigned by the harness and is one of `builder`, `verifier`,
`observer`, or `UNOBSERVED`. It is never inferred from a model response.

`actor_id` keeps the existing `hyodo.agent-event/v1` meaning: an opaque
harness label used for correlation. It is not an authentication identity.

Runtime fields are copied only from observed runtime values. Missing values
remain `UNOBSERVED`; HyoDo does not guess a model, host, provider, mode, or
session.

`github_actor` is recorded separately from the agent identity. A GitHub
credential identity is not a model or agent identity.

`exact_artifact_sha` is mandatory. Consumers should validate the nameplate with
the exact artifact SHA they are currently observing; a mismatch is not valid
provenance.

The contract deliberately has no `authority`, `approval`, or
`merge_permission` field. A nameplate can be evidence about provenance only.

## Compatibility boundaries

This contract does not modify:

- `hyodo.agent-event/v1`
- `hyodo.runtime-identity/v1`

An existing event `actor_id` can be compared with a nameplate `actor_id` for
correlation, while preserving the event schema's opaque-label semantics.
