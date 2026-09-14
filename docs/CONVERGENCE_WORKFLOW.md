# Evidence-first convergence workflow

This runbook describes how to move a multi-branch HyoDo change from a first
observation to a mergeable result without mixing evidence, losing work, or
drifting from the source of truth.

It is for maintainers coordinating several seats, agents, or Dependabot pull
requests. It does not grant merge authority. The maintainer remains the final
decision-maker.

## The operating rule

The coordinator stays in the middle:

```text
                         +----------------------+
                         |  SSOT / main HEAD    |
                         |  current gate policy  |
                         +----------+-----------+
                                    |
                 establish baseline, head, and write-sets
                                    |
       +----------------------------+----------------------------+
       |                            |                            |
       v                            v                            v
  Research lane                 Dry-run lane                Verification lane
  read-only facts               merge-tree / local tests     exact-head CI
       |                            |                            |
       +----------------------------+----------------------------+
                                    v
                         +----------------------+
                         | Coordinator decision |
                         | PASS / HOLD / BLOCK  |
                         +----------+-----------+
                                    |
                          one bounded integration
                                    |
                                    v
                         main HEAD + fresh readback
```

The coordinator never treats a score, a healthy-looking process, or a stale
green check as merge authority. Every claim is tied to a target, an exact
commit, an observation time, and a reproducible artifact or check URL.

## State vocabulary

| State | Meaning | Allowed promotion |
| --- | --- | --- |
| `UNOBSERVED` | No valid observation exists, or the target cannot be measured | Only after a fresh, target-bound observation |
| `UNKNOWN` | Evidence is incomplete or the source/head relationship is unclear | Resolve provenance or collect fresh evidence |
| `HOLD` | Work is valid but waiting for CI, owner review, or a base update | Continue only after the named condition changes |
| `BLOCK` | A concrete failure or policy violation prevents progress | Fix the cause and rerun the affected proof |
| `PASS` | Required evidence for the stated scope is fresh and successful | May enter the integration gate |

`UNOBSERVED` is never silently converted to `PASS`. “100%” means 100% of the
declared required observations are fresh and successful; it does not mean a
score was rounded up or that unmeasured runtime behavior was assumed healthy.

## Step 1: Establish the baseline

Before delegating or editing, record:

```text
baseline main SHA:
candidate head SHA:
working-tree status:
scope and product boundary:
required checks:
```

Use a clean temporary worktree for each write lane. The user worktree is
read-only unless the user explicitly places it in scope. Preserve existing
untracked files and unrelated hunks.

For every lane, declare:

- `write-set`: files the lane may change;
- `deny-set`: files and external actions it must not change;
- `readback`: the exact command or URL that proves its result.

If two lanes share a write-set, they may research in parallel but must not
merge in parallel.

## Step 2: Parallel research and dry-run

Parallel lanes should answer different questions. Do not ask two agents to
make the same unresolved change.

Recommended lanes:

| Lane | Responsibility | Mutation |
| --- | --- | --- |
| Research | PR purpose, changed files, CI and compatibility risk | None |
| Collision | file overlap, base drift, merge-tree result | Temporary refs only |
| Verification | focused tests and exact-head check status | Temporary worktree only |
| Coordinator | normalize findings and choose the next gate | No lane-owned edits |

The dry-run must happen before integration:

1. fetch the candidate head into an isolated ref;
2. compare it with the current SSOT/main SHA;
3. run a merge-tree conflict check;
4. run the smallest relevant local verification;
5. inspect exact-head CI, not a similarly named or older run;
6. record `PASS`, `HOLD`, `BLOCK`, or `UNKNOWN` with evidence.

Dry-run success proves that a candidate can be considered. It does not prove
that multiple candidates can be merged together, and it does not replace
post-merge CI.

## Step 3: Integrate by dependency and write-set

Use parallelism only across disjoint write-sets. Within one write-set, use:

```text
merge one candidate
  -> fetch the new main
  -> rebase the next candidate
  -> rerun exact-head checks
  -> inspect the readback
  -> continue or stop
```

A base-branch update invalidates the previous mergeability and CI evidence for
the affected candidate. Rebase or update the branch; do not reuse the old
green result.

When a merge is rejected because the base changed, stop that lane, reread the
new base, and retry only after revalidation. Do not force a merge around the
new base.

## Step 4: Promote observations honestly

An observation may be promoted only when all of these match:

- the target is the intended checkout, PR, site, runtime, or host;
- the source/head SHA is recorded and current;
- the command or check actually ran, rather than being skipped;
- the result is successful for the declared scope;
- the evidence is readable and traceable;
- no stronger gate remains pending or failed.

Retrieval or agent receipts may help correlate work, but they are not gate
authority. Keep them separate from the gate's `evidence_refs`.

## Step 5: Bounded final audit and PARK

After the requested scope is complete, perform one final bounded audit:

- confirm the final `main` SHA;
- confirm required CI and post-merge checks;
- confirm no unexpected working-tree changes;
- confirm no write-set collision remains;
- confirm documentation and public product boundaries;
- report residual `HOLD`, `UNKNOWN`, or `UNOBSERVED` states.

If no required work remains, mark the lane `PARKED`. Reopen it only for an
explicit change trigger: a new commit, failed check, changed policy, changed
runtime, or new consumer evidence.

## Failure handling

- **Pending:** keep `HOLD`; inspect whether the job is progressing before
  rerunning it.
- **Failed:** capture the failing step and minimal log evidence; fix only the
  owning lane.
- **Behind/unknown:** update from the current SSOT and rerun checks.
- **Conflict:** do not overlay another lane's hunks; resolve in the owner
  lane's isolated worktree.
- **Local environment mismatch:** report it separately from CI; do not claim a
  local pass when the required tool or package was missing.

## Completion contract

The workflow is complete only when:

```text
declared scope = observed scope
fresh exact-head evidence = present
required checks = all PASS
unresolved blockers = none
post-merge readback = PASS
```

This is an evidence completeness contract, not an authority transfer. Scores
remain review signals; the maintainer and repository policy decide whether to
merge or release.
