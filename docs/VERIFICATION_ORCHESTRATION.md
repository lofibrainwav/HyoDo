# HyoDo Verification Orchestration

> **DERIVED OPERATIONS MAP — NOT PRODUCT SSOT**
>
> This file is an operator-generated map. Source truth remains in the cited
> repository files, GitHub run records, artifact metadata, branch-protection
> readbacks, release records, and live endpoint readbacks. Do not treat a map
> row as evidence unless its full source identifier is cited.

## Ownership boundary: HyoDo and KINGDOM

HyoDo and KINGDOM are not interchangeable nodes in this map.

- **HyoDo is the mind:** a public, host-neutral layer for truth, evidence,
  policy, trust signals, and attestation contracts. It can describe an
  observation and its receipt, but it does not own execution authority.
- **KINGDOM is the system:** the integrating host owns orchestration, memory,
  retrieval, runtime, credentials, external mutations, and final authority.

HyoDo must never claim that a score, receipt, or observation caused a KINGDOM
action. KINGDOM evidence must come from the host's own authoritative readback.
If that readback is absent, the HyoDo-side statement is `UNOBSERVED`, not a
KINGDOM success. This boundary is a product contract, not merely a lane label.

This document is the saved map for moving HyoDo from partial evidence to
closeout. It keeps independent observations parallel and only opens a
dependent edge after its predecessor has a durable receipt.

## State vocabulary

- `UNOBSERVED`: no current evidence was collected.
- `OBSERVED`: a current receipt exists, but the acceptance condition is not
  necessarily satisfied.
- `VERIFIED`: the receipt satisfies the lane's acceptance condition.
- `CLOSED`: the verified condition is reflected in the authoritative external
  surface.
- `HOLD`: evidence exists but an owner or external action is required.
- `BLOCKED`: the required capability or authority is unavailable.

`UNOBSERVED` must never be promoted by documentation alone. Every promotion
must cite a current receipt bound to the relevant commit, artifact, workflow
run, or live endpoint.

## Execution map

```text
                         ┌─ secrets ───────────────┐
                         │                          │
                         ├─ governance ────────────┤
canonical candidate ─────┼─ container proof ────────┼─ integration gate
                         │                          │
                         ├─ production provenance ─┤
                         ├─ public release chain ──┘
                         └─ KINGDOM boundary audit

integration gate
      │
      ├─ main merge / required contexts
      ├─ production deployment convergence
      └─ release + PyPI provenance convergence
```

The six discovery lanes are independent and should run in parallel. The
integration gate is serial: it must not run until the lane receipts identify a
single candidate SHA and no unresolved blocker is being hidden as `GREEN`.

## Lane register (procedure, not live state)

Live state is intentionally not stored in this document. Read the authoritative
source at checkpoint time and record the full IDs in the checkpoint report.

| Lane | Authoritative source | Promotion rule | Next edge |
| --- | --- | --- | --- |
| Historical secrets | gitleaks receipt + `docs/security/GITLEAKS_DISPOSITION.md` | every finding has an owner disposition and fresh scan | security required gate |
| Security governance | GitHub branch-protection API | Security verification appears in required contexts | merge enforcement |
| Container | Container proof workflow + named artifact | run head, artifact head, receipt candidate SHA, and image/SBOM evidence all match | artifact/release gate |
| Site evidence graph | HyoDo Site Build run | current candidate run completes successfully with no failed verification step | site gate |
| Production provenance | Vercel deployment readback + live endpoint | for web-impacting changes, live deployment SHA equals canonical main SHA; for non-web changes, an explicit ignored-build receipt and unchanged-surface readback exist | production closeout |
| Public release | Git tag, GitHub Release, PyPI API, provenance receipts | signed tag, assets, and public package all bind to canonical main | release closeout |
| KINGDOM boundary | explicit host-side integration receipt | observed readback or explicit non-claim receipt exists | integration closeout |

The container lane is `OBSERVED` only after the `Container proof` workflow
completes successfully. A workflow definition or queued run is not a proof
receipt.

## Production impact routing

Classify the candidate diff before interpreting a Vercel result:

```text
site/** changed
  -> web-impacting
  -> Vercel deployment is required
  -> deployment SHA and live endpoint must be read back

site/** unchanged
  -> non-web
  -> ignored-build receipt is acceptable only when the project rule is observed
  -> unchanged production surface must still be read back
```

`Canceled by Ignored Build Step` is not automatically a successful non-web
receipt. If `site/**` changed, or if the project ignore rule was not measured,
the state remains `UNKNOWN` or `HOLD` and production convergence is not proven.

## Parallel dry-run contract

Run these read-only lanes against one exact candidate SHA. Do not echo secret
values; report rule, path, commit, line, and disposition only.

```bash
gitleaks detect --source . --redact --report-format json --report-path "$RECEIPT"
gh api repos/OWNER/REPO/branches/main/protection
gh pr view PR --json headRefOid,statusCheckRollup
docker build --pull --tag "hyodo:proof-$SHA" .
curl -sSI https://hyodo.app/
gh release view TAG --json tagName,targetCommitish,assets
```

The Docker command belongs to a Docker-capable CI runner. If the capability is
missing, record `BLOCKED`, not a successful empty result.

## Serial promotion contract

1. Freeze the candidate SHA and collect all six lane results.
2. Resolve or explicitly hold every secret finding.
3. Require the successful Security verification context in branch protection.
4. Require the container receipt and verify its commit binding.
5. Converge production to the canonical main SHA and read back the live SHA.
6. Create the release only after main, production, and public artifacts agree.
7. Perform one bounded final audit and park the result until a change trigger.

No step may promote a missing receipt, a queued workflow, or a prior release's
evidence.

## Assembly method: raw evidence to verified graph

Use this order when the surface is unfamiliar or the existing map is stale:

1. **Research first.** Freeze the candidate SHA and collect raw, redacted
   readbacks before proposing a fix. Preserve command output, timestamps, run
   IDs, artifact names, and endpoint status without copying secret values.
2. **Fan out independent lanes.** Dispatch one lane per independent domain.
   Each lane has an explicit write-set, deny-set, owner, and expected receipt.
   Shared files, shared mutable services, and dependent conclusions stay out of
   parallel execution.
3. **Report six facts.** For every observation record who owns it, what was
   observed, when it was observed, where the evidence lives, why it matters,
   and how it was measured. Classify the statement as `fact`, `inference`, or
   `unknown`.
4. **Draw edges.** Connect an observation to its next action only when the
   receipt supplies the required input. Mark missing edges as `UNOBSERVED`,
   not as a successful no-op. Name the single bottleneck that prevents the
   next edge.
5. **Promote serially.** After all independent lanes return, review conflicts,
   verify candidate-SHA binding, and promote only the first three ready gates.
   Pause for a checkpoint before external mutation or the next batch.
6. **Close the loop.** Re-read the authoritative surface after every mutation.
   If the SHA, workflow run, artifact, deployment, release, or owner decision
   changes, invalidate downstream receipts and reopen their edges.

This is the Lego rule: parallel lanes find the pieces, the graph shows which
pieces connect, and serial gates decide which assembled section is safe to
carry forward.

## Drift and silent-failure invariants

The following invariants are mandatory for every update:

- Every receipt names the candidate SHA; PR synthetic merge SHA is recorded as
  a separate workflow identity.
- Every artifact is checked against its workflow run and candidate SHA before
  being cited.
- A successful workflow with an unresolved register, missing owner, or absent
  required context remains `HOLD`.
- A queued, cancelled, stale, or capability-blocked run is never `GREEN`.
- External mutation requires an explicit owner, rollback trigger, and
  post-mutation readback.
- A final audit is bounded and then parked; it reopens on a declared change
  trigger rather than silently drifting.

## Checkpoint report format

At each checkpoint, report left-to-right in time order:

```text
head -> parallel observations -> receipts -> conflicts -> next serial gate
owner / what / when / where / why / how
state: UNOBSERVED | OBSERVED | VERIFIED | CLOSED | HOLD | BLOCKED
```

## Receipt anchors

Live receipt anchors are not stored in this procedure document. At every
checkpoint, read the workflow run and artifact APIs again. A receipt from a
different candidate SHA is historical evidence and cannot promote the current
candidate.

For PR workflows, record both the candidate head SHA and the synthetic workflow
SHA. Never replace either with an abbreviated identifier.

## Assistant self-audit

Before reporting any status, compare these values from raw sources:

```text
candidate HEAD == PR head == workflow head == artifact workflow_run.head_sha
```

If the equality cannot be proven, report `UNKNOWN` or `HOLD`. Never infer
`latest`, `current`, `GREEN`, or `VERIFIED` from a previous checkpoint or from
this document itself.

## Update procedure

For every refresh, append or update the lane row with:

```text
observed_at / candidate_sha / workflow_or_command / receipt_ref /
state / blocker / next_edge
```

Reopen the audit only when the candidate SHA, workflow conclusion, branch
protection, live deployment, public artifact, secret disposition, or KINGDOM
boundary changes. Otherwise preserve the last bounded audit and report it as
parked.
