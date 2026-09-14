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
| Container | `VERIFIED` | CI run `34862789517`; receipt binds candidate `293456cf…`, image user `hyodo`, image ID, and SBOM SHA | artifact/release gate |
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

## Latest receipt anchors

The current candidate `293456cf0141cc77f3201714784d98f151e073fa` has a verified
container receipt from workflow run `34862789517`. Its workflow SHA is recorded
separately because pull-request runs execute on a synthetic merge ref. The
artifact is `hyodo-container-proof-293456cf0141cc77f3201714784d98f151e073fa`.

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
