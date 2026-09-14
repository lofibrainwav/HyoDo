# KINGDOM/AFO strangler migration contract

Status: **DESIGN CONTRACT — migration not complete**

This document defines how KINGDOM may retire AFO legacy capabilities around
HyoDo's public contract. It is not evidence that KINGDOM has completed the
migration, and it does not make HyoDo a runtime, memory, retrieval, or
credential owner.

## Ownership boundary

```text
HyoDo  = first public vertex: evidence, policy, trust, attestation contracts
KINGDOM = integrating system: orchestration, runtime, memory, retrieval,
          credentials, external mutation, and final authority
AFO    = KINGDOM legacy surface: isolated, frozen, and strangled capability
```

The adapter belongs to KINGDOM. HyoDo receives only redacted observations,
evidence metadata, provenance references, contract version, and correlation
identifiers. Credentials, raw wallet material, legacy process handles,
retrieval bodies, and authority fields must not cross the boundary.

## Strangler stages

| Stage | Action | Required receipt | Exit condition |
| --- | --- | --- | --- |
| Freeze | Stop new AFO capability and credential use | KINGDOM legacy inventory | No new AFO dependency |
| Boundary | Put `LegacyBoundaryAdapter` in front of each AFO capability | Adapter contract and deny-list test | Calls are observable and redacted |
| Shadow | Run AFO and HyoDo observation paths in parallel | Same-input comparison receipt | Differences explained or held |
| Route | Send one capability at a time through HyoDo | Route decision and rollback trigger | Selected capability has stable readback |
| Cutover | Make the HyoDo contract path authoritative in KINGDOM | Source/runtime/readback receipt | AFO is no longer selected |
| Retire | Revoke credentials and remove AFO invocation | Invocation-zero and credential receipt | No consumer, process, or artifact depends on AFO |

## Orchestration

Independent lanes may run in parallel: legacy inventory, credential validity,
HyoDo contract tests, shadow comparison, and history/artifact scans. Shared
mutable runtimes and credential stores stay out of parallel execution.

Serial gates are:

```text
candidate SHA freeze
  -> legacy inventory
  -> credential revoke/rotate
  -> adapter boundary verification
  -> shadow mismatch resolution
  -> capability cutover
  -> AFO invocation-zero readback
  -> artifact/history verification
  -> bounded final audit
```

No gate may promote a missing receipt, stale SHA, healthy process without
consumer readback, or HyoDo receipt as KINGDOM authority.

## Invariants

- HyoDo never imports AFO runtime, wallet, or KINGDOM-only modules.
- KINGDOM owns the adapter, routing, rollback, and final decision.
- AFO credentials are never copied into HyoDo or public artifacts.
- Shadow results are comparison evidence, not authority.
- A changed source SHA invalidates downstream receipts.
- History rewrite is a separate repository-owner decision; credential revoke or
  rotation comes first when validity is uncertain.

## Legacy secret handling

Historical `afo_core` and related script findings belong to the KINGDOM legacy
cleanup lane:

```text
legacy finding
  -> redacted metadata
  -> revoke/rotate if validity is uncertain
  -> private receipt
  -> HyoDo register disposition
  -> fresh history and artifact scans
```

The public HyoDo repository must retain no populated environment file, wallet
value, credential, or unredacted scanner output. A historical finding may be
removed from public history only after explicit repository-owner approval and
a coordinated ref/tag/release impact review.

## Completion

Migration is complete only when KINGDOM can show, for each capability, the
HyoDo contract version and source SHA, adapter and route decision, shadow
receipt, rollback trigger, consumer readback, AFO invocation-zero evidence,
and credential/artifact/history receipts.

Until then the honest state is `MIGRATION IN PROGRESS`, `HOLD`, or
`UNOBSERVED`, never `RETIRED` or `GREEN`.
