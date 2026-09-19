# HyoDo unified doctrine: minimal reconciliation runbook

Status: reviewable replacement; not an adopted SSOT or execution authorization.
The previously reviewed file was absent from this checkout. This replacement
uses the supplied AV-01–AV-10 report; it does not claim to preserve unseen text.

## Start here

**OBSERVE → RECONCILE → SMALLEST SAFE FIX → READBACK**

1. **Observe:** identify the requested target, its owner and current evidence.
   Inspect local changes before touching files. Record missing observations.
2. **Reconcile:** name the discrepancy and the smallest acceptance condition.
   Resolve action authority using the rule below. Select only relevant checks.
3. **Smallest safe fix:** change the owned target within authorized scope.
   Run checks proportional to the affected behavior; failed checks stay failed.
4. **Readback:** inspect the resulting diff and the exact changed target.
   Report what changed, checks actually run, remaining blockers and ownership.

A stale version sentence needs the authoritative version, a scoped text fix,
link/diff checks, and readback of the edited document. If the request includes
the served website, source readback alone cannot close that request: separately
authorize publication and read back the served target. No unrelated issue,
research, branch cleanup or specialist campaign is required.

Keep these facts in the existing task/PR record. Do not create a new packet,
database, dashboard or mandatory receipt for each step.

## Preserved doctrine and ownership

The [product boundary](../docs/PRODUCT_BOUNDARY.md) and
[repository instructions](../AGENTS.md) remain authoritative. This runbook
describes a host's workflow; it adds no HyoDo orchestration capability.

- Evidence ≠ Authority. Derivation ≠ Valuation. HyoDo ≠ Execution.
- Source ≠ Package ≠ Served Runtime. Merged ≠ Served. UNOBSERVED ≠ GREEN.
- Truth / 眞, Goodness / 善, Beauty / 美, Benevolence / 仁, Hyo / 孝,
  and Eternity / 永 are six independent lenses, not an authorization score.
- KINGDOM = Agency, HyoDo = Trust, BB = Continuity describes that integration.
  Other hosts retain their own authority and continuity; neither KINGDOM nor
  BB is a prerequisite for using HyoDo.

**PRODUCT RELEASE CLOSURE ≠ RESEARCH VALIDATION.**
This runbook closes product/public-truth work. Research runs under a separate
research lifecycle. Research incompleteness does not reopen a shipped product
release. Product release does not validate a research hypothesis. A separately
observed product defect may open a new product task with its own evidence.

## Reuse inventory before adding a primitive

This inventory is of checkout source and consumers, not deployed behavior.

| Existing primitive | Inspected consumer / verification | Reuse and limit |
| --- | --- | --- |
| [Admission observation](../hyodo/admission_observation.py) | [CLI](../hyodo/cli/main.py), [tests](../tests/test_admission_observation.py) | Records an external admission decision; explicitly rejects execution claims. It cannot supply host authority. |
| [Orchestration observation](../hyodo/orchestration_observation.py) | CLI ingestion and `join_adapter_events`, [tests](../tests/test_orchestration_observation.py) | Sidecar evidence for external dependencies; does not mutate the event ledger or dispatch work. |
| [Evidence plate](../hyodo/evidence_plate.py) | [Six-lens runtime](../hyodo/six_lens_runtime.py), [tests](../tests/test_evidence_plate.py) | Bounded evidence with artifact identity and residuals; authority remains UNOBSERVED. |
| [Independent verifier attestation](../hyodo/independent_verifier.py) | [Exact-candidate tests](../tests/test_independent_verifier.py); no production caller established by this inventory | Read-only candidate evidence; rejects authority/builder verdict inputs; process/credential isolation remains unproven. |
| [Release chain receipt](../scripts/release/verify_release_chain.py) | [Receipt regression tests](../tests/test_release_chain_receipt.py) | Existing per-step observed/unobserved release evidence; not permission to release. |
| [Release pipeline](../scripts/release/pipeline.py) | [Pipeline tests](../tests/test_release_pipeline.py) | Explicit caller-supplied authorization reference plus exact-head binding. This is not a general delegation resolver; owner, expiry and revocation verification remain with the calling host. |

These primitives plus the existing task record suffice for this reconciliation.
No new decision-bearing object or attestation format is introduced. Before any
future extension, identify the exact consuming call site, missing information,
owner, compatibility requirements and why an existing reference cannot suffice.
Only then consider a bounded observation/receipt extension. An attestation's
integrity or signature does not grant execution authority.

## Independent state dictionary (AV-01, AV-08, AV-09)

These are reporting namespaces, not a migration of existing product schemas.
Never flatten them into a shared `status`, order them as a progression, or
implicitly cast between them. Existing primitive values retain their original
meaning; an adapter must explicitly document any mapping and preserve unknowns.

| Namespace / field | Values | Question answered |
| --- | --- | --- |
| EvidenceCoverage / `evidence_coverage` | OBSERVED, PARTIAL, UNOBSERVED, CONFLICTING | How much of this bounded claim is supported? |
| ClaimOrigin / `claim_origin` | OBSERVED, DERIVED | Was this claim directly observed or inferred? |
| ResolutionState / `resolution_state` | RESOLVED, UNRESOLVED | Has this discrepancy been settled? |
| DecisionNeed / `decision_need` | NONE, HUMAN_REQUIRED | Is a human decision still needed? NONE grants nothing. |
| LaneState / `lane_state` | READY, RUNNING, HOLD, BLOCKED, VERIFIED | What is this lane doing? VERIFIED applies only to its named check. |
| PublicSurfaceState / `public_surface_state` | LIVE, INTENTIONALLY_UNAVAILABLE, ABSENT | What was independently established about the public target? |
| Disposition / `disposition` | BLOCKED, WITHIN_AUTHORITY, AUTHORIZED_EXCEPTION | What may the host do about this specific action? |

OBSERVED coverage requires evidence for the whole named claim; partial evidence
is PARTIAL. Incompatible observations are CONFLICTING, without an invented
cause. UNOBSERVED means no adequate observation, not proof of absence.
Use `null` for an unestablished public-surface state or claim origin. ABSENT
requires an actual absence check; intentional unavailability requires an owner
record. LIVE requires fresh, direct readback of the identified served target,
independent of whether another claim is DERIVED. Record target, time, immutable
identity where available, method and evidence reference in the existing record.
Freshness is defined by the target's acceptance condition; an old URL is not
fresh readback. Unknown external vocabulary remains raw/unmapped, not VERIFIED.

UNRESOLVED or HOLD does not permit execution. For an affected action, default
to BLOCKED. An explicit host-authorized risk exception may change disposition
to AUTHORIZED_EXCEPTION with an authority reference, accepted risk, owner,
scope, target and expiry. It never rewrites evidence or resolution. An unrelated
blocked lane does not block an independently scoped, authorized action.

The [test-only schema](../tests/fixtures/runbook/state.schema.json) and
[positive/negative fixtures](../tests/fixtures/runbook/state-cases.json) check
vocabulary, axis separation and reference requirements. They are offline review
examples, not a public format, authority verifier or runtime truth surface.
Schema acceptance proves neither authenticity nor freshness of a reference.
The negative-boundary tests deliberately accept fixture references marked
expired, revoked or wrong-owner as structurally valid: this demonstrates why
the schema must never be used as an authority gate.

## Authority resolution and distinct records (AV-06, AV-10)

Before the specific mutation, the host checks existing explicit authorization
or delegation: issuer/owner, permitted action and scope, exact target, validity
period/expiry, revocation and any conditions. A valid grant is reused without
duplicate human approval. Unclear, expired, revoked or out-of-scope delegation
does not grant authority: ask only for the missing action authorization, while
continuing independent authorized inspection. A non-expiring grant must say so;
missing expiry semantics are not silently treated as unlimited.

An explicit human decision requirement cannot be bypassed using a general
delegation. Once the required decision is supplied, record its reference and
resolve that need before execution. Recheck authority if target, scope or time
changes. Non-overridable host prohibitions cannot be waived by this document.
Push, deployment, destructive Git and credential changes require the applicable
explicit authorization; approving this runbook does not authorize them.

| Record | Owner | Proves only |
| --- | --- | --- |
| ContractAdoption | Repository/contract owner | Acceptance of the named document revision |
| EvidenceVerification | Named verifier | The named evidence relationship was checked |
| AuthorityResolution | Host authority owner | Permission for the bounded action |
| ExecutionReceipt | Executor | The action's actual attempted result |
| ReleaseReadback | Target observer | What the identified target actually serves |

Reference existing records; these labels do not require five new artifacts.
None automatically creates another. Failed or absent execution/readback cannot
be repaired by document adoption, a high score or a passing local check.

## Conditional lanes and optional campaigns (AV-03, AV-04)

| Lane | Activate only when | Otherwise |
| --- | --- | --- |
| Issue reconciliation | Request names an `issue_id` or an observed defect requires tracking | Inactive; no hard-coded issue number |
| Privacy | Changed data collection, disclosure or access affects privacy | Inactive |
| Accessibility | Changed user interaction/content affects accessibility | Inactive |
| Contact | Changed contact information or contact handling | Inactive |
| Cultural provenance | Changed cultural claims/assets need provenance review | Inactive |
| Maintenance inventory | Explicit maintenance scope or branch ownership blocks this fix | Inspect only; unknown ownership never permits cleanup |
| External reproduction | Changed public exposure needs external proof, or explicitly requested | Inactive |
| UX | Changed user-facing behavior needs usability checks | Inactive |

Record the concrete trigger for an activated lane. Ambiguous applicability
requires a bounded inspection, not automatic fan-out. Branch cleanup is a
separate authorized operation. Other seats' dirty work forbids shared mutation;
use an owned isolated checkout if needed and preserve their work.

For an explicitly selected large release campaign, a host may expand the same
four phases into the legacy 13-node topology:
`G0 → G1 → (L1, L2, L3, L4) → G2 → L5 → L6 → G3 → L7 → G4 → G5`.
G0 observes; G1 fixes scope/contract references; L1 is optional issue work;
L2 is scoped reconciliation; L3 selects individual specialists; L4 is maintenance
inventory only. G2 gathers findings without clearing blockers. L5 applies the
authorized fix; L6 verifies it (serial after L5 when dependent). G3 checks scoped
acceptance; L7 performs external reproduction when selected. G4 resolves
authority for any remaining publication, never retroactively for L5. G5 reads
back the exact target. All earlier mutations also require authority resolution.
Independent read-only lanes may run concurrently. Shared mutations and joins
are serialized. Campaign selection alone does not activate every lane;
checks required by the affected scope or host policy cannot be skipped.

## Public state projection: default DO NOT BUILD (AV-05)

There is no identified new public-state consumer in this task. Do not create
`hyodo.public-state/v1`, a generated state file or a new publishing job here.
A future proposal must satisfy **all** of these conditions before construction:

1. A real consumer is named by exact call site and owned requirement.
2. Every value is generated from identified canonical sources.
3. Human editing is prohibited by the generation workflow.
4. It is explicitly a projection and never supersedes those sources.
5. Source identity, generation time and a consumer-enforced freshness rule
   make stale/missing/conflicting inputs detectable and unusable as fresh truth.

Failure of any condition means DO NOT BUILD. A schema, hypothetical dashboard
or desire for a consolidated status is not a consumer.

## Completion and adversarial acceptance (AV-07, AV-08)

Close only the named scope after proportional checks pass and target readback
meets its acceptance condition. Skipped checks and zero-gate runs are not
success. Required HOLD/BLOCKED lanes or UNRESOLVED findings prevent ordinary
completion. Preserving them in a join does not clear them. An authorized
exception may permit a bounded action, but report the exception and residual
as such; do not declare unconditional COMPLETE or SSOT_GREEN. De-scoping work
requires explicit scope ownership, not a verifier silently dropping a failure.

The following cases are review expectations, not claims of live host execution.
Offline schema tests cover representational invariants; delegated execution,
lane selection and live readback require the integrating host's own evidence.

| Adversarial input | Required result |
| --- | --- |
| Only some evidence observed | PARTIAL; no generated execution authority |
| Two observations conflict | CONFLICTING; retain both references; do not guess cause |
| A derived claim exists | DERIVED; no automatic VERIFIED, LIVE or authorization |
| A human decision is needed | HUMAN_REQUIRED and BLOCKED; no authority fabricated |
| Valid delegated authority exists | Verify owner/scope/target/expiry/revocation; reuse without asking again |
| No public-state consumer | DO NOT BUILD |
| No issue identifier or relevant issue trigger | Issue lane inactive |
| No relevant privacy concern | Privacy lane inactive; unrelated specialists stay inactive |
| Stale branch owner unknown | Inventory only; no delete/reset/rebase |
| Research pilot incomplete | Product closure unchanged; research remains separately incomplete |
| Required external reproduction unavailable | EvidenceCoverage=UNOBSERVED, LaneState=HOLD, Disposition=BLOCKED; no success claim |
| Another seat has dirty changes | No shared mutation; preserve work and isolate this fix |

Adoption is a separate owner decision after AV-01–AV-10 reconciliation review,
offline tests and exact consumer/owner/authority readback for the intended host.
Local test success alone cannot promote this document to SSOT or prove a
shipped product, functioning host integration or validated research hypothesis.

## Reproducing this review

Run the bounded checks from the checkout:

```bash
python -m pytest tests/test_runbook_state_contract.py tests/test_admission_observation.py tests/test_orchestration_observation.py tests/test_orchestration_observation_ingest.py tests/test_evidence_plate.py tests/test_independent_verifier.py tests/test_release_chain_receipt.py tests/test_release_pipeline.py tests/test_release_plan.py -q --tb=short
```

For changes to the reused package primitives, also run
`bash scripts/verify-public.sh` in an owned isolated checkout: it installs
dependencies and creates build/smoke artifacts, so it is not a zero-write check.
The [adversarial review receipt](./hyodo-unified-doctrine-adversarial-review.md)
separates actual observations from host-level expectations.
