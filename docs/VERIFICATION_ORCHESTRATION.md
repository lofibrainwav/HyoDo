# HyoDo Verification Orchestration

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

## Lane register

| Lane | Current state | Evidence required to advance | Next edge |
| --- | --- | --- | --- |
| Historical secrets | `HOLD` | owner disposition for all findings, then fresh gitleaks receipt | security required gate |
| Security governance | `OBSERVED` | Security verification required context readback | merge enforcement |
| Container | `OBSERVED` | Previous candidate `293456cf…` verified by CI run `34862789517`; latest head requires a fresh receipt | artifact/release gate |
| Production provenance | `HOLD` | live deployment SHA equals canonical main SHA | production closeout |
| Public release | `HOLD` | signed tag, GitHub assets, PyPI version and provenance all bind to main | release closeout |
| KINGDOM boundary | `UNOBSERVED` | host-side integration evidence or explicit non-claim receipt | integration closeout |

The container lane is `OBSERVED` only after the `Container proof` workflow
completes successfully. A workflow definition or queued run is not a proof
receipt.

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

The previous candidate `293456cf0141cc77f3201714784d98f151e073fa` had a
verified container receipt from workflow run `34862789517`. Its workflow SHA
was recorded separately because pull-request runs execute on a synthetic merge
ref. The artifact was
`hyodo-container-proof-293456cf0141cc77f3201714784d98f151e073fa`.

The current candidate must receive a new receipt after any subsequent commit.

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
